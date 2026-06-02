from app.infrastructure.repositories.SpecificTrainingProgramRepository import SpecificTrainingProgramRepository
from app.application.interfaces.ISpecificTrainingProgramApplication import ISpecificTrainingProgramApplication
from app.application.services.SpecificTrainingProgramApplication import SpecificTrainingProgramApplication
from app.domain.dtos.SpecificTrainingProgramDto import SpecificTrainingProgramDto
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/specific-training-program", tags=["specific-training-program"])
logger = getLogger(__name__)

def getSpecificTrainingProgramApplication(db: Session = Depends(getDb)) -> ISpecificTrainingProgramApplication:
    specificTrainingProgramRepository = SpecificTrainingProgramRepository(db)
    return SpecificTrainingProgramApplication(specificTrainingProgramRepository)

@router.get("/", response_model=apiResponseDto[List[SpecificTrainingProgramDto]])
def getAllSpecificTrainingPrograms(service: ISpecificTrainingProgramApplication = Depends(getSpecificTrainingProgramApplication)):
    try:
        logger.info("Consultando tipos de programa de formación")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen tipos de programa de formación registrados.", result=[])
        
        logger.info("Tipos de programa de formación obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Tipos de programa de formación obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo tipos de programa de formación")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los tipos de programa de formación.")