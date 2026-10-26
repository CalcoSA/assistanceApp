from app.domain.dtos.EventStatusDto import EventStatusDto
from app.domain.dtos.SolutionCenterDto import SolutionCenterResponseDto
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date, datetime, time
from typing import List, Optional

class EventCreateDto(BaseModel):
    IdTrainingParameter: Optional[int] = Field(
        default=None, gt=0,
        description="Parámetro activo explícito. Si se omite topics, se usan los temas del catálogo.",
    )
    titleEvent: str
    descriptionEvent: Optional[str] = None
    dateEvent: date
    durationEvent: Optional[str] = None
    startTimeEvent: time
    endTimeEvent: time
    IdSolutionCenter: Optional[int] = None
    IdAssistanceReason: Optional[int] = None
    IdSpecificTrainingProgram: Optional[int] = None
    IdEventCategory: Optional[int] = None
    facilitatorNameEvent: Optional[str] = None
    facilitatorTypeEvent: Optional[str] = None
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorTypeEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
    thirdFacilitatorNameEvent: Optional[str] = None
    thirdFacilitatorTypeEvent: Optional[str] = None
    thirdFacilitatorCompanyEvent: Optional[str] = None
    thirdFacilitatorPositionEvent: Optional[str] = None
    scheduledPeopleNumber: Optional[int] = Field(default=None, ge=0)
    isPaidTrainingEvent: Optional[bool] = None
    isNewStaffInductionEvent: Optional[bool] = False
    observationsEvent: Optional[str] = None
    eventPlace: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    competencies: List[int] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def rejectClientOfficialPensum(cls, values):
        if isinstance(values, dict) and values.get("IdTrainingParameter") is not None:
            if any(key.startswith("pensum") for key in values):
                raise ValueError("El PÉNSUM oficial se obtiene exclusivamente del parámetro.")
        return values

class EventUpdateDto(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def rejectParameterChanges(cls, values):
        if isinstance(values, dict) and "IdTrainingParameter" in values:
            raise ValueError("IdTrainingParameter no se puede cambiar ni retirar después de crear el evento.")
        return values

    titleEvent: Optional[str] = None
    descriptionEvent: Optional[str] = None
    dateEvent: Optional[date] = None
    durationEvent: Optional[str] = None
    startTimeEvent: Optional[time] = None
    endTimeEvent: Optional[time] = None
    IdSolutionCenter: Optional[int] = None
    IdAssistanceReason: Optional[int] = None
    IdSpecificTrainingProgram: Optional[int] = None
    IdEventCategory: Optional[int] = None
    facilitatorNameEvent: Optional[str] = None
    facilitatorTypeEvent: Optional[str] = None
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorTypeEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
    thirdFacilitatorNameEvent: Optional[str] = None
    thirdFacilitatorTypeEvent: Optional[str] = None
    thirdFacilitatorCompanyEvent: Optional[str] = None
    thirdFacilitatorPositionEvent: Optional[str] = None
    scheduledPeopleNumber: Optional[int] = Field(default=None, ge=0)
    isPaidTrainingEvent: Optional[bool] = None
    isNewStaffInductionEvent: Optional[bool] = None
    observationsEvent: Optional[str] = None
    eventPlace: Optional[str] = None
    topics: Optional[List[str]] = None
    competencies: Optional[List[int]] = None

class EventCancelDto(BaseModel):
    cancellationReason: str

class EventTopicResponseDto(BaseModel):
    IdEventTopic: int
    IdEvent: int
    nameEventTopic: str

    model_config = ConfigDict(from_attributes=True)

class EventCompetencyResponseDto(BaseModel):
    IdEventCompetency: int
    IdEvent: int
    IdCompetency: int

    model_config = ConfigDict(from_attributes=True)

class EventQrResponseDto(BaseModel):
    IdEvent: int
    tokenEvent: str
    publicUrlEvent: Optional[str] = None
    qrPathEvent: Optional[str] = None

class EventResponseDto(BaseModel):
    IdEvent: int
    IdTrainingParameter: Optional[int] = None
    titleEvent: str
    descriptionEvent: Optional[str] = None
    dateEvent: date
    durationEvent: Optional[str] = None
    startTimeEvent: time
    endTimeEvent: time
    IdSolutionCenter: Optional[int] = None
    IdAssistanceReason: Optional[int] = None
    IdSpecificTrainingProgram: Optional[int] = None
    IdEventCategory: Optional[int] = None
    IdEventStatus: int
    eventStatus : Optional[EventStatusDto] = None
    solutionCenter: Optional[SolutionCenterResponseDto] = None
    facilitatorNameEvent: Optional[str] = None
    facilitatorTypeEvent: Optional[str] = None
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorTypeEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
    thirdFacilitatorNameEvent: Optional[str] = None
    thirdFacilitatorTypeEvent: Optional[str] = None
    thirdFacilitatorCompanyEvent: Optional[str] = None
    thirdFacilitatorPositionEvent: Optional[str] = None
    scheduledPeopleNumber: Optional[int] = None
    attendedPeopleNumber: Optional[int] = None
    observationsEvent: Optional[str] = None
    eventPlace: Optional[str] = None
    attendanceStartDateTime: datetime
    attendanceEndDateTime: datetime
    tokenEvent: str
    publicUrlEvent: Optional[str] = None
    qrPathEvent: Optional[str] = None
    pensumOriginalNameEvent: Optional[str] = None
    pensumPathEvent: Optional[str] = None
    pensumMimeTypeEvent: Optional[str] = None
    pensumSizeEvent: Optional[int] = None
    isPaidTrainingEvent: Optional[bool] = None
    isNewStaffInductionEvent: Optional[bool] = False
    createdByUserLogin: str
    updatedByUserLogin: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    notificationEmailSent: Optional[bool] = None
    notificationMessage: Optional[str] = None
    topics: List[EventTopicResponseDto] = Field(default_factory=list)
    competencies: List[EventCompetencyResponseDto] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class EventAttendancePersonResponseDto(BaseModel):
    IdAttendancePerson: int
    fullNameAttendancePerson: str
    documentNumberAttendancePerson: str
    positionAttendancePerson: Optional[str] = None
    IdSolutionCenter: Optional[int] = None
    phoneAttendancePerson: Optional[str] = None
    signaturePathAttendancePerson: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventAttendanceResponseDto(BaseModel):
    IdAttendance: int
    IdEvent: int
    IdAttendancePerson: int
    ipAddressAttendance: Optional[str] = None
    userAgentAttendance: Optional[str] = None
    createdAt: Optional[datetime] = None
    attendancePerson: Optional[EventAttendancePersonResponseDto] = None

    model_config = ConfigDict(from_attributes=True)

class EventPaginatedResponseDto(BaseModel):
    items: List[EventResponseDto]
    total: int
    page: int
    pageSize: int
    totalPages: int
