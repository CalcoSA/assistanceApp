from app.domain.dtos.EventDto import (EventCreateDto, EventQrResponseDto, EventResponseDto, EventUpdateDto, EventPaginatedResponseDto)
from app.application.interfaces.IEventApplication import IEventApplication
from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.dtos.EventDto import EventAttendanceResponseDto
from app.infrastructure.db.config import settings
from app.domain.entities.Event import Event
from fastapi import UploadFile
from datetime import datetime
import qrcode
import uuid
import os

class EventApplication(IEventApplication):

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_CANCELLED = 3
    STATUS_ACTIVE_NAME = "activo"
    STATUS_INACTIVE_NAME = "inactivo"
    STATUS_CANCELLED_NAME = "cancelado"
    VIEW_ALL_ROLES = ["administrador"]
    CREATE_EVENT_ROLES = ["administrador", "formador"]

    def __init__(self, eventRepository: IEventRepository):
        self.eventRepository = eventRepository

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

        return [
            EventAttendanceResponseDto.model_validate(attendance)
            for attendance in attendances
        ]
    
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

        createdAt = datetime.now()
        attendanceStartDateTime = createdAt
        attendanceEndDateTime = datetime.combine(eventData.dateEvent, eventData.endTimeEvent)

        if attendanceEndDateTime <= createdAt:
            raise ValueError("La fecha y hora final del evento debe ser mayor a la fecha y hora actual.")

        tokenEvent = uuid.uuid4().hex
        publicUrlEvent = f"{self.publicAttendanceBaseUrl}/{tokenEvent}"
        qrPathEvent = self._generateQr(tokenEvent, publicUrlEvent)

        newEvent = Event(
            titleEvent=eventData.titleEvent.strip(),
            descriptionEvent=eventData.descriptionEvent,
            dateEvent=eventData.dateEvent,
            durationEvent=eventData.durationEvent,
            startTimeEvent=eventData.startTimeEvent,
            endTimeEvent=eventData.endTimeEvent,
            IdSolutionCenter=eventData.IdSolutionCenter,
            IdAssistanceReason=eventData.IdAssistanceReason,
            IdSpecificTrainingProgram=eventData.IdSpecificTrainingProgram,
            IdEventCategory=eventData.IdEventCategory,
            IdEventStatus=self.STATUS_ACTIVE,
            facilitatorNameEvent=eventData.facilitatorNameEvent,
            facilitatorCompanyEvent=eventData.facilitatorCompanyEvent,
            facilitatorPositionEvent=eventData.facilitatorPositionEvent,
            secondFacilitatorNameEvent=eventData.secondFacilitatorNameEvent,
            secondFacilitatorCompanyEvent=eventData.secondFacilitatorCompanyEvent,
            secondFacilitatorPositionEvent=eventData.secondFacilitatorPositionEvent,
            scheduledPeopleNumber=eventData.scheduledPeopleNumber,
            attendedPeopleNumber=None,
            observationsEvent=eventData.observationsEvent,
            eventPlace=eventData.eventPlace,
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

        eventCreated = self.eventRepository.create(newEvent, eventData.topics, eventData.competencies)

        return self._buildResponse(eventCreated)

    def update(self, IdEvent: int, eventData: EventUpdateDto, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para actualizar este evento.")

        if eventFound.IdEventStatus == self.STATUS_CANCELLED:
            raise ValueError("No se puede actualizar un evento cancelado.")

        if self._eventHasStarted(eventFound):
            self._validateUpdateAfterEventStarted(eventData)
        else:
            self._validateUpdateBeforeEventStarted(eventData, eventFound)

        updateData = eventData.model_dump(exclude_unset=True, exclude={"topics", "competencies"})

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

        if eventData.dateEvent is not None or eventData.endTimeEvent is not None:
            updateData["attendanceEndDateTime"] = datetime.combine(finalDateEvent, finalEndTimeEvent)

        updateData["updatedByUserLogin"] = userLogin
        updateData["updatedAt"] = datetime.now()

        eventUpdated = self.eventRepository.update(IdEvent, updateData, eventData.topics, eventData.competencies)

        if not eventUpdated:
            raise ValueError("El evento no existe.")

        return self._buildResponse(eventUpdated)

    def cancel(self, IdEvent: int, userLogin: str, roles: list[str]):
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

        eventCancelled = self.eventRepository.cancel(IdEvent)

        if not eventCancelled:
            raise ValueError("El evento no existe.")

        return self._buildResponse(eventCancelled)

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

        return EventQrResponseDto(IdEvent=eventFound.IdEvent, tokenEvent=eventFound.tokenEvent, publicUrlEvent=eventFound.publicUrlEvent, qrPathEvent=eventFound.qrPathEvent)

    def _validateCreateData(self, eventData: EventCreateDto) -> None:
        if not eventData.titleEvent.strip():
            raise ValueError("El título del evento es obligatorio.")

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

        if finalEndDateTime <= datetime.now():
            raise ValueError("La fecha y hora final del evento debe ser mayor a la fecha y hora actual.")

    def _validateUpdateAfterEventStarted(self, eventData: EventUpdateDto) -> None:
        if eventData.dateEvent is not None:
            raise ValueError("No se puede reagendar un evento que ya inició.")

        if eventData.startTimeEvent is not None:
            raise ValueError("No se puede cambiar la hora de inicio de un evento que ya inició.")

        if eventData.endTimeEvent is not None:
            raise ValueError("No se puede cambiar la hora final de un evento que ya inició.")

    def _eventHasStarted(self, event: Event) -> bool:
        eventStartDateTime = datetime.combine(event.dateEvent, event.startTimeEvent)
        return datetime.now() >= eventStartDateTime

    def _syncStatusByEndDateTime(self, event: Event) -> Event:
        if (event.IdEventStatus == self.STATUS_ACTIVE and datetime.now() > event.attendanceEndDateTime):
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
        return EventResponseDto.model_validate(event)
    
    def uploadPensum(self, IdEvent: int, file: UploadFile, userLogin: str, roles: list[str]):
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        eventFound = self._syncStatusByEndDateTime(eventFound)

        if not self._userCanAccessEvent(eventFound, userLogin, roles):
            raise PermissionError("No tiene permisos para actualizar el pensum de este evento.")

        if self._eventHasStatus(eventFound, self.STATUS_CANCELLED_NAME):
            raise ValueError("No se puede actualizar el pensum de un evento cancelado.")

        if not file or not file.filename:
            raise ValueError("Debe adjuntar un archivo de pensum.")

        allowedExtensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".png",
            ".jpg",
            ".jpeg",
        }

        originalFileName = file.filename
        extension = os.path.splitext(originalFileName)[1].lower()

        if extension not in allowedExtensions:
            raise ValueError("Tipo de archivo no permitido. Adjunte PDF, Word, Excel o imagen.")

        pensumDirectory = os.path.join(self.uploadDir, "pensum", str(IdEvent))
        os.makedirs(pensumDirectory, exist_ok=True)

        if eventFound.pensumPathEvent:
            oldFilePath = eventFound.pensumPathEvent.lstrip("/").replace("/", os.sep)

            if os.path.exists(oldFilePath):
                os.remove(oldFilePath)

        fileName = f"pensum_event_{IdEvent}_{uuid.uuid4().hex}{extension}"
        filePath = os.path.join(pensumDirectory, fileName)

        fileContent = file.file.read()

        with open(filePath, "wb") as outputFile:
            outputFile.write(fileContent)

        relativePath = f"/uploads/pensum/{IdEvent}/{fileName}"

        eventUpdated = self.eventRepository.updatePensum(
            IdEvent=IdEvent,
            pensumOriginalNameEvent=originalFileName,
            pensumPathEvent=relativePath,
            pensumMimeTypeEvent=file.content_type or "application/octet-stream",
            pensumSizeEvent=len(fileContent),
            updatedByUserLogin=userLogin
        )

        if not eventUpdated:
            raise ValueError("El evento no existe.")

        return self._buildResponse(eventUpdated)