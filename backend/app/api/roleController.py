from app.domain.dtos.RoleDto import ( RoleCreateDto, RoleUpdateDto, RoleResponseDto, RoleDetailResponseDto, AssignMenuOptionsToRoleDto )
from app.infrastructure.repositories.MenuOptionRepository import MenuOptionRepository
from app.infrastructure.repositories.RoleRepository import RoleRepository
from app.application.interfaces.IRoleApplication import IRoleApplication
from app.application.services.RoleApplication import RoleApplication
from app.domain.dtos.MenuOptionDto import MenuOptionResponseDto
from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/role", tags=["role"])
logger = getLogger(__name__)

def getRoleApplication(db: Session = Depends(getDb)) -> IRoleApplication:
    roleRepository = RoleRepository(db)
    menuOptionRepository = MenuOptionRepository(db)
    return RoleApplication(roleRepository, menuOptionRepository)

@router.get("/", response_model=apiResponseDto[List[RoleResponseDto]])
def getAllRoles(service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Consultando roles")
        data = service.getAll()

        if not data:
            logger.info("No existen roles registrados.")
            return apiResponseDto(isSuccess=False, Message="No existen roles registrados.", result=[])
        
        logger.info("Roles obtenidos correctamente | total=%s", len(data))
        return apiResponseDto(isSuccess=True, Message="Roles obtenidos correctamente.", result=data)

    except Exception:
        logger.exception("Error inesperado obteniendo roles.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener los roles.")

@router.get("/{IdRole}", response_model=apiResponseDto[RoleDetailResponseDto])
def getRoleById(IdRole: int, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Consultando rol | IdRole=%s", IdRole)
        role = service.getById(IdRole)
        menuOptions = service.getMenuOptionsByRole(IdRole)
        logger.info("Rol obtenido correctamente | IdRole=%s | totalMenuOptions=%s", IdRole, len(menuOptions))
        return apiResponseDto(
            isSuccess=True,
            Message="Rol obtenido correctamente.",
            result=RoleDetailResponseDto(
                IdRole=role.IdRole,
                nameRole=role.nameRole,
                statusRole=role.statusRole,
                menuOptions=menuOptions
            )
        )

    except ValueError as e:
        logger.warning("Rol no encontrado | IdRole=%s | error=%s", IdRole, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error inesperado obteniendo rol | IdRole=%s", IdRole)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el rol.")

@router.post("/", response_model=apiResponseDto[RoleResponseDto], status_code=status.HTTP_201_CREATED)
def createRole(roleData: RoleCreateDto, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Creando rol | nameRole=%s", getattr(roleData, "nameRole", None))
        data = service.create(roleData)
        logger.info("Rol creado correctamente | IdRole=%s | nameRole=%s", getattr(data, "IdRole", None), getattr(data, "nameRole", None))
        return apiResponseDto(isSuccess=True, Message="Rol creado correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación creando rol | nameRole=%s | error=%s", getattr(roleData, "nameRole", None), str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error inesperado creando rol | nameRole=%s", getattr(roleData, "nameRole", None))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el rol.")

@router.put("/{IdRole}", response_model=apiResponseDto[RoleResponseDto])
def updateRole(IdRole: int, roleData: RoleUpdateDto, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Actualizando rol | IdRole=%s | nameRole=%s", IdRole, getattr(roleData, "nameRole", None))
        data = service.update(IdRole, roleData)
        logger.info("Rol actualizado correctamente | IdRole=%s", IdRole)        
        return apiResponseDto(isSuccess=True, Message="Rol actualizado correctamente.", result=data)

    except ValueError as e:
        message = str(e)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no encontrado" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning("Validación actualizando rol | IdRole=%s | status=%s | error=%s", IdRole, statusCode, message)
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception("Error inesperado actualizando rol | IdRole=%s", IdRole)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el rol.")

@router.delete("/{IdRole}", response_model=apiResponseDto[dict])
def deleteRole(IdRole: int, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Eliminando rol | IdRole=%s", IdRole)
        service.delete(IdRole)
        logger.info("Rol eliminado correctamente | IdRole=%s", IdRole)
        return apiResponseDto(isSuccess=True, Message="Rol eliminado correctamente.", result={})

    except ValueError as e:
        logger.warning("Rol no encontrado al eliminar | IdRole=%s | error=%s", IdRole, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error inesperado eliminando rol | IdRole=%s", IdRole)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el rol.")

@router.get("/{IdRole}/menu-options", response_model=apiResponseDto[List[MenuOptionResponseDto]])
def getMenuOptionsByRole(IdRole: int, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Consultando opciones de menú del rol | IdRole=%s", IdRole)
        data = service.getMenuOptionsByRole(IdRole)
        logger.info("Opciones de menú del rol obtenidas correctamente | IdRole=%s | total=%s", IdRole, len(data))
        return apiResponseDto(isSuccess=True, Message="Opciones de menú del rol obtenidas correctamente.", result=data)

    except ValueError as e:
        logger.warning("Rol no encontrado al consultar opciones de menú | IdRole=%s | error=%s", IdRole, str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception:
        logger.exception("Error inesperado obteniendo opciones de menú del rol | IdRole=%s", IdRole)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener las opciones de menú del rol.")

@router.put("/{IdRole}/menu-options", response_model=apiResponseDto[List[MenuOptionResponseDto]])
def setMenuOptionsToRole(IdRole: int, data: AssignMenuOptionsToRoleDto, service: IRoleApplication = Depends(getRoleApplication)):
    try:
        logger.info("Asignando opciones de menú al rol | IdRole=%s | totalMenuOptions=%s", IdRole, len(data.menuOptionIds))
        result = service.setMenuOptionsToRole(IdRole, data.menuOptionIds)
        logger.info("Opciones de menú asignadas correctamente al rol | IdRole=%s | total=%s", IdRole, len(result))
        return apiResponseDto(isSuccess=True, Message="Opciones de menú asignadas correctamente al rol.", result=result)

    except ValueError as e:
        message = str(e)
        statusCode = (
            status.HTTP_404_NOT_FOUND
            if "no encontrado" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        logger.warning("Validación asignando opciones de menú al rol | IdRole=%s | status=%s | error=%s", IdRole, statusCode, message)
        raise HTTPException(status_code=statusCode, detail=message)

    except Exception:
        logger.exception("Error inesperado asignando opciones de menú al rol | IdRole=%s", IdRole)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al asignar opciones de menú al rol.")