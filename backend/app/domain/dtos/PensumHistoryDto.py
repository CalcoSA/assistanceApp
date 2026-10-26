from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TrainingParameterVersionResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    IdTrainingParameterVersion: int
    IdTrainingParameter: int
    versionNumber: int
    pensumPathTrainingParameterVersion: str
    pensumOriginalNameTrainingParameterVersion: str
    pensumMimeTypeTrainingParameterVersion: str
    pensumSizeTrainingParameterVersion: int
    createdAt: datetime
    createdByUserLogin: str | None
    isBaseline: bool
    isCurrent: bool = False
    parameterName: str = ""


class PensumEventAssociationDto(BaseModel):
    IdEvent: int
    titleEvent: str
    IdTrainingParameter: int | None
    createdAt: datetime | None


class PensumEventPageDto(BaseModel):
    items: list[PensumEventAssociationDto]
    total: int
    page: int
    pageSize: int


class PensumHistoryItemDto(BaseModel):
    documentKey: str
    name: str
    mime: str | None
    size: int | None
    registeredAt: datetime | None
    isLocal: bool
    versions: list[TrainingParameterVersionResponseDto] = Field(default_factory=list)
    events: list[PensumEventAssociationDto] = Field(default_factory=list)
    eventCount: int
    eventId: int | None
    origins: list[str]


class PensumHistoryPageDto(BaseModel):
    items: list[PensumHistoryItemDto]
    total: int
    page: int
    pageSize: int
