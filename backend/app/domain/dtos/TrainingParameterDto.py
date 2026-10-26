from datetime import datetime
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalizeName(value: str, limit: int) -> str:
    value = unicodedata.normalize("NFC", " ".join(value.split()).upper())
    if not value or len(value) > limit:
        raise ValueError(f"El nombre es obligatorio y no puede superar {limit} caracteres.")
    return value


def normalizeTopics(topics: list[str]) -> list[str]:
    names = [normalizeName(topic, 300) for topic in topics]
    # Match case/accent-insensitive catalog names before the DB unique constraint.
    keys = [
        "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
        for name in names
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("Los temas no pueden repetirse dentro del mismo parámetro.")
    return names


class TrainingParameterCreateDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nameTrainingParameter: str
    topics: list[str] = Field(
        default_factory=list, description="Lista de temas; su posición define sortOrder desde cero.",
    )
    isActive: bool = False

    @field_validator("nameTrainingParameter")
    @classmethod
    def validateName(cls, value):
        return normalizeName(value, 200)

    @field_validator("topics")
    @classmethod
    def validateTopics(cls, value):
        return normalizeTopics(value)


class TrainingParameterCompleteCreateDto(TrainingParameterCreateDto):
    topics: list[str] = Field(..., min_length=1, description="Temas ordenados; se requiere al menos uno.")


class TrainingParameterUpdateDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nameTrainingParameter: str | None = None
    topics: list[str] | None = Field(
        default=None, description="Si se envía, reemplaza los temas del catálogo en este orden.",
    )
    isActive: bool | None = None

    @field_validator("nameTrainingParameter", "topics", "isActive")
    @classmethod
    def rejectNull(cls, value):
        if value is None:
            raise ValueError("Omita el campo si no desea actualizarlo; no se acepta null.")
        return value

    @field_validator("nameTrainingParameter")
    @classmethod
    def validateName(cls, value):
        return normalizeName(value, 200)

    @field_validator("topics")
    @classmethod
    def validateTopics(cls, value):
        return normalizeTopics(value)


class TrainingParameterStatusDto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    isActive: bool


class ParameterTopicResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    IdParameterTopic: int
    IdTrainingParameter: int
    nameParameterTopic: str
    sortOrder: int


class TrainingParameterResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    IdTrainingParameter: int
    nameTrainingParameter: str
    pensumPathTrainingParameter: str | None = None
    pensumOriginalNameTrainingParameter: str | None = None
    pensumMimeTypeTrainingParameter: str | None = None
    pensumSizeTrainingParameter: int | None = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime | None = None
    topics: list[ParameterTopicResponseDto] = Field(default_factory=list)
