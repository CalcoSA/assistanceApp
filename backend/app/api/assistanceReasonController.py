from app.infrastructure.repositories.AssistanceReasonRepository import AssistanceReasonRepository
from app.application.interfaces.IAssistanceReasonApplication import IAssistanceReasonApplication
from app.application.services.AssistanceReasonApplication import AssistanceReasonApplication
from app.domain.dtos.AssistanceReasonDto import AssistanceReasonDto
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/assistance-reason", tags=["assistance-reason"])
logger = getLogger(__name__)

def getAssistanceReasonApplication(db: Session = Depends(getDb)) -> IAssistanceReasonApplication:
    assistanceReasonRepository = AssistanceReasonRepository(db)
    return AssistanceReasonApplication(assistanceReasonRepository)

@router.get("/", response_model=apiResponseDto[List[AssistanceReasonDto]])
def getAllAssistanceReasons(service: IAssistanceReasonApplication = Depends(getAssistanceReasonApplication)):
    try:
        logger.info("Consultando motivos de asistencia")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen motivos de asistencia registrados.", result=[])
        
        logger.info("Motivos de asistencia obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Motivos de asistencia obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo motivos de asistencias")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los motivos de asistencia.")