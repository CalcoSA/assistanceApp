from app.application.interfaces.IOnlyOfficeApplication import IOnlyOfficeApplication
from app.application.services.OnlyOfficeApplication import OnlyOfficeApplication
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.domain.dtos.OnlyOfficeDto import OnlyOfficePreviewResponseDto
from app.infrastructure.db.connection import getDb
from app.infrastructure.logging.loggerConfig import getLogger
from app.infrastructure.repositories.EventRepository import EventRepository
from app.api.authController import getCurrentPayload
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session


router = APIRouter(prefix="/onlyoffice", tags=["onlyoffice"])
logger = getLogger(__name__)


def getOnlyOfficeApplication(
    db: Session = Depends(getDb),
) -> IOnlyOfficeApplication:
    return OnlyOfficeApplication(EventRepository(db))


def getCurrentAuthContext(payload: dict = Depends(getCurrentPayload)) -> dict:
    userLogin = (
        payload.get("wordpressUserLogin")
        or payload.get("userLogin")
        or payload.get("username")
    )

    if not userLogin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido. No contiene usuario.",
        )

    roles = payload.get("roles") if isinstance(payload.get("roles"), list) else []

    return {"userLogin": userLogin, "roles": roles}


@router.post(
    "/pensum/preview",
    response_model=apiResponseDto[OnlyOfficePreviewResponseDto],
)
def createTemporaryPensumPreview(
    file: UploadFile = File(...),
    authContext: dict = Depends(getCurrentAuthContext),
    service: IOnlyOfficeApplication = Depends(getOnlyOfficeApplication),
):
    try:
        data = service.createTemporaryPensumPreview(
            file=file,
            userLogin=authContext["userLogin"],
        )
        return apiResponseDto(
            isSuccess=True,
            Message="Vista previa de OnlyOffice generada correctamente.",
            result=data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        logger.error("Configuración de OnlyOffice incompleta | error=%s", str(error))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Error generando vista previa temporal de PENSUM")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible generar la vista previa del documento.",
        ) from error


@router.get(
    "/pensum/events/{IdEvent}",
    response_model=apiResponseDto[OnlyOfficePreviewResponseDto],
)
def getEventPensumPreview(
    IdEvent: int,
    authContext: dict = Depends(getCurrentAuthContext),
    service: IOnlyOfficeApplication = Depends(getOnlyOfficeApplication),
):
    try:
        data = service.createEventPensumPreview(
            IdEvent=IdEvent,
            userLogin=authContext["userLogin"],
            roles=authContext["roles"],
        )
        return apiResponseDto(
            isSuccess=True,
            Message="Vista previa de OnlyOffice obtenida correctamente.",
            result=data,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        logger.error("Configuración de OnlyOffice incompleta | error=%s", str(error))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Error obteniendo vista previa de PENSUM | IdEvent=%s", IdEvent)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible generar la vista previa del documento.",
        ) from error


@router.get("/files/{accessToken}", include_in_schema=False)
def getOnlyOfficeFile(
    accessToken: str,
    service: IOnlyOfficeApplication = Depends(getOnlyOfficeApplication),
):
    try:
        filePath, originalFileName, mimeType = service.resolveFileAccess(accessToken)
        return FileResponse(
            path=filePath,
            media_type=mimeType,
            filename=originalFileName,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Error entregando archivo a OnlyOffice")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible entregar el documento.",
        ) from error

