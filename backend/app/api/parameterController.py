from app.domain.dtos.ParameterDto import ParameterCreateDto, ParameterUpdateDto, ParameterResponseDto
from app.infrastructure.repositories.ParameterRepository import ParameterRepository
from app.application.interfaces.IParameterApplication import IParameterApplication
from app.application.services.ParameterApplication import ParameterApplication
from app.infrastructure.logging.loggerConfig import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies.AuthDependencies import requireMenuPermission
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/parameter",
    tags=["parameter"],
    dependencies=[Depends(requireMenuPermission("/maestros/parametros"))],
)
logger = getLogger(__name__)


def getParameterApplication(db: Session = Depends(getDb)) -> IParameterApplication:
    parameterRepository = ParameterRepository(db)
    return ParameterApplication(parameterRepository)


@router.get("/", response_model=apiResponseDto[List[ParameterResponseDto]])
def getAllParameters(service: IParameterApplication = Depends(getParameterApplication)):
    try:
        logger.info("Consultando parámetros")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen parámetros registrados.", result=[])

        logger.info("Parámetros obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Parámetros obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo parámetros")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los parámetros.")


@router.get("/{IdParameter}", response_model=apiResponseDto[ParameterResponseDto])
def getParameterById(IdParameter: int, service: IParameterApplication = Depends(getParameterApplication)):
    try:
        logger.info("Consultando parámetro | IdParameter=%s", IdParameter)
        data = service.getById(IdParameter)
        return apiResponseDto(isSuccess=True, Message="Parámetro obtenido correctamente.", result=data)

    except ValueError as e:
        logger.warning("Parámetro no encontrado | IdParameter=%s", IdParameter)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error obteniendo parámetro | IdParameter=%s", IdParameter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el parámetro.")


@router.post("/", response_model=apiResponseDto[ParameterResponseDto], status_code=status.HTTP_201_CREATED)
def createParameter(parameterData: ParameterCreateDto, service: IParameterApplication = Depends(getParameterApplication)):
    try:
        logger.info("Creando parámetro | nameParameter=%s", parameterData.nameParameter)
        data = service.create(parameterData)
        return apiResponseDto(isSuccess=True, Message="Parámetro creado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación creando parámetro | error=%s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error creando parámetro")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el parámetro.")


@router.put("/{IdParameter}", response_model=apiResponseDto[ParameterResponseDto])
def updateParameter(IdParameter: int, parameterData: ParameterUpdateDto, service: IParameterApplication = Depends(getParameterApplication)):
    try:
        logger.info("Actualizando parámetro | IdParameter=%s", IdParameter)
        data = service.update(IdParameter, parameterData)
        return apiResponseDto(isSuccess=True, Message="Parámetro actualizado correctamente.", result=data)

    except ValueError as e:
        message = str(e)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no existe" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning("Validación actualizando parámetro | IdParameter=%s | error=%s", IdParameter, message)
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception("Error actualizando parámetro | IdParameter=%s", IdParameter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el parámetro.")


@router.delete("/{IdParameter}", response_model=apiResponseDto[bool])
def deleteParameter(IdParameter: int, service: IParameterApplication = Depends(getParameterApplication)):
    try:
        logger.info("Eliminando parámetro | IdParameter=%s", IdParameter)
        data = service.delete(IdParameter)
        return apiResponseDto(isSuccess=True, Message="Parámetro eliminado correctamente.", result=data)

    except ValueError as e:
        message = str(e)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no existe" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning("Validación eliminando parámetro | IdParameter=%s | error=%s", IdParameter, message)
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception("Error eliminando parámetro | IdParameter=%s", IdParameter)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el parámetro.")
