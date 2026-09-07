from app.domain.dtos.CompetencyDto import (
    CompetencyCreateDto,
    CompetencyResponseDto,
    CompetencyUpdateDto,
)
from app.infrastructure.repositories.CompetencyRepository import CompetencyRepository
from app.application.interfaces.ICompetencyApplication import ICompetencyApplication
from app.application.services.CompetencyApplication import CompetencyApplication
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.api.dependencies.AuthDependencies import requireMenuPermission
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

COMPETENCIES_MENU_PATH = "/maestros/competencias"
router = APIRouter(prefix="/competency", tags=["competency"])
logger = getLogger(__name__)

def getCompetencyApplication(db: Session = Depends(getDb)) -> ICompetencyApplication:
    competencyRepository = CompetencyRepository(db)
    return CompetencyApplication(competencyRepository)

@router.get("/", response_model=apiResponseDto[List[CompetencyResponseDto]])
def getAllCompetencies(
    service: ICompetencyApplication = Depends(getCompetencyApplication),
):
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


@router.get(
    "/{IdCompetency}",
    response_model=apiResponseDto[CompetencyResponseDto],
    dependencies=[Depends(requireMenuPermission(COMPETENCIES_MENU_PATH))],
)
def getCompetencyById(
    IdCompetency: int,
    service: ICompetencyApplication = Depends(getCompetencyApplication),
):
    try:
        logger.info("Consultando competencia | IdCompetency=%s", IdCompetency)
        data = service.getById(IdCompetency)
        return apiResponseDto(
            isSuccess=True,
            Message="Competencia obtenida correctamente.",
            result=data,
        )

    except ValueError as error:
        logger.warning(
            "Competencia no encontrada | IdCompetency=%s | error=%s",
            IdCompetency,
            str(error),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    except Exception:
        logger.exception(
            "Error obteniendo competencia | IdCompetency=%s",
            IdCompetency,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la competencia.",
        )


@router.post(
    "/",
    response_model=apiResponseDto[CompetencyResponseDto],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requireMenuPermission(COMPETENCIES_MENU_PATH))],
)
def createCompetency(
    competencyData: CompetencyCreateDto,
    service: ICompetencyApplication = Depends(getCompetencyApplication),
):
    try:
        logger.info(
            "Creando competencia | nameCompetency=%s",
            competencyData.nameCompetency,
        )
        data = service.create(competencyData)
        return apiResponseDto(
            isSuccess=True,
            Message="Competencia creada correctamente.",
            result=data,
        )

    except ValueError as error:
        logger.warning(
            "Validación creando competencia | error=%s",
            str(error),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception:
        logger.exception("Error creando competencia")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la competencia.",
        )


@router.put(
    "/{IdCompetency}",
    response_model=apiResponseDto[CompetencyResponseDto],
    dependencies=[Depends(requireMenuPermission(COMPETENCIES_MENU_PATH))],
)
def updateCompetency(
    IdCompetency: int,
    competencyData: CompetencyUpdateDto,
    service: ICompetencyApplication = Depends(getCompetencyApplication),
):
    try:
        logger.info("Actualizando competencia | IdCompetency=%s", IdCompetency)
        data = service.update(IdCompetency, competencyData)
        return apiResponseDto(
            isSuccess=True,
            Message="Competencia actualizada correctamente.",
            result=data,
        )

    except ValueError as error:
        message = str(error)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no existe" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning(
            "Validación actualizando competencia | IdCompetency=%s | error=%s",
            IdCompetency,
            message,
        )
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception(
            "Error actualizando competencia | IdCompetency=%s",
            IdCompetency,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la competencia.",
        )


@router.delete(
    "/{IdCompetency}",
    response_model=apiResponseDto[bool],
    dependencies=[Depends(requireMenuPermission(COMPETENCIES_MENU_PATH))],
)
def deleteCompetency(
    IdCompetency: int,
    service: ICompetencyApplication = Depends(getCompetencyApplication),
):
    try:
        logger.info("Eliminando competencia | IdCompetency=%s", IdCompetency)
        data = service.delete(IdCompetency)
        return apiResponseDto(
            isSuccess=True,
            Message="Competencia eliminada correctamente.",
            result=data,
        )

    except ValueError as error:
        message = str(error)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no existe" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning(
            "Validación eliminando competencia | IdCompetency=%s | error=%s",
            IdCompetency,
            message,
        )
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception(
            "Error eliminando competencia | IdCompetency=%s",
            IdCompetency,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la competencia.",
        )
