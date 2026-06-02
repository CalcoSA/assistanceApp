from pydantic import BaseModel, ConfigDict
from typing import Optional

class MenuOptionCreateDto(BaseModel):
    nameMenuOption: str
    pathMenuOption: Optional[str] = None
    iconMenuOption: Optional[str] = None
    parentMenuOption: Optional[int] = None
    orderMenuOption: int = 0
    statusMenuOption: bool = True

class MenuOptionUpdateDto(BaseModel):
    nameMenuOption: Optional[str] = None
    pathMenuOption: Optional[str] = None
    iconMenuOption: Optional[str] = None
    parentMenuOption: Optional[int] = None
    orderMenuOption: Optional[int] = None
    statusMenuOption: Optional[bool] = None

class MenuOptionResponseDto(BaseModel):
    IdMenuOption: int
    nameMenuOption: str
    pathMenuOption: Optional[str] = None
    iconMenuOption: Optional[str] = None
    parentMenuOption: Optional[int] = None
    orderMenuOption: int
    statusMenuOption: bool

    model_config = ConfigDict(from_attributes=True)