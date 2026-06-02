from app.infrastructure.repositories.EventCategoryRepository import EventCategoryRepository
from app.application.interfaces.IEventCategoryApplication import IEventCategoryApplication
from app.application.services.EventCategoryApplication import EventCategoryApplication
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.EventCategoryDto import EventCategoryDto
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/event-category", tags=["event-category"])
logger = getLogger(__name__)

def getEventCategoryApplication(db: Session = Depends(getDb)) -> IEventCategoryApplication:
    eventCategoryRepository = EventCategoryRepository(db)
    return EventCategoryApplication(eventCategoryRepository)

@router.get("/", response_model=apiResponseDto[List[EventCategoryDto]])
def getAllCompetencys(service: IEventCategoryApplication = Depends(getEventCategoryApplication)):
    try:
        logger.info("Consultando categorias")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen categorias registradas.", result=[])
        
        logger.info("Categorias obtenidas | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Categorias obtenidas correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo las categorias")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las categorias.")