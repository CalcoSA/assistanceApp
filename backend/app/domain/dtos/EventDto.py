from app.domain.dtos.EventStatusDto import EventStatusDto
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime, time
from typing import List, Optional

class EventCreateDto(BaseModel):
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
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
    scheduledPeopleNumber: Optional[int] = None
    isPaidTrainingEvent: Optional[bool] = None
    isNewStaffInductionEvent: Optional[bool] = False
    observationsEvent: Optional[str] = None
    eventPlace: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    competencies: List[int] = Field(default_factory=list)

class EventUpdateDto(BaseModel):
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
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
    scheduledPeopleNumber: Optional[int] = None
    isPaidTrainingEvent: Optional[bool] = None
    isNewStaffInductionEvent: Optional[bool] = None
    observationsEvent: Optional[str] = None
    eventPlace: Optional[str] = None
    topics: Optional[List[str]] = None
    competencies: Optional[List[int]] = None

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
    facilitatorNameEvent: Optional[str] = None
    facilitatorCompanyEvent: Optional[str] = None
    facilitatorPositionEvent: Optional[str] = None
    secondFacilitatorNameEvent: Optional[str] = None
    secondFacilitatorCompanyEvent: Optional[str] = None
    secondFacilitatorPositionEvent: Optional[str] = None
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