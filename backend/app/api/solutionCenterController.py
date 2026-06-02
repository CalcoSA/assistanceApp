from app.domain.dtos.SolutionCenterDto import (SolutionCenterCreateDto, SolutionCenterUpdateDto, SolutionCenterResponseDto)
from app.infrastructure.repositories.SolutionCenterRepository import SolutionCenterRepository
from app.application.interfaces.ISolutionCenterApplication import ISolutionCenterApplication
from app.application.services.SolutionCenterApplication import SolutionCenterApplication
from app.infrastructure.logging.loggerConfig import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/solution-center", tags=["solution-center"])
logger = getLogger(__name__)

def getSolutionCenterApplication(db: Session = Depends(getDb)) -> ISolutionCenterApplication:
    solutionCenterRepository = SolutionCenterRepository(db)
    return SolutionCenterApplication(solutionCenterRepository)

@router.get("/", response_model=apiResponseDto[List[SolutionCenterResponseDto]])
def getAllSolutionCenters(service: ISolutionCenterApplication = Depends(getSolutionCenterApplication)):
    try:
        logger.info("Consultando centros de soluciones")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen centros de soluciones registrados.", result=[])

        logger.info("Centros de soluciones obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Centros de soluciones obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo centros de soluciones")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los centros de soluciones.")

@router.get("/{IdSolutionCenter}", response_model=apiResponseDto[SolutionCenterResponseDto])
def getSolutionCenterById(IdSolutionCenter: int, service: ISolutionCenterApplication = Depends(getSolutionCenterApplication)):
    try:
        logger.info("Consultando centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        data = service.getById(IdSolutionCenter)
        return apiResponseDto(isSuccess=True, Message="Centro de soluciones obtenido correctamente.", result=data)

    except ValueError as e:
        logger.warning("Centro de soluciones no encontrado | IdSolutionCenter=%s", IdSolutionCenter)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error obteniendo centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el centro de soluciones.")

@router.post("/", response_model=apiResponseDto[SolutionCenterResponseDto], status_code=status.HTTP_201_CREATED)
def createSolutionCenter(solutionCenterData: SolutionCenterCreateDto, service: ISolutionCenterApplication = Depends(getSolutionCenterApplication)):
    try:
        logger.info("Creando centro de soluciones | code=%s | name=%s", solutionCenterData.codeSolutionCenter, solutionCenterData.nameSolutionCenter)
        data = service.create(solutionCenterData)
        return apiResponseDto(isSuccess=True, Message="Centro de soluciones creado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación creando centro de soluciones | error=%s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error creando centro de soluciones")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el centro de soluciones.")

@router.put("/{IdSolutionCenter}", response_model=apiResponseDto[SolutionCenterResponseDto])
def updateSolutionCenter(IdSolutionCenter: int, solutionCenterData: SolutionCenterUpdateDto, service: ISolutionCenterApplication = Depends(getSolutionCenterApplication)):
    try:
        logger.info("Actualizando centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        data = service.update(IdSolutionCenter, solutionCenterData)
        return apiResponseDto(isSuccess=True, Message="Centro de soluciones actualizado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación actualizando centro de soluciones | IdSolutionCenter=%s | error=%s", IdSolutionCenter, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error actualizando centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el centro de soluciones.")


@router.delete("/{IdSolutionCenter}", response_model=apiResponseDto[bool])
def deleteSolutionCenter(IdSolutionCenter: int, service: ISolutionCenterApplication = Depends(getSolutionCenterApplication)):
    try:
        logger.info("Eliminando centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        data = service.delete(IdSolutionCenter)
        return apiResponseDto(isSuccess=True, Message="Centro de soluciones eliminado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación eliminando centro de soluciones | IdSolutionCenter=%s | error=%s", IdSolutionCenter, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error eliminando centro de soluciones | IdSolutionCenter=%s", IdSolutionCenter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el centro de soluciones.")