from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.dependencies.AuthDependencies import requireAdministrator, requireMenuPermission
from app.api.onlyOfficeController import getCurrentAuthContext
from app.api.trainingParameterController import _respond
from app.application.services.PensumHistoryApplication import PensumHistoryApplication
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.domain.dtos.PensumHistoryDto import PensumHistoryPageDto, PensumEventPageDto
from app.infrastructure.db.connection import getDb
from app.infrastructure.repositories.PensumHistoryRepository import PensumHistoryRepository

historyPermission = requireMenuPermission("/maestros/historico-pensum")
router = APIRouter(prefix="/pensum-history", tags=["pensum-history"],
                   dependencies=[Depends(requireAdministrator), Depends(historyPermission)])


def getPensumHistoryApplication(db: Session = Depends(getDb)):
    return PensumHistoryApplication(PensumHistoryRepository(db))


@router.get("", response_model=apiResponseDto[PensumHistoryPageDto])
def getPensumHistory(response: Response, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100),
                     search: str = Query("", max_length=200),
                     origin: Literal["all", "parameter", "freeEvent", "parameterEvent"] = "all",
                     versionState: Literal["all", "current", "previous"] = "all",
                     auth: dict = Depends(getCurrentAuthContext), service: PensumHistoryApplication = Depends(getPensumHistoryApplication)):
    response.headers["Cache-Control"] = "private, no-store"
    return _respond(lambda: service.getPage(auth["userLogin"], auth["roles"], page=page, pageSize=pageSize,
                    search=search.strip(), origin=origin, versionState=versionState), "Histórico de PÉNSUM.")


@router.get("/events", response_model=apiResponseDto[PensumEventPageDto])
def getDocumentEvents(versionId: int | None = Query(None, ge=1), eventId: int | None = Query(None, ge=1),
                      page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100),
                      auth: dict = Depends(getCurrentAuthContext), service: PensumHistoryApplication = Depends(getPensumHistoryApplication)):
    if (versionId is None) == (eventId is None):
        raise HTTPException(400, "Indique una versión o un evento, exclusivamente.")
    return _respond(lambda: service.getEvents(auth["userLogin"], auth["roles"], versionId=versionId,
                    eventId=eventId, page=page, pageSize=pageSize), "Eventos asociados al documento.")


@router.get("/events/{eventId}/local")
def getLocalPensum(eventId: int, auth: dict = Depends(getCurrentAuthContext),
                   service: PensumHistoryApplication = Depends(getPensumHistoryApplication)):
    try:
        path, name, mime = service.getLocalDocument(eventId, auth["userLogin"], auth["roles"])
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except PermissionError as error:
        raise HTTPException(403, "La ruta del documento no es válida.") from error
    return FileResponse(path, filename=name, media_type=mime,
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
