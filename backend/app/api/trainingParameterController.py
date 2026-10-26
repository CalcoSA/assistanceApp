import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import WithJsonSchema
from sqlalchemy.orm import Session

from app.api.authController import getCurrentPayload
from app.api.dependencies.AuthDependencies import requireAdministrator
from app.application.interfaces.ITrainingParameterApplication import ITrainingParameterApplication
from app.application.services.TrainingParameterApplication import TrainingParameterApplication
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.domain.dtos.PensumHistoryDto import TrainingParameterVersionResponseDto
from app.domain.dtos.TrainingParameterDto import (
    TrainingParameterCompleteCreateDto, TrainingParameterCreateDto, TrainingParameterResponseDto,
    TrainingParameterStatusDto, TrainingParameterUpdateDto,
)
from app.infrastructure.db.connection import getDb
from app.infrastructure.repositories.TrainingParameterRepository import TrainingParameterRepository
from app.infrastructure.storage.GcsStorage import GcsStorageError

router = APIRouter(
    prefix="/training-parameters", tags=["training-parameters"],
    dependencies=[Depends(getCurrentPayload)],
)
logger = logging.getLogger(__name__)
adminOnly = [Depends(requireAdministrator)]


def getPublicationUser(payload: dict = Depends(requireAdministrator)) -> str:
    login = payload.get("wordpressUserLogin") or payload.get("userLogin") or payload.get("username")
    if not isinstance(login, str) or not login.strip() or len(login) > 100:
        raise HTTPException(status_code=401, detail="La sesión no contiene un usuario válido.")
    return login


def getTrainingParameterApplication(db: Session = Depends(getDb)) -> ITrainingParameterApplication:
    return TrainingParameterApplication(TrainingParameterRepository(db))


def _respond(operation, message):
    try:
        return apiResponseDto(isSuccess=True, Message=message, result=operation())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except GcsStorageError as error:
        raise HTTPException(status_code=503, detail="No fue posible acceder a GCS.") from error
    except Exception as error:
        logger.exception("Error procesando parámetro de capacitación")
        raise HTTPException(status_code=500, detail="No fue posible completar la operación.") from error


@router.get("/", response_model=apiResponseDto[list[TrainingParameterResponseDto]])
def getTrainingParameters(
    isActive: bool | None = None,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.getAll(isActive), "Parámetros obtenidos correctamente.")


@router.post(
    "/complete", response_model=apiResponseDto[TrainingParameterResponseDto],
    status_code=201, dependencies=adminOnly,
    openapi_extra={
        "requestBody": {"content": {"multipart/form-data": {
            "encoding": {"topics": {"contentType": "application/json"}},
        }}},
    },
)
def createCompleteTrainingParameter(
    *,
    nameTrainingParameter: str = Form(..., description="Nombre de capacitación (máximo 200 caracteres)."),
    # Swagger sends explicitly encoded JSON parts as blobs; keep its editor a text field.
    topics: Annotated[
        str | UploadFile,
        Form(description="Arreglo JSON de temas ordenados; conservar corchetes y comillas.",
             examples=['["INTRODUCCION","PRACTICA"]']),
        WithJsonSchema({"type": "string"}),
    ],
    file: UploadFile = File(..., description="PÉNSUM oficial obligatorio."),
    userLogin: str = Depends(getPublicationUser),
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    def create():
        try:
            topicsText = topics if isinstance(topics, str) else topics.file.read().decode("utf-8")
            parsedTopics = json.loads(topicsText)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("El campo topics debe contener un arreglo JSON válido de temas.") from error
        data = TrainingParameterCompleteCreateDto(
            nameTrainingParameter=nameTrainingParameter, topics=parsedTopics,
        )
        return service.createComplete(data, file, userLogin)
    return _respond(create, "Parámetro completo creado y activado correctamente.")


@router.get("/{IdTrainingParameter}", response_model=apiResponseDto[TrainingParameterResponseDto])
def getTrainingParameter(
    IdTrainingParameter: int,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.getById(IdTrainingParameter), "Parámetro obtenido correctamente.")


@router.post(
    "/", response_model=apiResponseDto[TrainingParameterResponseDto],
    status_code=201, dependencies=adminOnly,
)
def createTrainingParameter(
    data: TrainingParameterCreateDto,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.create(data), "Parámetro creado correctamente.")


@router.put(
    "/{IdTrainingParameter}", response_model=apiResponseDto[TrainingParameterResponseDto],
    dependencies=adminOnly,
)
def updateTrainingParameter(
    IdTrainingParameter: int, data: TrainingParameterUpdateDto,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.update(IdTrainingParameter, data), "Parámetro actualizado correctamente.")


@router.patch(
    "/{IdTrainingParameter}/status", response_model=apiResponseDto[TrainingParameterResponseDto],
    dependencies=adminOnly,
)
def setTrainingParameterStatus(
    IdTrainingParameter: int, data: TrainingParameterStatusDto,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(
        lambda: service.update(IdTrainingParameter, TrainingParameterUpdateDto(isActive=data.isActive)),
        "Estado actualizado correctamente.",
    )


@router.post(
    "/{IdTrainingParameter}/pensum", response_model=apiResponseDto[TrainingParameterResponseDto],
    dependencies=adminOnly,
)
def uploadTrainingParameterPensum(
    IdTrainingParameter: int, file: UploadFile = File(...),
    userLogin: str = Depends(getPublicationUser),
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.uploadPensum(IdTrainingParameter, file, userLogin), "PÉNSUM oficial adjuntado correctamente.")


@router.put(
    "/{IdTrainingParameter}/pensum", response_model=apiResponseDto[TrainingParameterResponseDto],
    dependencies=adminOnly,
)
def updateTrainingParameterPensum(
    IdTrainingParameter: int, file: UploadFile = File(...),
    userLogin: str = Depends(getPublicationUser),
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    return _respond(lambda: service.updatePensum(IdTrainingParameter, file, userLogin), "PÉNSUM oficial actualizado correctamente.")


@router.get("/{IdTrainingParameter}/versions", response_model=apiResponseDto[list[TrainingParameterVersionResponseDto]], dependencies=adminOnly)
def getTrainingParameterVersions(IdTrainingParameter: int, service: ITrainingParameterApplication = Depends(getTrainingParameterApplication)):
    return _respond(lambda: service.getVersions(IdTrainingParameter), "Versiones registradas.")


@router.get("/{IdTrainingParameter}/versions/{versionId}/pensum/access", response_model=apiResponseDto[str], dependencies=adminOnly)
def getVersionPensumAccess(IdTrainingParameter: int, versionId: int, response: Response, download: bool = False,
                          service: ITrainingParameterApplication = Depends(getTrainingParameterApplication)):
    response.headers["Cache-Control"] = "private, no-store"
    return _respond(lambda: service.getVersionReadUrl(IdTrainingParameter, versionId, download), "Acceso temporal a la versión.")


@router.get("/{IdTrainingParameter}/pensum/access", response_model=apiResponseDto[str])
def getTrainingParameterPensumAccess(
    IdTrainingParameter: int, response: Response, download: bool = False,
    service: ITrainingParameterApplication = Depends(getTrainingParameterApplication),
):
    response.headers["Cache-Control"] = "private, no-store"
    return _respond(
        lambda: service.getPensumReadUrl(IdTrainingParameter, download),
        "Acceso temporal al PÉNSUM oficial.",
    )
