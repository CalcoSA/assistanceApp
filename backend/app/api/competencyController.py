from app.infrastructure.repositories.CompetencyRepository import CompetencyRepository
from app.application.interfaces.ICompetencyApplication import ICompetencyApplication
from app.application.services.CompetencyApplication import CompetencyApplication
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.domain.dtos.CompetencyDto import CompetencyDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/competency", tags=["competency"])
logger = getLogger(__name__)

def getCompetencyApplication(db: Session = Depends(getDb)) -> ICompetencyApplication:
    competencyRepository = CompetencyRepository(db)
    return CompetencyApplication(competencyRepository)

@router.get("/", response_model=apiResponseDto[List[CompetencyDto]])
def getAllCompetencys(service: ICompetencyApplication = Depends(getCompetencyApplication)):
    try:
        logger.info("Consultando competencias")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen competencias registradas.", result=[])
        
        logger.info("Competencias obtenidas | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Competencias obtenidas correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo las competencias")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las competencias.")