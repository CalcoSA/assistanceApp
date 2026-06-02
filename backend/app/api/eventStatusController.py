from app.infrastructure.repositories.EventStatusRepository import EventStatusRepository
from app.application.interfaces.IEventStatusApplication import IEventStatusApplication
from app.application.services.EventStatusApplication import EventStatusApplication
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.domain.dtos.EventStatusDto import EventStatusDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/event-status", tags=["event-status"])
logger = getLogger(__name__)

def getEventStatusApplication(db: Session = Depends(getDb)) -> IEventStatusApplication:
    eventStatusRepository = EventStatusRepository(db)
    return EventStatusApplication(eventStatusRepository)

@router.get("/", response_model=apiResponseDto[List[EventStatusDto]])
def getAllEventStatus(service: IEventStatusApplication = Depends(getEventStatusApplication)):
    try:
        logger.info("Consultando estados de evento")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen estados de evento registrados.", result=[])
        
        logger.info("Estados de evento obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Estados de evento obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo los estados de evento")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los estados de evento.")