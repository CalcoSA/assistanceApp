from app.domain.dtos.EventDto import (EventCreateDto, EventUpdateDto, EventResponseDto, EventQrResponseDto, EventAttendanceResponseDto, EventPaginatedResponseDto)
from app.infrastructure.repositories.EventRepository import EventRepository
from app.infrastructure.repositories.ParameterRepository import ParameterRepository
from app.infrastructure.repositories.WordpressUserRepository import WordpressUserRepository
from app.application.interfaces.IEventApplication import IEventApplication
from app.application.services.EventApplication import EventApplication
from app.application.services.EventNotificationApplication import EventNotificationApplication
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.infrastructure.db.wordpressConnection import getWordpressDb
from app.application.services.JwtService import JwtService
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from fastapi.responses import FileResponse
from fastapi import UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

router = APIRouter(prefix="/events", tags=["events"])
security = HTTPBearer()
logger = getLogger(__name__)

def getEventApplication(
    db: Session = Depends(getDb),
    wpDb: Session = Depends(getWordpressDb),
) -> IEventApplication:
    eventRepository = EventRepository(db)
    parameterRepository = ParameterRepository(db)
    wordpressUserRepository = WordpressUserRepository(wpDb)
    eventNotificationApplication = EventNotificationApplication(
        parameterRepository,
        wordpressUserRepository,
    )
    return EventApplication(eventRepository, eventNotificationApplication)

def getCurrentAuthContext(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = JwtService.decodeToken(credentials.credentials)
    userLogin = (payload.get("wordpressUserLogin") or payload.get("userLogin") or payload.get("username"))

    if not userLogin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido. No contiene usuario.")

    roles = []

    if isinstance(payload.get("roles"), list):
        roles = payload.get("roles")

    return { "userLogin": userLogin, "roles": roles }

@router.get("/{IdEvent}", response_model=apiResponseDto[EventResponseDto])
def getEventById(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Consultando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.getByIdByUserScope(IdEvent, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Evento obtenido correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado consultando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Evento no encontrado | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error obteniendo evento | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el evento.")
    
@router.get("/{IdEvent}/attendances", response_model=apiResponseDto[List[EventAttendanceResponseDto]])
def getEventAttendances(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Consultando asistentes del evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.getAttendancesByEventScope(IdEvent, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Asistentes del evento obtenidos correctamente.", result=data)

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error consultando asistentes del evento | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al consultar los asistentes del evento.")
    
@router.get("/", response_model=apiResponseDto[EventPaginatedResponseDto])
def getEvents(page: int = Query(1, ge=1), pageSize: int = Query(10, ge=1, le=100), statusFilter: Optional[str] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication),):
    try:
        logger.info("Consultando eventos paginados | userLogin=%s | roles=%s | page=%s | pageSize=%s | statusFilter=%s", authContext["userLogin"], authContext["roles"], page, pageSize, statusFilter,)
        data = service.getPaginatedByUserScope(page=page, pageSize=pageSize, status=statusFilter, userLogin=authContext["userLogin"], roles=authContext["roles"],)
        return apiResponseDto(isSuccess=True, Message="Eventos obtenidos correctamente.", result=data,)

    except Exception:
        logger.exception("Error obteniendo eventos paginados")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los eventos.")

@router.post("/", response_model=apiResponseDto[EventResponseDto], status_code=status.HTTP_201_CREATED)
def createEvent(eventData: EventCreateDto, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Creando evento | title=%s | userLogin=%s", eventData.titleEvent, authContext["userLogin"])
        data = service.create(eventData, authContext["userLogin"], authContext["roles"])
        message = data.notificationMessage or "Evento creado correctamente."
        return apiResponseDto(isSuccess=True, Message=message, result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado creando evento | userLogin=%s | error=%s", authContext["userLogin"], str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación creando evento | userLogin=%s | error=%s", authContext["userLogin"], str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error creando evento")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el evento.")

@router.put("/{IdEvent}", response_model=apiResponseDto[EventResponseDto])
def updateEvent(IdEvent: int, eventData: EventUpdateDto, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Actualizando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.update(IdEvent, eventData, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Evento actualizado correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado actualizando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación actualizando evento | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error actualizando evento | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el evento.")

@router.patch("/{IdEvent}/cancel", response_model=apiResponseDto[EventResponseDto])
def cancelEvent(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Cancelando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.cancel(IdEvent, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Evento cancelado correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado cancelando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación cancelando evento | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error cancelando evento | IdEvent=%s", IdEvent)

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al cancelar el evento.")

@router.delete("/{IdEvent}", response_model=apiResponseDto[bool])
def deleteEvent(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Eliminando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.delete(IdEvent, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Evento eliminado correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado eliminando evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación eliminando evento | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error eliminando evento | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el evento.")

@router.get("/{IdEvent}/qr", response_model=apiResponseDto[EventQrResponseDto])
def getEventQr(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Consultando QR del evento | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        data = service.getQrInfo(IdEvent, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="QR obtenido correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado consultando QR | IdEvent=%s | userLogin=%s", IdEvent, authContext["userLogin"])
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación consultando QR | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error consultando QR | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el QR del evento.")
    
@router.post("/{IdEvent}/pensum", response_model=apiResponseDto[EventResponseDto])
def uploadEventPensum(IdEvent: int, file: UploadFile = File(...), authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        logger.info("Actualizando pensum del evento | IdEvent=%s | file=%s | userLogin=%s", IdEvent, file.filename, authContext["userLogin"])
        data = service.uploadPensum(IdEvent, file, authContext["userLogin"], authContext["roles"])
        return apiResponseDto(isSuccess=True, Message="Pensum del evento actualizado correctamente.", result=data)

    except PermissionError as e:
        logger.warning("Permiso denegado actualizando pensum | IdEvent=%s | userLogin=%s | error=%s", IdEvent, authContext["userLogin"], str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        logger.warning("Validación actualizando pensum | IdEvent=%s | error=%s", IdEvent, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error actualizando pensum | IdEvent=%s", IdEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el pensum del evento.")
    
@router.get("/{IdEvent}/qr/download")
def downloadEventQr(IdEvent: int, authContext: dict = Depends(getCurrentAuthContext), service: IEventApplication = Depends(getEventApplication)):
    try:
        qrInfo = service.getQrInfo(IdEvent, authContext["userLogin"], authContext["roles"])

        if not qrInfo.qrPathEvent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El evento no tiene imagen QR generada.")

        backendDir = Path(__file__).resolve().parents[2]
        relativePath = qrInfo.qrPathEvent.lstrip("/")

        filePath = backendDir / relativePath

        if not filePath.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la imagen QR en el servidor.")

        return FileResponse(path=str(filePath), media_type="image/png", filename=f"qr_evento_{IdEvent}.png")

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
