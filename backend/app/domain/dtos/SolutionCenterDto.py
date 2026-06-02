from pydantic import BaseModel, ConfigDict
from typing import Optional

class SolutionCenterCreateDto(BaseModel):
    codeSolutionCenter: str
    nameSolutionCenter: str
    statusSolutionCenter: bool = True

class SolutionCenterUpdateDto(BaseModel):
    codeSolutionCenter: Optional[str] = None
    nameSolutionCenter: Optional[str] = None
    statusSolutionCenter: Optional[bool] = None

class SolutionCenterResponseDto(BaseModel):
    IdSolutionCenter: int
    codeSolutionCenter: str
    nameSolutionCenter: str
    statusSolutionCenter: bool

    model_config = ConfigDict(from_attributes=True)