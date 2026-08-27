from pydantic import BaseModel, ConfigDict
from typing import Optional


class ParameterCreateDto(BaseModel):
    nameParameter: str
    valueParameter: str


class ParameterUpdateDto(BaseModel):
    valueParameter: Optional[str] = None


class ParameterResponseDto(BaseModel):
    IdParameter: int
    nameParameter: str
    valueParameter: str

    model_config = ConfigDict(from_attributes=True)
