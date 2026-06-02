from app.domain.dtos.AttendanceDto import (PublicEventResponseDto, AttendancePersonResponseDto, AttendanceRegisterDto, AttendanceRegisterResponseDto, PersonnelTypeResponseDto)
from app.infrastructure.repositories.AttendancePersonRepository import AttendancePersonRepository
from app.infrastructure.repositories.PersonnelTypeRepository import PersonnelTypeRepository
from app.application.interfaces.IAttendanceApplication import IPublicAttendanceApplication
from app.application.services.AttendanceApplication import PublicAttendanceApplication
from app.infrastructure.repositories.AttendanceRepository import AttendanceRepository
from app.domain.interfaces.IPersonnelTypeRepository import IPersonnelTypeRepository
from app.infrastructure.repositories.EventRepository import EventRepository
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.infrastructure.logging.loggerConfig import getLogger
from app.domain.dtos.ApiResponseDto import apiResponseDto
from app.infrastructure.db.connection import getDb
from sqlalchemy.orm import Session
from typing import Optional, List

router = APIRouter(prefix="/public-attendance", tags=["public-attendance"])
logger = getLogger(__name__)

def getPublicAttendanceApplication(db: Session = Depends(getDb)) -> IPublicAttendanceApplication:
    eventRepository = EventRepository(db)
    attendancePersonRepository = AttendancePersonRepository(db)
    attendanceRepository = AttendanceRepository(db)
    personnelTypeRepository = PersonnelTypeRepository(db)

    return PublicAttendanceApplication(eventRepository, attendancePersonRepository, attendanceRepository, personnelTypeRepository)

def getPersonnelTypeRepository(db: Session = Depends(getDb)) -> IPersonnelTypeRepository:
    return PersonnelTypeRepository(db)

@router.get("/{tokenEvent}/event", response_model=apiResponseDto[PublicEventResponseDto])
def getPublicEventByToken(tokenEvent: str, service: IPublicAttendanceApplication = Depends(getPublicAttendanceApplication)):
    try:
        logger.info("Consultando evento público | tokenEvent=%s", tokenEvent)
        data = service.getEventByToken(tokenEvent)
        return apiResponseDto(isSuccess=True, Message="Evento obtenido correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación consultando evento público | tokenEvent=%s | error=%s", tokenEvent, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error consultando evento público | tokenEvent=%s", tokenEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al consultar el evento.")
    
@router.get("/personnel-types", response_model=apiResponseDto[List[PersonnelTypeResponseDto]])
def getPersonnelTypes(repository: IPersonnelTypeRepository = Depends(getPersonnelTypeRepository)):
    try:
        logger.info("Consultando tipos de personal")
        data = repository.getAll()
        return apiResponseDto(
            isSuccess=True,
            Message="Tipos de personal obtenidos correctamente.",
            result=[
                PersonnelTypeResponseDto.model_validate(item)
                for item in data
            ],
        )

    except Exception:
        logger.exception("Error consultando tipos de personal")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al consultar los tipos de personal.")

@router.get("/person/{documentNumber}", response_model=apiResponseDto[Optional[AttendancePersonResponseDto]])
def getAttendancePersonByDocument(documentNumber: str, service: IPublicAttendanceApplication = Depends(getPublicAttendanceApplication)):
    try:
        logger.info("Consultando persona de asistencia | documentNumber=%s", documentNumber)
        data = service.getPersonByDocument(documentNumber)

        if not data:
            return apiResponseDto(isSuccess=False, Message="Persona no encontrada.", result=None)

        return apiResponseDto(isSuccess=True, Message="Persona encontrada correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación consultando persona | documentNumber=%s | error=%s", documentNumber, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error consultando persona | documentNumber=%s", documentNumber)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al consultar la persona.")

@router.post("/{tokenEvent}/register", response_model=apiResponseDto[AttendanceRegisterResponseDto], status_code=status.HTTP_201_CREATED)
def registerPublicAttendance(tokenEvent: str, attendanceData: AttendanceRegisterDto, request: Request, service: IPublicAttendanceApplication = Depends(getPublicAttendanceApplication)):
    try:
        forwardedFor = request.headers.get("x-forwarded-for")
        ipAddress = forwardedFor.split(",")[0].strip() if forwardedFor else (request.client.host if request.client else None)
        userAgent = request.headers.get("user-agent")
        logger.info("Registrando asistencia pública | tokenEvent=%s | document=%s | ip=%s", tokenEvent, attendanceData.documentNumberAttendancePerson, ipAddress)
        data = service.registerAttendance(tokenEvent, attendanceData, ipAddress, userAgent)
        return apiResponseDto(isSuccess=True, Message="Asistencia registrada correctamente.", result=data)

    except ValueError as e:
        logger.warning("Validación registrando asistencia | tokenEvent=%s | document=%s | error=%s", tokenEvent, attendanceData.documentNumberAttendancePerson, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:
        logger.exception("Error registrando asistencia | tokenEvent=%s", tokenEvent)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al registrar la asistencia.")