from app.domain.dtos.MenuOptionDto import ( MenuOptionCreateDto, MenuOptionUpdateDto, MenuOptionResponseDto )
from app.infrastructure.repositories.MenuOptionRepository import MenuOptionRepository
from app.application.interfaces.IMenuOptionApplication import IMenuOptionApplication
from app.application.services.MenuOptionApplication import MenuOptionApplication
from app.infrastructure.logging.loggerConfig import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/menu-option", tags=["menu-option"])
logger = getLogger(__name__)

def getMenuOptionApplication(db: Session = Depends(getDb)) -> IMenuOptionApplication:
    repository = MenuOptionRepository(db)
    return MenuOptionApplication(repository)

@router.get("/", response_model=apiResponseDto[List[MenuOptionResponseDto]])
def getAllMenuOptions(service: IMenuOptionApplication = Depends(getMenuOptionApplication)):
    try:
        logger.info("Consultando opciones de menú")
        data = service.getAll()
        logger.info("Opciones de menú obtenidas correctamente | total=%s", len(data) if data else 0)
        return apiResponseDto(isSuccess=True, Message="Opciones de menú obtenidas correctamente.", result=data)

    except Exception:
        logger.exception("Error inesperado obteniendo opciones de menú.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las opciones de menú.")

@router.get("/{IdMenuOption}", response_model=apiResponseDto[MenuOptionResponseDto])
def getMenuOptionById(IdMenuOption: int, service: IMenuOptionApplication = Depends(getMenuOptionApplication)):
    try:
        logger.info("Consultando opción de menú | IdMenuOption=%s", IdMenuOption)
        data = service.getById(IdMenuOption)
        logger.info("Opción de menú obtenida correctamente | IdMenuOption=%s", IdMenuOption)
        return apiResponseDto(isSuccess=True, Message="Opción de menú obtenida correctamente.", result=data)

    except ValueError as e:
        logger.warning("Opción de menú no encontrada | IdMenuOption=%s | error=%s", IdMenuOption, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error inesperado obteniendo opción de menú | IdMenuOption=%s", IdMenuOption)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la opción de menú.")

@router.post("/", response_model=apiResponseDto[MenuOptionResponseDto], status_code=status.HTTP_201_CREATED)
def createMenuOption(menuOptionData: MenuOptionCreateDto, service: IMenuOptionApplication = Depends(getMenuOptionApplication)):
    try:
        logger.info("Creando opción de menú | nameMenuOption=%s | pathMenuOption=%s", getattr(menuOptionData, "nameMenuOption", None), getattr(menuOptionData, "pathMenuOption", None))
        data = service.create(menuOptionData)
        logger.info("Opción de menú creada correctamente | IdMenuOption=%s | nameMenuOption=%s", getattr(data, "IdMenuOption", None), getattr(data, "nameMenuOption", None))
        return apiResponseDto(isSuccess=True, Message="Opción de menú creada correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación creando opción de menú | nameMenuOption=%s | error=%s", getattr(menuOptionData, "nameMenuOption", None), str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error inesperado creando opción de menú | nameMenuOption=%s | pathMenuOption=%s", getattr(menuOptionData, "nameMenuOption", None), getattr(menuOptionData, "pathMenuOption", None))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear la opción de menú.")

@router.put("/{IdMenuOption}", response_model=apiResponseDto[MenuOptionResponseDto])
def updateMenuOption(IdMenuOption: int, menuOptionData: MenuOptionUpdateDto, service: IMenuOptionApplication = Depends(getMenuOptionApplication)):
    try:
        logger.info("Actualizando opción de menú | IdMenuOption=%s | nameMenuOption=%s | pathMenuOption=%s", IdMenuOption, getattr(menuOptionData, "nameMenuOption", None), getattr(menuOptionData, "pathMenuOption", None))
        data = service.update(IdMenuOption, menuOptionData)
        logger.info("Opción de menú actualizada correctamente | IdMenuOption=%s", IdMenuOption)
        return apiResponseDto(isSuccess=True, Message="Opción de menú actualizada correctamente.", result=data)

    except ValueError as e:
        message = str(e)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no encontrada" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning("Validación actualizando opción de menú | IdMenuOption=%s | status=%s | error=%s", IdMenuOption, statusCode, message)
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception("Error inesperado actualizando opción de menú | IdMenuOption=%s", IdMenuOption)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar la opción de menú.")

@router.delete("/{IdMenuOption}", response_model=apiResponseDto[dict])
def deleteMenuOption(IdMenuOption: int, service: IMenuOptionApplication = Depends(getMenuOptionApplication)):
    try:
        logger.info("Eliminando opción de menú | IdMenuOption=%s", IdMenuOption)
        service.delete(IdMenuOption)
        logger.info("Opción de menú eliminada correctamente | IdMenuOption=%s", IdMenuOption)
        return apiResponseDto(isSuccess=True, Message="Opción de menú eliminada correctamente.", result={})

    except ValueError as e:
        logger.warning("Opción de menú no encontrada al eliminar | IdMenuOption=%s | error=%s", IdMenuOption, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error inesperado eliminando opción de menú | IdMenuOption=%s", IdMenuOption)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar la opción de menú.")