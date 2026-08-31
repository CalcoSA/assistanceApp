from app.domain.dtos.AttendanceDto import (PublicEventResponseDto, AttendancePersonResponseDto, AttendanceRegisterDto, AttendanceRegisterResponseDto,)
from app.application.interfaces.IAttendanceApplication import IPublicAttendanceApplication
from app.domain.interfaces.IAttendancePersonRepository import IAttendancePersonRepository
from app.domain.interfaces.IPersonnelTypeRepository import IPersonnelTypeRepository
from app.domain.interfaces.IAttendanceRepository import IAttendanceRepository
from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.entities.Event import Event
from app.infrastructure.db.config import APP_TIMEZONE_INFO
from datetime import datetime, timedelta
import base64
import os
import re

class PublicAttendanceApplication(IPublicAttendanceApplication):

    STATUS_ACTIVE_NAME = "activo"
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    ATTENDANCE_GRACE_PERIOD = timedelta(minutes=30)

    def __init__(self, eventRepository: IEventRepository, attendancePersonRepository: IAttendancePersonRepository, attendanceRepository: IAttendanceRepository, personnelTypeRepository: IPersonnelTypeRepository):
        self.eventRepository = eventRepository
        self.attendancePersonRepository = attendancePersonRepository
        self.attendanceRepository = attendanceRepository
        self.uploadDir = os.getenv("UPLOAD_DIR", "uploads")
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

        return AttendancePersonResponseDto.model_validate(personFound)

    def registerAttendance(self, tokenEvent: str, data: AttendanceRegisterDto, ipAddress: str | None, userAgent: str | None) -> AttendanceRegisterResponseDto:
        eventFound = self._getValidEventByToken(tokenEvent)

        self._validateRegisterData(data)

        cleanDocument = data.documentNumberAttendancePerson.strip()
        personFound = self.attendancePersonRepository.getByDocument(cleanDocument)
        signaturePath = None

        if personFound:
            existingAttendance = self.attendanceRepository.getByEventAndPerson(
                eventFound.IdEvent,
                personFound.IdAttendancePerson,
            )

            if existingAttendance:
                raise ValueError(
                    "Esta persona ya registró asistencia para este evento."
                )

        if personFound and data.signatureBase64:
            signaturePath = self._saveSignature(cleanDocument, data.signatureBase64, personFound.signaturePathAttendancePerson)

        if not personFound and data.signatureBase64:
            signaturePath = self._saveSignature(cleanDocument, data.signatureBase64, None)

        if not personFound and not data.signatureBase64:
            raise ValueError("Debe registrar la firma para guardar la asistencia.")

        if personFound and not personFound.signaturePathAttendancePerson and not data.signatureBase64:
            raise ValueError("Debe registrar la firma para guardar la asistencia.")

        if personFound:
            personSaved = self.attendancePersonRepository.update(personFound, data, signaturePath)
        else:
            personSaved = self.attendancePersonRepository.create(data, signaturePath)

        attendanceCreated, attendanceCount = (
            self.attendanceRepository.createAndCount(
                eventFound.IdEvent,
                personSaved.IdAttendancePerson,
                data.IdPersonnelType,
                ipAddress,
                userAgent,
            )
        )

        return AttendanceRegisterResponseDto(
            IdAttendance=attendanceCreated.IdAttendance,
            IdEvent=eventFound.IdEvent,
            IdAttendancePerson=personSaved.IdAttendancePerson,
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

        if not personnelTypeFound:
            raise ValueError("El tipo de personal seleccionado no es válido.")

    def _cleanRequiredText(self, value: str | None, message: str) -> str:
        if not value or not value.strip():
            raise ValueError(message)

        return value.strip()

    def _sanitizeDocument(self, documentNumber: str) -> str:
        cleanDocument = re.sub(r"[^a-zA-Z0-9_-]", "", documentNumber)

        if not cleanDocument:
            raise ValueError("La cédula contiene caracteres no válidos.")

        return cleanDocument

    def _saveSignature(self, documentNumber: str, signatureBase64: str, oldSignaturePath: str | None) -> str:
        cleanDocument = self._sanitizeDocument(documentNumber)

        signatureDirectory = os.path.join(self.uploadDir, "signatures", cleanDocument)
        os.makedirs(signatureDirectory, exist_ok=True)

        if oldSignaturePath:
            oldFilePath = oldSignaturePath.lstrip("/").replace("/", os.sep)

            if os.path.exists(oldFilePath):
                os.remove(oldFilePath)

        signatureContent = signatureBase64

        if "," in signatureContent:
            signatureContent = signatureContent.split(",", 1)[1]

        try:
            imageBytes = base64.b64decode(signatureContent)
        except Exception:
            raise ValueError("La firma no tiene un formato válido.")

        fileName = f"signature_{cleanDocument}.png"
        filePath = os.path.join(signatureDirectory, fileName)

        with open(filePath, "wb") as outputFile:
            outputFile.write(imageBytes)

        return f"/uploads/signatures/{cleanDocument}/{fileName}"
