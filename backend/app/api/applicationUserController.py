from app.domain.dtos.ApplicationUserDto import ( ApplicationUserCreateDto, ApplicationUserUpdateDto, ApplicationUserResponseDto )
from app.infrastructure.repositories.ApplicationUserRepository import ApplicationUserRepository
from app.application.interfaces.IApplicationUserApplication import IApplicationUserApplication
from app.infrastructure.repositories.WordpressUserRepository import WordpressUserRepository
from app.application.services.ApplicationUserApplication import ApplicationUserApplication
from app.infrastructure.repositories.RoleRepository import RoleRepository
from app.domain.dtos.WordpressUserDto import WordpressUserResponseDto
from app.infrastructure.db.wordpressConnection import getWordpressDb
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/application-user", tags=["application-user"])
logger = getLogger(__name__)

def getApplicationUserApplication(db: Session = Depends(getDb), wpDb: Session = Depends(getWordpressDb)) -> IApplicationUserApplication:
    applicationUserRepository = ApplicationUserRepository(db)
    roleRepository = RoleRepository(db)
    wordpressUserRepository = WordpressUserRepository(wpDb)
    return ApplicationUserApplication(applicationUserRepository, roleRepository, wordpressUserRepository)

@router.get("/wordpress-users", response_model=apiResponseDto[List[WordpressUserResponseDto]])
def searchWordpressUsers(search: str = Query(...), service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Buscando usuarios WordPress | search=%s", search)
        data = service.searchWordpressUsers(search)
        logger.info("Usuarios WordPress obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Usuarios de WordPress obtenidos correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación buscando usuarios WordPress | search=%s | error=%s", search, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.exception("Error buscando usuarios WordPress | search=%s", search)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al buscar usuarios de WordPress: {str(e)}")

@router.get("/", response_model=apiResponseDto[List[ApplicationUserResponseDto]])
def getAllApplicationUsers(service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Consultando usuarios del aplicativo")
        data = service.getAll()

        if not data:
            return apiResponseDto(isSuccess=False, Message="No existen usuarios del aplicativo registrados.", result=[])
        
        logger.info("Usuarios del aplicativo obtenidos | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Usuarios del aplicativo obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error obteniendo usuarios del aplicativo")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los usuarios del aplicativo.")

@router.get("/{IdApplicationUser}", response_model=apiResponseDto[ApplicationUserResponseDto])
def getApplicationUserById(IdApplicationUser: int, service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Consultando usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        data = service.getById(IdApplicationUser)
        logger.info("Usuario del aplicativo obtenido | IdApplicationUser=%s", IdApplicationUser)
        return apiResponseDto(isSuccess=True, Message="Usuario del aplicativo obtenido correctamente.", result=data)

    except ValueError as e:
        logger.warning("Usuario del aplicativo no encontrado | IdApplicationUser=%s | error=%s", IdApplicationUser, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error obteniendo usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el usuario del aplicativo.")

@router.post("/", response_model=apiResponseDto[ApplicationUserResponseDto], status_code=status.HTTP_201_CREATED)
def createApplicationUser(applicationUserData: ApplicationUserCreateDto, service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Creando usuario del aplicativo | wordpressUserId=%s", applicationUserData.wordpressUserId)
        data = service.create(applicationUserData)
        logger.info("Usuario autorizado correctamente | IdApplicationUser=%s | wordpressUserId=%s", data.IdApplicationUser, data.wordpressUserId)
        return apiResponseDto(isSuccess=True, Message="Usuario autorizado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación creando usuario del aplicativo | wordpressUserId=%s | error=%s", applicationUserData.wordpressUserId, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error autorizando usuario del aplicativo | wordpressUserId=%s", applicationUserData.wordpressUserId)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al autorizar el usuario.")

@router.put("/{IdApplicationUser}", response_model=apiResponseDto[ApplicationUserResponseDto])
def updateApplicationUser(IdApplicationUser: int, applicationUserData: ApplicationUserUpdateDto, service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Actualizando usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        data = service.update(IdApplicationUser, applicationUserData)
        logger.info("Usuario del aplicativo actualizado correctamente | IdApplicationUser=%s", IdApplicationUser)
        return apiResponseDto(isSuccess=True, Message="Usuario del aplicativo actualizado correctamente.", result=data)

    except ValueError as e:
        message = str(e)
        statusCode = status.HTTP_404_NOT_FOUND if "no encontrado" in message.lower() else status.HTTP_400_BAD_REQUEST
        logger.warning("Validación actualizando usuario del aplicativo | IdApplicationUser=%s | status=%s | error=%s", IdApplicationUser, statusCode, message)
        raise HTTPException(status_code=statusCode, detail=message)
    
    except Exception:
        logger.exception("Error actualizando usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el usuario del aplicativo.")

@router.delete("/{IdApplicationUser}", response_model=apiResponseDto[dict])
def deleteApplicationUser(IdApplicationUser: int, service: IApplicationUserApplication = Depends(getApplicationUserApplication)):
    try:
        logger.info("Eliminando usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        service.delete(IdApplicationUser)
        logger.info("Usuario del aplicativo eliminado correctamente | IdApplicationUser=%s", IdApplicationUser)
        return apiResponseDto(isSuccess=True, Message="Usuario del aplicativo eliminado correctamente.", result={})

    except ValueError as e:
        logger.warning("Usuario del aplicativo no encontrado al eliminar | IdApplicationUser=%s | error=%s", IdApplicationUser, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error eliminando usuario del aplicativo | IdApplicationUser=%s", IdApplicationUser)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el usuario del aplicativo.")