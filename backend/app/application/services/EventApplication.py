from app.domain.dtos.EventDto import (EventCreateDto, EventQrResponseDto, EventResponseDto, EventUpdateDto, EventPaginatedResponseDto)
from app.application.interfaces.IEventApplication import IEventApplication
from app.application.interfaces.IEventNotificationApplication import IEventNotificationApplication
from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.dtos.EventDto import EventAttendanceResponseDto
from app.infrastructure.db.config import APP_TIMEZONE_INFO, settings
from app.domain.entities.Event import Event
from fastapi import UploadFile
from datetime import datetime, time, timedelta
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
        facilitatorData = self._normalizeEventFacilitators(
            facilitatorName=eventData.facilitatorNameEvent,
            facilitatorType=eventData.facilitatorTypeEvent,
            facilitatorCompany=eventData.facilitatorCompanyEvent,
            facilitatorPosition=eventData.facilitatorPositionEvent,
            secondFacilitatorName=eventData.secondFacilitatorNameEvent,
            secondFacilitatorType=eventData.secondFacilitatorTypeEvent,
            secondFacilitatorCompany=eventData.secondFacilitatorCompanyEvent,
            secondFacilitatorPosition=eventData.secondFacilitatorPositionEvent,
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

        newEvent = Event(
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
        )

        updateData = eventData.model_dump(
            exclude_unset=True,
            exclude={
                "topics",
                "competencies",
                "durationEvent",
                "facilitatorTypeEvent",
                "secondFacilitatorTypeEvent",
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

        return {
            "facilitatorNameEvent": principal["name"],
            "facilitatorCompanyEvent": principal["company"],
            "facilitatorPositionEvent": principal["position"],
            "secondFacilitatorNameEvent": second["name"],
            "secondFacilitatorCompanyEvent": second["company"],
            "secondFacilitatorPositionEvent": second["position"],
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
                "facilitatorTypeEvent": self._inferFacilitatorType(
                    event.facilitatorNameEvent,
                    event.facilitatorCompanyEvent,
                ),
                "secondFacilitatorTypeEvent": self._inferFacilitatorType(
                    event.secondFacilitatorNameEvent,
                    event.secondFacilitatorCompanyEvent,
                ),
            }
        )
    
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
            ".docm",
            ".docx",
            ".odt",
            ".rtf",
            ".txt",
            ".csv",
            ".ods",
            ".xls",
            ".xlsb",
            ".xlsm",
            ".xlsx",
            ".odp",
            ".ppt",
            ".pptm",
            ".pptx",
            ".png",
            ".jpg",
            ".jpeg",
        }

        originalFileName = file.filename
        extension = os.path.splitext(originalFileName)[1].lower()

        if extension not in allowedExtensions:
            raise ValueError(
                "Tipo de archivo no permitido. Adjunte PDF, imagen o un "
                "documento compatible con OnlyOffice."
            )

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
