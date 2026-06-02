from pydantic import BaseModel, ConfigDict
from datetime import date, datetime, time
from typing import Optional

class PublicEventResponseDto(BaseModel):
    IdEvent: int
    titleEvent: str
    descriptionEvent: Optional[str] = None
    dateEvent: date
    startTimeEvent: time
    endTimeEvent: time
    eventPlace: Optional[str] = None
    facilitatorNameEvent: Optional[str] = None
    attendanceStartDateTime: datetime
    attendanceEndDateTime: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendancePersonResponseDto(BaseModel):
    IdAttendancePerson: int
    fullNameAttendancePerson: str
    documentNumberAttendancePerson: str
    positionAttendancePerson: Optional[str] = None
    IdSolutionCenter: Optional[int] = None
    phoneAttendancePerson: Optional[str] = None
    signaturePathAttendancePerson: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AttendanceRegisterDto(BaseModel):
    documentNumberAttendancePerson: str
    fullNameAttendancePerson: str
    positionAttendancePerson: Optional[str] = None
    IdSolutionCenter: Optional[int] = None
    IdPersonnelType: int
    phoneAttendancePerson: Optional[str] = None
    signatureBase64: Optional[str] = None

class AttendanceRegisterResponseDto(BaseModel):
    IdAttendance: int
    IdEvent: int
    IdAttendancePerson: int
    attendedPeopleNumber: int

class PersonnelTypeResponseDto(BaseModel):
    IdPersonnelType: int
    namePersonnelType: str

    model_config = ConfigDict(from_attributes=True)