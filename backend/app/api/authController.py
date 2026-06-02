from app.infrastructure.repositories.ApplicationUserRepository import ApplicationUserRepository
from app.infrastructure.repositories.WordpressUserRepository import WordpressUserRepository
from app.application.services.WordpressPasswordVerifier import WordpressPasswordVerifier
from app.infrastructure.repositories.RoleRepository import RoleRepository
from app.application.interfaces.IAuthApplication import IAuthApplication
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.application.services.AuthApplication import AuthApplication
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.infrastructure.db.wordpressConnection import getWordpressDb
from app.domain.dtos.AuthDto import LoginDto, AuthResponseDto
from app.application.services.JwtService import JwtService
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
import logging
import jwt
import os

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "production")

def getAuthApplication(db: Session = Depends(getDb), wpDb: Session = Depends(getWordpressDb)) -> IAuthApplication:
    applicationUserRepository = ApplicationUserRepository(db)
    wordpressUserRepository = WordpressUserRepository(wpDb)
    wordpressPasswordVerifier = WordpressPasswordVerifier()
    roleRepository = RoleRepository(db)

    return AuthApplication(
        applicationUserRepository,
        wordpressUserRepository,
        wordpressPasswordVerifier,
        roleRepository
    )

def getSafeLoginUser(loginData: LoginDto) -> str:
    return (
        getattr(loginData, "userLogin", None)
        or getattr(loginData, "username", None)
        or getattr(loginData, "user", None)
        or "N/A"
    )

def getCurrentPayload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        return JwtService.decodeToken(credentials.credentials)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión expiró.")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

@router.post("/login", response_model=apiResponseDto[AuthResponseDto])
def login(loginData: LoginDto, service: IAuthApplication = Depends(getAuthApplication)):
    try:
        logger.info("Intentando inicio de sesión | user=%s", getSafeLoginUser(loginData))
        data = service.login(loginData)
        logger.info("Inicio de sesión correcto | user=%s", getSafeLoginUser(loginData))
        return apiResponseDto(isSuccess=True, Message="Inicio de sesión correcto.", result=data)

    except ValueError as e:
        logger.warning("Credenciales inválidas | user=%s | error=%s", getSafeLoginUser(loginData), str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    except PermissionError as e:
        logger.warning("Usuario sin permisos de acceso | user=%s | error=%s", getSafeLoginUser(loginData), str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception as e:
        safeUser = getSafeLoginUser(loginData)
        logger.exception("Error inesperado al iniciar sesión. Usuario=%s", safeUser)
        detail = "Error al iniciar sesión."

        if APP_ENV in ["development", "qa", "local"]:
            detail = f"Error al iniciar sesión: {str(e)}"

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

@router.get("/intranet-access", response_model=apiResponseDto[AuthResponseDto])
def intranetAccess(userLogin: str = Query(...), ts: int = Query(...), sig: str = Query(...), service: IAuthApplication = Depends(getAuthApplication)):
    try:
        logger.info("Validando acceso desde intranet | userLogin=%s", userLogin)
        data = service.intranetAccess(userLogin, ts, sig)
        logger.info("Acceso desde intranet correcto | userLogin=%s", userLogin)
        return apiResponseDto(isSuccess=True, Message="Acceso desde intranet correcto.", result=data)

    except PermissionError as e:
        logger.warning("Acceso desde intranet denegado | userLogin=%s | error=%s", userLogin, str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception as e:
        logger.exception("Error inesperado al validar acceso desde intranet. Usuario=%s", userLogin)
        detail = "Error al validar el acceso desde intranet."

        if APP_ENV in ["development", "qa", "local"]:
            detail = f"Error al validar el acceso desde intranet: {str(e)}"

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

@router.get("/me", response_model=apiResponseDto[AuthResponseDto])
def me(payload: dict = Depends(getCurrentPayload), service: IAuthApplication = Depends(getAuthApplication)):
    try:
        wordpressUserId = payload.get("wordpressUserId")

        if wordpressUserId is None:
            raise PermissionError("Token inválido. No contiene usuario de WordPress.")

        logger.info("Consultando usuario autenticado | wordpressUserId=%s", wordpressUserId)
        data = service.getCurrentUser(wordpressUserId)
        return apiResponseDto(isSuccess=True, Message="Usuario autenticado obtenido correctamente.", result=data)

    except PermissionError as e:
        logger.warning("No se pudo obtener usuario autenticado | error=%s", str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception:
        logger.exception("Error al obtener el usuario autenticado")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el usuario autenticado.")