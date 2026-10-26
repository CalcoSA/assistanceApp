from app.domain.dtos.AttendanceDto import (PublicEventResponseDto, AttendancePersonResponseDto, AttendanceRegisterDto, AttendanceRegisterResponseDto,)
from app.application.interfaces.IAttendanceApplication import IPublicAttendanceApplication
from app.domain.interfaces.IAttendancePersonRepository import IAttendancePersonRepository
from app.domain.interfaces.IPersonnelTypeRepository import IPersonnelTypeRepository
from app.domain.interfaces.IAttendanceRepository import IAttendanceRepository, AttendancePersistenceError
from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.entities.Event import Event
from app.infrastructure.db.config import APP_TIMEZONE_INFO
from app.infrastructure.storage.GcsStorage import GcsStorage
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
import base64
import logging
import re
import uuid

logger = logging.getLogger(__name__)

class PublicAttendanceApplication(IPublicAttendanceApplication):

    STATUS_ACTIVE_NAME = "activo"
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    ATTENDANCE_GRACE_PERIOD = timedelta(minutes=30)

    def __init__(self, eventRepository: IEventRepository, attendancePersonRepository: IAttendancePersonRepository, attendanceRepository: IAttendanceRepository, personnelTypeRepository: IPersonnelTypeRepository):
        self.eventRepository = eventRepository
        self.attendancePersonRepository = attendancePersonRepository
        self.attendanceRepository = attendanceRepository
        self.personnelTypeRepository = personnelTypeRepository

    def getEventByToken(self, tokenEvent: str) -> PublicEventResponseDto:
        eventFound = self._getValidEventByToken(tokenEvent)
        attendanceCount = self.attendanceRepository.countByEvent(eventFound.IdEvent)
        return PublicEventResponseDto.model_validate(eventFound).model_copy(
            update={"attendedPeopleNumber": attendanceCount}
        )

    def getPersonByDocument(self, documentNumber: str):
        cleanDocument = self._cleanRequiredText(documentNumber, "La cédula es obligatoria.")
        personFound = self.attendancePersonRepository.getByDocument(cleanDocument)

        if not personFound:
            return None

        latestAttendance = self.attendanceRepository.getLatestByPerson(personFound.IdAttendancePerson)
        personnelType = (
            self.personnelTypeRepository.getById(latestAttendance.IdPersonnelType)
            if latestAttendance else None
        )
        personnelTypeId = (
            personnelType.IdPersonnelType
            if personnelType and personnelType.namePersonnelType.strip().lower() != "no aplica"
            else None
        )

        return AttendancePersonResponseDto.model_validate(personFound).model_copy(
            update={"IdPersonnelType": personnelTypeId}
        )

    def registerAttendance(self, tokenEvent: str, data: AttendanceRegisterDto, ipAddress: str | None, userAgent: str | None) -> AttendanceRegisterResponseDto:
        eventFound = self._getValidEventByToken(tokenEvent)
        eventId = eventFound.IdEvent

        self._validateRegisterData(data)

        cleanDocument = data.documentNumberAttendancePerson.strip()
        personFound = self.attendancePersonRepository.getByDocument(cleanDocument)

        if personFound:
            existingAttendance = self.attendanceRepository.getByEventAndPerson(
                eventId,
                personFound.IdAttendancePerson,
            )

            if existingAttendance:
                raise ValueError(
                    "Esta persona ya registró asistencia para este evento."
                )

        imageBytes = self._decodeSignature(data.signatureBase64)
        receipt = {}
        storage = GcsStorage()
        try:
            def saveSignature(personId: int) -> str:
                path = f"signatures/{personId}/{uuid.uuid4().hex}.png"
                receipt["path"] = path
                reference = storage.objectReference(path)
                receipt["generation"] = storage.upload(path, imageBytes, "image/png")
                return reference

            try:
                attendanceId, personId, attendanceCount, oldSignature = (
                    self.attendanceRepository.registerWithSignature(
                        eventId, data, ipAddress, userAgent, saveSignature,
                    )
                )
            except Exception as error:
                uncertain = isinstance(error, AttendancePersistenceError) and error.commitUncertain
                if "generation" in receipt and not uncertain:
                    try:
                        storage.delete(receipt["path"], expectedGeneration=receipt["generation"])
                    except Exception:
                        logger.warning("Firma pendiente de limpieza tras rollback | object=%s", receipt["path"])
                elif "path" in receipt:
                    # A lost upload/commit acknowledgement cannot prove failure.
                    # Never delete an object which may now be the current signature.
                    logger.warning("Firma conservada por resultado incierto | object=%s", receipt["path"])
                raise

            # The row lock supplied the actual previous signature, not the stale
            # public lookup. Concurrent registrations therefore retire a chain of
            # unique versions and never delete the current object of another call.
            if oldSignature and oldSignature.startswith("gs://"):
                try:
                    oldPath = storage.relativePathFromReference(oldSignature)
                    if re.fullmatch(rf"signatures/{personId}/[0-9a-f]{{32}}\.png", oldPath) and oldPath != receipt["path"]:
                        storage.delete(oldPath)
                except Exception:
                    logger.warning("Firma anterior pendiente de limpieza | personId=%s", personId)
        finally:
            try:
                storage.close()
            except Exception:
                # Closing a transport must not turn a committed attendance into
                # an apparent failure or obscure the original registration error.
                logger.warning("No fue posible cerrar el transporte de firmas GCS.")

        return AttendanceRegisterResponseDto(
            IdAttendance=attendanceId,
            IdEvent=eventId,
            IdAttendancePerson=personId,
            attendedPeopleNumber=attendanceCount
        )

    def _getValidEventByToken(self, tokenEvent: str) -> Event:
        cleanToken = self._cleanRequiredText(tokenEvent, "El token del evento es obligatorio.")

        eventFound = self.eventRepository.getByToken(cleanToken)

        if not eventFound:
            raise ValueError("El evento no existe o el enlace no es válido.")

        now = self._currentDateTime()
        eventFound, attendanceEndDateTime = self._syncAttendanceWindow(
            eventFound,
            now,
        )

        if now > attendanceEndDateTime:
            if eventFound.IdEventStatus == self.STATUS_ACTIVE:
                self.eventRepository.setStatus(
                    eventFound.IdEvent,
                    self.STATUS_INACTIVE,
                )

            raise ValueError("El formulario de asistencia ya no está disponible.")

        if not self._eventIsActive(eventFound):
            raise ValueError("El formulario de asistencia no está disponible porque el evento no está activo.")

        if now < eventFound.attendanceStartDateTime:
            raise ValueError("El formulario de asistencia aún no está disponible.")

        return eventFound

    def _currentDateTime(self) -> datetime:
        return datetime.now(APP_TIMEZONE_INFO).replace(tzinfo=None)

    def _getAttendanceEndDateTime(self, event: Event) -> datetime:
        return (
            datetime.combine(event.dateEvent, event.endTimeEvent)
            + self.ATTENDANCE_GRACE_PERIOD
        )

    def _syncAttendanceWindow(
        self,
        event: Event,
        currentDateTime: datetime,
    ) -> tuple[Event, datetime]:
        eventEndDateTime = datetime.combine(event.dateEvent, event.endTimeEvent)
        attendanceEndDateTime = self._getAttendanceEndDateTime(event)
        wasInactiveWithLegacyWindow = (
            event.IdEventStatus == self.STATUS_INACTIVE
            and event.attendanceEndDateTime == eventEndDateTime
            and currentDateTime <= attendanceEndDateTime
        )

        if event.attendanceEndDateTime != attendanceEndDateTime:
            updatedEvent = self.eventRepository.update(
                event.IdEvent,
                {"attendanceEndDateTime": attendanceEndDateTime},
                None,
                None,
            )
            event = updatedEvent if updatedEvent else event

        if wasInactiveWithLegacyWindow:
            updatedEvent = self.eventRepository.setStatus(
                event.IdEvent,
                self.STATUS_ACTIVE,
            )
            event = updatedEvent if updatedEvent else event

        return event, attendanceEndDateTime

    def _eventIsActive(self, event: Event) -> bool:
        if not event.eventStatus or not event.eventStatus.nameEventStatus:
            return False

        return event.eventStatus.nameEventStatus.strip().lower() == self.STATUS_ACTIVE_NAME

    def _validateRegisterData(self, data: AttendanceRegisterDto) -> None:
        self._cleanRequiredText(data.documentNumberAttendancePerson, "La cédula es obligatoria.")
        self._cleanRequiredText(data.fullNameAttendancePerson, "El nombre completo es obligatorio.")
        
        if not data.IdPersonnelType:
            raise ValueError("Debe seleccionar el tipo de personal.")

        personnelTypeFound = self.personnelTypeRepository.getById(data.IdPersonnelType)

        if not personnelTypeFound or personnelTypeFound.namePersonnelType.strip().lower() == "no aplica":
            raise ValueError("El tipo de personal seleccionado no es válido.")

        self._cleanRequiredText(data.signatureBase64, "Debe registrar la firma para guardar la asistencia.")

    def _cleanRequiredText(self, value: str | None, message: str) -> str:
        if not value or not value.strip():
            raise ValueError(message)

        return value.strip()

    def _decodeSignature(self, signatureBase64: str) -> bytes:
        try:
            signatureContent = signatureBase64.strip()
            if signatureContent.startswith("data:"):
                header, signatureContent = signatureContent.split(",", 1)
                if header != "data:image/png;base64":
                    raise ValueError
            imageBytes = base64.b64decode(signatureContent, validate=True)
            with Image.open(BytesIO(imageBytes)) as image:
                if image.format != "PNG":
                    raise ValueError
                image.verify()
            return imageBytes
        except Exception:
            raise ValueError("La firma debe ser una imagen PNG válida.") from None
