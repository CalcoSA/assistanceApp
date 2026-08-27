from app.infrastructure.repositories.ReportRepository import ReportRepository
from app.application.interfaces.IReportApplication import IReportApplication
from app.application.services.ReportApplication import ReportApplication
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.application.services.JwtService import JwtService
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.domain.dtos.ReportDto import (
    TrainingReportResponseDto,
    SstTrainingReportResponseDto,
    TrainingHoursReportResponseDto,
    NewStaffInductionReportResponseDto,
    AdministrativeInductionReportResponseDto,
    TransversalTrainingReportResponseDto,
    CollaboratorTrainingReportResponseDto,
    GeneralReportResponseDto,
    AverageTrainingTimeReportResponseDto
)

router = APIRouter(prefix="/reports", tags=["Reports"])
security = HTTPBearer()

def getReportApplication(db: Session = Depends(getDb)) -> IReportApplication:
    reportRepository = ReportRepository(db)
    return ReportApplication(reportRepository)

def getCurrentAuthContext(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = JwtService.decodeToken(credentials.credentials)
    userLogin = (payload.get("wordpressUserLogin") or payload.get("userLogin") or payload.get("username"))

    if not userLogin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido. No contiene usuario.")

    roles = []

    if isinstance(payload.get("roles"), list):
        roles = payload.get("roles")

    return { "userLogin": userLogin, "roles": roles }

@router.get("/training", response_model=apiResponseDto[TrainingReportResponseDto])
def getTrainingReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getTrainingReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de capacitación obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de capacitación.",)
    
@router.get("/sst-training", response_model=apiResponseDto[SstTrainingReportResponseDto])
def getSstTrainingReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getSstTrainingReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de capacitación SST obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de capacitación SST.",)
    
@router.get("/training-hours", response_model=apiResponseDto[TrainingHoursReportResponseDto])
def getTrainingHoursReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getTrainingHoursReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de horas de capacitación obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de horas de capacitación.",)
    
@router.get("/new-staff-induction", response_model=apiResponseDto[NewStaffInductionReportResponseDto])
def getNewStaffInductionReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getNewStaffInductionReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de inducción a personal nuevo obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de inducción a personal nuevo.",)
    
@router.get("/administrative-induction", response_model=apiResponseDto[AdministrativeInductionReportResponseDto])
def getAdministrativeInductionReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getAdministrativeInductionReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de inducción a personal administrativo obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)
    
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de inducción a personal administrativo.",)
    
@router.get("/transversal-training", response_model=apiResponseDto[TransversalTrainingReportResponseDto])
def getTransversalTrainingReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getTransversalTrainingReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte de capacitaciones transversales obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de capacitaciones transversales.",)

@router.get("/general", response_model=apiResponseDto[GeneralReportResponseDto])
def getGeneralReport(dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getGeneralReport(dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Reporte general obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte general.",)
    
@router.get("/collaborator-training", response_model=apiResponseDto[CollaboratorTrainingReportResponseDto])
def getCollaboratorTrainingReport(search: str = Query(..., min_length=1, max_length=200), dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getCollaboratorTrainingReport(search, dateFrom, dateTo)
        return apiResponseDto(isSuccess=True, Message="Historial de capacitaciones del colaborador obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el historial de capacitaciones del colaborador.",)

@router.get("/average-training-time", response_model=apiResponseDto[AverageTrainingTimeReportResponseDto])
def getAverageTrainingTimeReport(totalWorkers: int = Query(..., gt=0), dateFrom: Optional[date] = Query(None), dateTo: Optional[date] = Query(None), authContext: dict = Depends(getCurrentAuthContext), service: IReportApplication = Depends(getReportApplication),):
    try:
        data = service.getAverageTrainingTimeReport(dateFrom, dateTo, totalWorkers,)
        return apiResponseDto(isSuccess=True, Message="Reporte de promedio de tiempo de capacitación obtenido correctamente.", result=data,)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener el reporte de promedio de tiempo de capacitación.",)
