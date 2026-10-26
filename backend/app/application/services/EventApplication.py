from app.domain.dtos.EventDto import (EventCreateDto, EventQrResponseDto, EventResponseDto, EventUpdateDto, EventCancelDto, EventPaginatedResponseDto)
from app.application.interfaces.IEventApplication import IEventApplication
from app.application.interfaces.IEventNotificationApplication import IEventNotificationApplication
from app.application.services.PensumFile import readPensumUpload
from app.domain.dtos.TrainingParameterDto import normalizeTopics
from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.dtos.EventDto import EventAttendanceResponseDto
from app.infrastructure.db.config import APP_TIMEZONE_INFO, settings
from app.infrastructure.storage.GcsStorage import GcsStorage
from app.domain.entities.Event import Event
from fastapi import UploadFile
from datetime import datetime, time, timedelta
import qrcode
import uuid
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
import re

logger = logging.getLogger(__name__)
QR_CLEANUP_INTERVAL_SECONDS = 300


def cleanupEventQrs() -> None:
    # Each pass owns its session inside the worker thread; request sessions are
    # never shared with the periodic task or other server processes.
    from app.infrastructure.db.connection import SessionLocal
    from app.infrastructure.repositories.EventRepository import EventRepository

    with SessionLocal() as db:
        EventApplication(EventRepository(db)).cleanupExpiredQrs()


@asynccontextmanager
async def eventQrLifespan(app):
    stop = asyncio.Event()

    async def cleanup():
        try:
            await asyncio.to_thread(cleanupEventQrs)
        except Exception as error:
            logger.warning("No fue posible completar la limpieza de QR; se reintentará | errorType=%s", type(error).__name__)

    async def periodicallyCleanup():
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), QR_CLEANUP_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                await cleanup()

    await cleanup()
    task = asyncio.create_task(periodicallyCleanup(), name="event-qr-cleanup")
    try:
        yield
    finally:
        stop.set()
        await task

class EventApplication(IEventApplication):

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_CANCELLED = 3
    STATUS_ACTIVE_NAME = "activo"
    STATUS_INACTIVE_NAME = "inactivo"
    STATUS_CANCELLED_NAME = "cancelado"
    VIEW_ALL_ROLES = ["administrador"]
    CREATE_EVENT_ROLES = ["administrador", "formador"]
    FACILITATOR_TYPE_INTERNAL = "INTERNO"
    FACILITATOR_TYPE_EXTERNAL = "EXTERNO"
    FACILITATOR_TYPES = {
        FACILITATOR_TYPE_INTERNAL,
        FACILITATOR_TYPE_EXTERNAL,
    }
    ATTENDANCE_GRACE_PERIOD = timedelta(minutes=30)

    def __init__(
        self,
        eventRepository: IEventRepository,
        eventNotificationApplication: IEventNotificationApplication | None = None,
    ):
        self.eventRepository = eventRepository
        self.eventNotificationApplication = eventNotificationApplication

        publicBaseUrl = settings.PUBLIC_BASE_URL
        self.publicAttendanceBaseUrl = f"{publicBaseUrl.rstrip('/')}/attendance"

        self.uploadDir = os.getenv("UPLOAD_DIR", "uploads")

    def getAllByUserScope(self, userLogin: str, roles: list[str]):
        if self._userCanViewAllEvents(roles):
            events = self.eventRepository.getAll()
        else:
            events = self.eventRepository.getByCreatedBy(userLogin)

        return [
            self._buildResponse(self._syncStatusByEndDateTime(event))
            for event in events
        ]

    def getByIdByUserScope(self, IdEvent: int, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar este evento.")

        return self._buildResponse(eventFound)
    
    def getAttendancesByEventScope(self, IdEvent: int, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar los asistentes de este evento.")

        attendances = self.eventRepository.getAttendancesByEvent(IdEvent)

        result = []
        for attendance in attendances:
            item = EventAttendanceResponseDto.model_validate(attendance)
            if item.attendancePerson and item.attendancePerson.signaturePathAttendancePerson:
                # Keep storage references in the DB; expose an authorized backend
                # resource for both the signature viewer and the Excel export.
                item.attendancePerson.signaturePathAttendancePerson = (
                    f"/events/{IdEvent}/attendances/{item.IdAttendance}/signature"
                )
            result.append(item)
        return result

    def getAttendanceSignatureByUserScope(
        self, IdEvent: int, IdAttendance: int, userLogin: str, roles: list[str],
    ) -> bytes:
        eventFound = self.eventRepository.getById(IdEvent)
        if not eventFound:
            raise ValueError("El evento no existe.")
        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar las firmas de este evento.")
        attendance = self.eventRepository.getAttendanceByEvent(IdEvent, IdAttendance)
        person = attendance.attendancePerson if attendance else None
        reference = person.signaturePathAttendancePerson if person else None
        if not reference:
            raise ValueError("No se encontró la firma registrada.")
        if reference.startswith("gs://"):
            with GcsStorage() as storage:
                relativePath = storage.relativePathFromReference(reference)
                if not relativePath.startswith(f"signatures/{person.IdAttendancePerson}/"):
                    raise ValueError("La referencia no corresponde a la firma de esta persona.")
                return storage.download(relativePath)

        # Historical signatures stay on disk. Resolve only within uploads/signatures,
        # rejecting traversal, absolute paths and symlinks outside that directory.
        if not reference.startswith("/uploads/signatures/"):
            raise ValueError("La referencia de firma local no es válida.")
        root = (Path(settings.UPLOAD_DIR).resolve() / "signatures").resolve()
        path = (root / reference.removeprefix("/uploads/signatures/")).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("No se encontró la firma registrada.")
        return path.read_bytes()
    
    def getPaginatedByUserScope(self, page: int, pageSize: int, status, userLogin: str, roles: list[str],):
        createdByUserLogin = None

        if not self._userCanViewAllEvents(roles):
            createdByUserLogin = userLogin

        result = self.eventRepository.getPaginated(page=page, pageSize=pageSize, status=status, createdByUserLogin=createdByUserLogin,)

        items = [
            self._buildResponse(self._syncStatusByEndDateTime(event))
            for event in result["items"]
        ]

        return EventPaginatedResponseDto(items=items, total=result["total"], page=result["page"], pageSize=result["pageSize"], totalPages=result["totalPages"],)

    def create(self, eventData: EventCreateDto, userLogin: str, roles: list[str]):
        if not self._userCanCreateEvents(roles):
            raise PermissionError("No tiene permisos para crear eventos.")

        self._validateCreateData(eventData)
        if eventData.IdTrainingParameter is not None:
            if len(eventData.titleEvent.strip().upper()) > 200:
                raise ValueError("El título del evento no puede superar 200 caracteres.")
            if "topics" in eventData.model_fields_set:
                if not eventData.topics:
                    raise ValueError("El evento parametrizado debe tener al menos un tema.")
                normalizeTopics(eventData.topics)
        facilitatorData = self._normalizeEventFacilitators(
            facilitatorName=eventData.facilitatorNameEvent,
            facilitatorType=eventData.facilitatorTypeEvent,
            facilitatorCompany=eventData.facilitatorCompanyEvent,
            facilitatorPosition=eventData.facilitatorPositionEvent,
            secondFacilitatorName=eventData.secondFacilitatorNameEvent,
            secondFacilitatorType=eventData.secondFacilitatorTypeEvent,
            secondFacilitatorCompany=eventData.secondFacilitatorCompanyEvent,
            secondFacilitatorPosition=eventData.secondFacilitatorPositionEvent,
            thirdFacilitatorName=eventData.thirdFacilitatorNameEvent,
            thirdFacilitatorType=eventData.thirdFacilitatorTypeEvent,
            thirdFacilitatorCompany=eventData.thirdFacilitatorCompanyEvent,
            thirdFacilitatorPosition=eventData.thirdFacilitatorPositionEvent,
        )

        createdAt = self._currentDateTime()
        attendanceStartDateTime = createdAt
        attendanceEndDateTime = self._getAttendanceEndDateTime(
            eventData.dateEvent,
            eventData.endTimeEvent,
        )

        if attendanceEndDateTime <= createdAt:
            raise ValueError("La fecha y hora final del evento debe ser mayor a la fecha y hora actual.")

        tokenEvent = uuid.uuid4().hex
        publicUrlEvent = f"{self.publicAttendanceBaseUrl}/{tokenEvent}"
        qrPathEvent = self._generateQr(tokenEvent, publicUrlEvent)
        uppercaseTopics = [topic.strip().upper() for topic in eventData.topics if topic.strip()]
        if eventData.IdTrainingParameter is not None and "topics" not in eventData.model_fields_set:
            uppercaseTopics = None

        newEvent = Event(
            IdTrainingParameter=eventData.IdTrainingParameter,
            titleEvent=eventData.titleEvent.strip().upper(),
            descriptionEvent=self._uppercaseOptionalText(eventData.descriptionEvent),
            dateEvent=eventData.dateEvent,
            durationEvent=self._calculateDuration(
                eventData.startTimeEvent,
                eventData.endTimeEvent,
            ),
            startTimeEvent=eventData.startTimeEvent,
            endTimeEvent=eventData.endTimeEvent,
            IdSolutionCenter=eventData.IdSolutionCenter,
            IdAssistanceReason=eventData.IdAssistanceReason,
            IdSpecificTrainingProgram=eventData.IdSpecificTrainingProgram,
            IdEventCategory=eventData.IdEventCategory,
            IdEventStatus=self.STATUS_ACTIVE,
            **facilitatorData,
            scheduledPeopleNumber=eventData.scheduledPeopleNumber,
            attendedPeopleNumber=None,
            observationsEvent=self._uppercaseOptionalText(eventData.observationsEvent),
            eventPlace=self._uppercaseOptionalText(eventData.eventPlace),
            attendanceStartDateTime=attendanceStartDateTime,
            attendanceEndDateTime=attendanceEndDateTime,
            tokenEvent=tokenEvent,
            publicUrlEvent=publicUrlEvent,
            qrPathEvent=qrPathEvent,
            isPaidTrainingEvent=eventData.isPaidTrainingEvent,
            isNewStaffInductionEvent=eventData.isNewStaffInductionEvent or False,
            createdByUserLogin=userLogin,
            createdAt=createdAt
        )

        eventCreated = self.eventRepository.create(newEvent, uppercaseTopics, eventData.competencies)

        response = self._buildResponse(eventCreated)

        if self.eventNotificationApplication:
            notificationResult = self.eventNotificationApplication.notifyEventCreated(
                response
            )
            response = response.model_copy(
                update={
                    "notificationEmailSent": notificationResult.sent,
                    "notificationMessage": notificationResult.message,
                }
            )

        return response

    def update(self, IdEvent: int, eventData: EventUpdateDto, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para actualizar este evento.")

        if getattr(eventFound, "IdTrainingParameter", None) is not None and eventData.topics is not None:
            eventData.topics = normalizeTopics(eventData.topics)
            if not eventData.topics:
                raise ValueError("El evento parametrizado debe tener al menos un tema.")

        if eventFound.IdEventStatus == self.STATUS_CANCELLED:
            raise ValueError("No se puede actualizar un evento cancelado.")

        if self._eventHasStarted(eventFound):
            self._validateUpdateAfterEventStarted(eventData, eventFound)
        else:
            self._validateUpdateBeforeEventStarted(eventData, eventFound)

        facilitatorData = self._normalizeEventFacilitators(
            facilitatorName=self._getFinalUpdateValue(
                eventData,
                "facilitatorNameEvent",
                eventFound.facilitatorNameEvent,
            ),
            facilitatorType=self._getFinalUpdateValue(
                eventData,
                "facilitatorTypeEvent",
                self._inferFacilitatorType(
                    eventFound.facilitatorNameEvent,
                    eventFound.facilitatorCompanyEvent,
                ),
            ),
            facilitatorCompany=self._getFinalUpdateValue(
                eventData,
                "facilitatorCompanyEvent",
                eventFound.facilitatorCompanyEvent,
            ),
            facilitatorPosition=self._getFinalUpdateValue(
                eventData,
                "facilitatorPositionEvent",
                eventFound.facilitatorPositionEvent,
            ),
            secondFacilitatorName=self._getFinalUpdateValue(
                eventData,
                "secondFacilitatorNameEvent",
                eventFound.secondFacilitatorNameEvent,
            ),
            secondFacilitatorType=self._getFinalUpdateValue(
                eventData,
                "secondFacilitatorTypeEvent",
                self._inferFacilitatorType(
                    eventFound.secondFacilitatorNameEvent,
                    eventFound.secondFacilitatorCompanyEvent,
                ),
            ),
            secondFacilitatorCompany=self._getFinalUpdateValue(
                eventData,
                "secondFacilitatorCompanyEvent",
                eventFound.secondFacilitatorCompanyEvent,
            ),
            secondFacilitatorPosition=self._getFinalUpdateValue(
                eventData,
                "secondFacilitatorPositionEvent",
                eventFound.secondFacilitatorPositionEvent,
            ),
            thirdFacilitatorName=self._getFinalUpdateValue(
                eventData,
                "thirdFacilitatorNameEvent",
                eventFound.thirdFacilitatorNameEvent,
            ),
            thirdFacilitatorType=self._getFinalUpdateValue(
                eventData,
                "thirdFacilitatorTypeEvent",
                self._inferFacilitatorType(
                    eventFound.thirdFacilitatorNameEvent,
                    eventFound.thirdFacilitatorCompanyEvent,
                ),
            ),
            thirdFacilitatorCompany=self._getFinalUpdateValue(
                eventData,
                "thirdFacilitatorCompanyEvent",
                eventFound.thirdFacilitatorCompanyEvent,
            ),
            thirdFacilitatorPosition=self._getFinalUpdateValue(
                eventData,
                "thirdFacilitatorPositionEvent",
                eventFound.thirdFacilitatorPositionEvent,
            ),
        )

        updateData = eventData.model_dump(
            exclude_unset=True,
            exclude={
                "topics",
                "competencies",
                "durationEvent",
                "facilitatorTypeEvent",
                "secondFacilitatorTypeEvent",
                "thirdFacilitatorTypeEvent",
            },
        )
        updateData.update(facilitatorData)

        if "titleEvent" in updateData and updateData["titleEvent"] is not None:
            updateData["titleEvent"] = updateData["titleEvent"].strip()

        finalDateEvent = (
            eventData.dateEvent
            if eventData.dateEvent is not None
            else eventFound.dateEvent
        )

        finalEndTimeEvent = (
            eventData.endTimeEvent
            if eventData.endTimeEvent is not None
            else eventFound.endTimeEvent
        )

        finalStartTimeEvent = (
            eventData.startTimeEvent
            if eventData.startTimeEvent is not None
            else eventFound.startTimeEvent
        )

        scheduleTimeChanged = (
            finalStartTimeEvent != eventFound.startTimeEvent
            or finalEndTimeEvent != eventFound.endTimeEvent
        )

        if scheduleTimeChanged:
            updateData["durationEvent"] = self._calculateDuration(
                finalStartTimeEvent,
                finalEndTimeEvent,
            )

        updateData["attendanceEndDateTime"] = self._getAttendanceEndDateTime(
            finalDateEvent,
            finalEndTimeEvent,
        )

        updateData["updatedByUserLogin"] = userLogin
        updateData["updatedAt"] = self._currentDateTime()

        eventUpdated = self.eventRepository.update(IdEvent, updateData, eventData.topics, eventData.competencies)

        if not eventUpdated:
            raise ValueError("El evento no existe.")

        return self._buildResponse(eventUpdated)

    def cancel(self, IdEvent: int, eventData: EventCancelDto, userLogin: str, roles: list[str]):
        cancellationReason = eventData.cancellationReason.strip()

        if not cancellationReason:
            raise ValueError("El motivo de cancelación es obligatorio.")

        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para cancelar este evento.")

        if self._eventHasStatus(eventFound, self.STATUS_CANCELLED_NAME):
            raise ValueError("El evento ya se encuentra cancelado.")

        if self._eventHasStatus(eventFound, self.STATUS_INACTIVE_NAME):
            raise ValueError("No se puede cancelar un evento inactivo.")

        attendanceCount = self.eventRepository.countAttendances(IdEvent)

        if self._eventHasStarted(eventFound) and attendanceCount > 0:
            raise ValueError("No se puede cancelar el evento porque ya inició y tiene asistentes registrados.")

        cancellationObservation = f"Motivo de cancelación: {cancellationReason}"
        existingObservations = eventFound.observationsEvent
        observationsEvent = (
            f"{existingObservations.rstrip()}\n{cancellationObservation}"
            if existingObservations and existingObservations.strip()
            else cancellationObservation
        )
        eventCancelled = self.eventRepository.cancel(IdEvent, observationsEvent)

        if not eventCancelled:
            raise ValueError("El evento no existe.")

        response = self._buildResponse(eventCancelled)
        self._cleanupEventQr(IdEvent)
        return response

    def delete(self, IdEvent: int, userLogin: str, roles: list[str]) -> bool:
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para eliminar este evento.")

        if self._eventHasStarted(eventFound):
            raise ValueError("No se puede eliminar un evento que ya inició. Use cancelar si aplica.")

        return self.eventRepository.delete(IdEvent)

    def getQrInfo(self, IdEvent: int, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar el QR de este evento.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        return EventQrResponseDto(IdEvent=eventFound.IdEvent, tokenEvent=eventFound.tokenEvent, publicUrlEvent=eventFound.publicUrlEvent, qrPathEvent=self._visibleQrPath(eventFound))

    def getQrImage(self, IdEvent: int, userLogin: str, roles: list[str]) -> bytes:
        qrInfo = self.getQrInfo(IdEvent, userLogin, roles)
        if not qrInfo.qrPathEvent:
            raise ValueError("El QR ya no está disponible para este evento.")
        try:
            # Read before returning the response. A concurrent unlink is either
            # harmless to an open file or results in a controlled 404, not a late
            # FileResponse error after the response headers were already sent.
            return self._resolveQrPath(qrInfo).read_bytes()
        except OSError:
            raise ValueError("No se encontró la imagen QR en el servidor.") from None

    def _qrHasExpired(self, event: Event) -> bool:
        return event.IdEventStatus == self.STATUS_CANCELLED or self._currentDateTime() > self._getAttendanceEndDateTime(
            event.dateEvent, event.endTimeEvent,
        )

    def _resolveQrPath(self, event) -> Path:
        token = event.tokenEvent
        if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", token):
            raise ValueError("El nombre del QR no es válido.")
        fileName = f"qr_event_{token}.png"
        if event.qrPathEvent != f"/uploads/qrs/{fileName}":
            raise ValueError("La ruta no corresponde al QR de este evento.")
        root = Path(self.uploadDir).resolve() / "qrs"
        path = root / fileName
        if root.resolve() != root or path.is_symlink() or path.resolve().parent != root:
            raise ValueError("La ruta del QR no está dentro del directorio permitido.")
        return path

    def _visibleQrPath(self, event: Event) -> str | None:
        if not getattr(event, "qrPathEvent", None) or self._qrHasExpired(event):
            return None
        try:
            return event.qrPathEvent if self._resolveQrPath(event).is_file() else None
        except (OSError, ValueError):
            return None

    def _removeExpiredQr(self, event: Event) -> bool:
        if not self._qrHasExpired(event):
            return False
        self._resolveQrPath(event).unlink(missing_ok=True)
        return True

    def _cleanupEventQr(self, IdEvent: int) -> None:
        try:
            self.eventRepository.cleanupQr(IdEvent, self._removeExpiredQr)
        except Exception as error:
            logger.warning("Limpieza de QR pendiente; se reintentará | IdEvent=%s | errorType=%s", IdEvent, type(error).__name__)

    def cleanupExpiredQrs(self) -> None:
        throughDate = self._currentDateTime().date()
        afterId = 0
        while True:
            candidates = self.eventRepository.getQrCleanupCandidates(throughDate, afterId)
            if not candidates:
                return
            for eventId in candidates:
                self._cleanupEventQr(eventId)
            afterId = candidates[-1]

    def _validateCreateData(self, eventData: EventCreateDto) -> None:
        if not eventData.titleEvent.strip():
            raise ValueError("El título del evento es obligatorio.")

        if (
            eventData.scheduledPeopleNumber is not None
            and eventData.scheduledPeopleNumber < 0
        ):
            raise ValueError(
                "El número de personas programadas debe ser mayor o igual a cero."
            )

        eventStartDateTime = datetime.combine(eventData.dateEvent, eventData.startTimeEvent)

        if eventStartDateTime <= self._currentDateTime():
            raise ValueError("La fecha y hora de inicio deben ser posteriores a la fecha y hora actual.")

        if eventData.startTimeEvent >= eventData.endTimeEvent:
            raise ValueError("La hora inicial del evento debe ser menor a la hora final.")
        
        if eventData.isPaidTrainingEvent is None:
            raise ValueError("Debe seleccionar si la capacitación es dentro del horario laboral o paga.")

    def _validateUpdateBeforeEventStarted(self, eventData: EventUpdateDto, eventFound: Event) -> None:
        if eventData.titleEvent is not None and not eventData.titleEvent.strip():
            raise ValueError("El título del evento no puede estar vacío.")

        finalDateEvent = (
            eventData.dateEvent
            if eventData.dateEvent is not None
            else eventFound.dateEvent
        )

        finalStartTimeEvent = (
            eventData.startTimeEvent
            if eventData.startTimeEvent is not None
            else eventFound.startTimeEvent
        )

        finalEndTimeEvent = (
            eventData.endTimeEvent
            if eventData.endTimeEvent is not None
            else eventFound.endTimeEvent
        )

        if finalStartTimeEvent >= finalEndTimeEvent:
            raise ValueError("La hora inicial del evento debe ser menor a la hora final.")

        finalEndDateTime = datetime.combine(finalDateEvent, finalEndTimeEvent)

        if finalEndDateTime <= self._currentDateTime():
            raise ValueError("La fecha y hora final del evento debe ser mayor a la fecha y hora actual.")

    def _validateUpdateAfterEventStarted(
        self,
        eventData: EventUpdateDto,
        eventFound: Event,
    ) -> None:
        if (
            eventData.dateEvent is not None
            and eventData.dateEvent != eventFound.dateEvent
        ):
            raise ValueError("No se puede reagendar un evento que ya inició.")

        if (
            eventData.startTimeEvent is not None
            and eventData.startTimeEvent != eventFound.startTimeEvent
        ):
            raise ValueError("No se puede cambiar la hora de inicio de un evento que ya inició.")

        if (
            eventData.endTimeEvent is not None
            and eventData.endTimeEvent != eventFound.endTimeEvent
        ):
            raise ValueError("No se puede cambiar la hora final de un evento que ya inició.")

    def _eventHasStarted(self, event: Event) -> bool:
        eventStartDateTime = datetime.combine(event.dateEvent, event.startTimeEvent)
        return self._currentDateTime() >= eventStartDateTime

    def _syncStatusByEndDateTime(self, event: Event) -> Event:
        eventEndDateTime = datetime.combine(
            event.dateEvent,
            event.endTimeEvent,
        )
        attendanceEndDateTime = self._getAttendanceEndDateTime(
            event.dateEvent,
            event.endTimeEvent,
        )
        currentDateTime = self._currentDateTime()
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

        if (
            event.IdEventStatus == self.STATUS_ACTIVE
            and currentDateTime > attendanceEndDateTime
        ):
            updatedEvent = self.eventRepository.setStatus(event.IdEvent, self.STATUS_INACTIVE)

            return updatedEvent if updatedEvent else event

        return event

    def _generateQr(self, tokenEvent: str, publicUrlEvent: str) -> str:
        qrDirectory = os.path.join(self.uploadDir, "qrs")
        os.makedirs(qrDirectory, exist_ok=True)

        qrFileName = f"qr_event_{tokenEvent}.png"
        filePath = os.path.join(qrDirectory, qrFileName)

        qrImage = qrcode.make(publicUrlEvent)
        qrImage.save(filePath)

        return f"/uploads/qrs/{qrFileName}"

    def _normalizeText(self, value: str | None) -> str:
        return value.strip().lower() if value else ""

    def _currentDateTime(self) -> datetime:
        return datetime.now(APP_TIMEZONE_INFO).replace(tzinfo=None)

    def _getAttendanceEndDateTime(self, eventDate, eventEndTime) -> datetime:
        return (
            datetime.combine(eventDate, eventEndTime)
            + self.ATTENDANCE_GRACE_PERIOD
        )

    def _uppercaseOptionalText(self, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    def _calculateDuration(self, startTime: time, endTime: time) -> str:
        startMinutes = startTime.hour * 60 + startTime.minute
        endMinutes = endTime.hour * 60 + endTime.minute
        totalMinutes = endMinutes - startMinutes

        if totalMinutes <= 0:
            raise ValueError("La hora inicial del evento debe ser menor a la hora final.")

        hours, minutes = divmod(totalMinutes, 60)
        durationParts = []

        if hours:
            durationParts.append(f"{hours} {'HORA' if hours == 1 else 'HORAS'}")

        if minutes:
            durationParts.append(
                f"{minutes} {'MINUTO' if minutes == 1 else 'MINUTOS'}"
            )

        return " ".join(durationParts)

    def _normalizeEventFacilitators(
        self,
        *,
        facilitatorName: str | None,
        facilitatorType: str | None,
        facilitatorCompany: str | None,
        facilitatorPosition: str | None,
        secondFacilitatorName: str | None,
        secondFacilitatorType: str | None,
        secondFacilitatorCompany: str | None,
        secondFacilitatorPosition: str | None,
        thirdFacilitatorName: str | None,
        thirdFacilitatorType: str | None,
        thirdFacilitatorCompany: str | None,
        thirdFacilitatorPosition: str | None,
    ) -> dict[str, str | None]:
        principal = self._normalizeFacilitator(
            name=facilitatorName,
            facilitatorType=facilitatorType,
            company=facilitatorCompany,
            position=facilitatorPosition,
            label="facilitador principal",
            required=True,
            positionRequired=True,
        )
        second = self._normalizeFacilitator(
            name=secondFacilitatorName,
            facilitatorType=secondFacilitatorType,
            company=secondFacilitatorCompany,
            position=secondFacilitatorPosition,
            label="segundo facilitador",
            required=False,
            positionRequired=False,
        )
        third = self._normalizeFacilitator(
            name=thirdFacilitatorName,
            facilitatorType=thirdFacilitatorType,
            company=thirdFacilitatorCompany,
            position=thirdFacilitatorPosition,
            label="tercer facilitador",
            required=False,
            positionRequired=False,
        )

        return {
            "facilitatorNameEvent": principal["name"],
            "facilitatorCompanyEvent": principal["company"],
            "facilitatorPositionEvent": principal["position"],
            "secondFacilitatorNameEvent": second["name"],
            "secondFacilitatorCompanyEvent": second["company"],
            "secondFacilitatorPositionEvent": second["position"],
            "thirdFacilitatorNameEvent": third["name"],
            "thirdFacilitatorCompanyEvent": third["company"],
            "thirdFacilitatorPositionEvent": third["position"],
        }

    def _normalizeFacilitator(
        self,
        *,
        name: str | None,
        facilitatorType: str | None,
        company: str | None,
        position: str | None,
        label: str,
        required: bool,
        positionRequired: bool,
    ) -> dict[str, str | None]:
        normalizedName = self._uppercaseOptionalText(name) or None
        normalizedType = self._uppercaseOptionalText(facilitatorType) or None
        normalizedCompany = self._uppercaseOptionalText(company) or None
        normalizedPosition = self._uppercaseOptionalText(position) or None
        hasAnyData = any(
            (
                normalizedName,
                normalizedType,
                normalizedCompany,
                normalizedPosition,
            )
        )

        if not required and not hasAnyData:
            return {"name": None, "company": None, "position": None}

        if not normalizedName:
            raise ValueError(f"El nombre del {label} es obligatorio.")

        if positionRequired and not normalizedPosition:
            raise ValueError(f"El cargo del {label} es obligatorio.")

        if not normalizedType:
            raise ValueError(f"El tipo del {label} es obligatorio.")

        if normalizedType not in self.FACILITATOR_TYPES:
            raise ValueError(
                f"El tipo del {label} debe ser INTERNO o EXTERNO."
            )

        if (
            normalizedType == self.FACILITATOR_TYPE_EXTERNAL
            and not normalizedCompany
        ):
            raise ValueError(
                f"La empresa del {label} es obligatoria cuando es EXTERNO."
            )

        if normalizedType == self.FACILITATOR_TYPE_INTERNAL:
            normalizedCompany = None

        return {
            "name": normalizedName,
            "company": normalizedCompany,
            "position": normalizedPosition,
        }

    def _inferFacilitatorType(
        self,
        facilitatorName: str | None,
        facilitatorCompany: str | None,
    ) -> str | None:
        if facilitatorCompany and facilitatorCompany.strip():
            return self.FACILITATOR_TYPE_EXTERNAL

        if facilitatorName and facilitatorName.strip():
            return self.FACILITATOR_TYPE_INTERNAL

        return None

    def _getFinalUpdateValue(
        self,
        eventData: EventUpdateDto,
        fieldName: str,
        currentValue,
    ):
        if fieldName in eventData.model_fields_set:
            return getattr(eventData, fieldName)

        return currentValue
    
    def _getEventStatusName(self, event: Event) -> str:
        if event.eventStatus and event.eventStatus.nameEventStatus:
            return self._normalizeText(event.eventStatus.nameEventStatus)
        return ""

    def _eventHasStatus(self, event: Event, statusName: str) -> bool:
        return self._getEventStatusName(event) == self._normalizeText(statusName)

    def _normalizeRoles(self, roles: list[str]) -> list[str]:
        return [self._normalizeText(role) for role in roles if role]

    def _userCanViewAllEvents(self, roles: list[str]) -> bool:
        normalizedRoles = self._normalizeRoles(roles)
        allowedRoles = [self._normalizeText(role) for role in self.VIEW_ALL_ROLES]

        return any(role in allowedRoles for role in normalizedRoles)

    def _userCanCreateEvents(self, roles: list[str]) -> bool:
        normalizedRoles = self._normalizeRoles(roles)
        allowedRoles = [self._normalizeText(role) for role in self.CREATE_EVENT_ROLES]

        return any(role in allowedRoles for role in normalizedRoles)

    def _userCanAccessEvent(self, event: Event, userLogin: str, roles: list[str]) -> bool:
        if self._userCanViewAllEvents(roles):
            return True

        return event.createdByUserLogin == userLogin

    def _buildResponse(self, event: Event) -> EventResponseDto:
        response = EventResponseDto.model_validate(event)

        return response.model_copy(
            update={
                "qrPathEvent": self._visibleQrPath(event),
                "facilitatorTypeEvent": self._inferFacilitatorType(
                    event.facilitatorNameEvent,
                    event.facilitatorCompanyEvent,
                ),
                "secondFacilitatorTypeEvent": self._inferFacilitatorType(
                    event.secondFacilitatorNameEvent,
                    event.secondFacilitatorCompanyEvent,
                ),
                "thirdFacilitatorTypeEvent": self._inferFacilitatorType(
                    event.thirdFacilitatorNameEvent,
                    event.thirdFacilitatorCompanyEvent,
                ),
            }
        )
    
    def uploadPensum(self, IdEvent: int, file: UploadFile, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para actualizar el pensum de este evento.")

        if getattr(eventFound, "IdTrainingParameter", None) is not None:
            raise ValueError("No se permite reemplazar el PÉNSUM de un evento parametrizado.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if self._eventHasStatus(eventFound, self.STATUS_CANCELLED_NAME):
            raise ValueError("No se puede actualizar el pensum de un evento cancelado.")

        originalFileName, extension, fileContent, mimeType = readPensumUpload(file)
        oldReference = eventFound.pensumPathEvent
        fileName = f"pensum_event_{IdEvent}_{uuid.uuid4().hex}{extension}"
        relativePath = f"pensum/{IdEvent}/{fileName}"
        with GcsStorage() as storage:
            reference = storage.objectReference(relativePath)
            generation = storage.upload(relativePath, fileContent, mimeType)
            try:
                eventUpdated = self.eventRepository.updatePensum(
                    IdEvent=IdEvent,
                    pensumOriginalNameEvent=originalFileName,
                    pensumPathEvent=reference,
                    pensumMimeTypeEvent=mimeType,
                    pensumSizeEvent=len(fileContent),
                    updatedByUserLogin=userLogin,
                )
            except Exception:
                # A failed commit/refresh does not prove rollback, and a later
                # read can still race an in-flight commit. Preserve both objects
                # for recovery instead of risking a DB reference to deleted data.
                logger.warning(
                    "Pensum conservado en GCS tras error de persistencia | IdEvent=%s | object=%s",
                    IdEvent, relativePath,
                )
                raise
            if not eventUpdated:
                # The repository explicitly found no event and performed no write.
                try:
                    storage.delete(relativePath, expectedGeneration=generation)
                except Exception:
                    logger.warning(
                        "No se pudo retirar el Pensum sin evento | IdEvent=%s | object=%s",
                        IdEvent, relativePath,
                    )
                raise ValueError("El evento no existe.")

            # Never remove historical local files. A failed GCS cleanup must not
            # undo a successful DB replacement or remove the newly stored object.
            if oldReference and oldReference.startswith("gs://") and oldReference != reference:
                try:
                    oldPath = storage.relativePathFromReference(oldReference)
                    if oldPath.startswith(f"pensum/{IdEvent}/"):
                        storage.delete(oldPath)
                except Exception:
                    logger.warning("No se pudo retirar el Pensum GCS reemplazado | IdEvent=%s", IdEvent)

        return self._buildResponse(eventUpdated)

    def getPensumReadUrl(
        self, IdEvent: int, userLogin: str, roles: list[str], download: bool = False,
    ) -> str:
        eventFound = self.eventRepository.getById(IdEvent)
        if not eventFound:
            raise ValueError("El evento no existe.")
        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar este pensum.")
        reference = eventFound.pensumPathEvent
        if not reference:
            raise ValueError("El evento no tiene un pensum adjunto.")
        if not reference.startswith("gs://"):
            return reference
        with GcsStorage() as storage:
            relativePath = storage.relativePathFromReference(reference)
            if not relativePath.startswith("pensum/"):
                raise ValueError("La referencia no corresponde a un pensum.")
            if not storage.exists(relativePath):
                raise ValueError("No se encontró el archivo pensum.")
            return storage.generateReadUrl(
                relativePath, fileName=eventFound.pensumOriginalNameEvent, download=download,
            )
