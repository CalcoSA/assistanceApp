from app.domain.dtos.MenuOptionDto import MenuOptionResponseDto
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class RoleCreateDto(BaseModel):
    nameRole: str
    statusRole: bool = True
    menuOptionIds: List[int] = Field(default_factory=list)

class RoleUpdateDto(BaseModel):
    nameRole: Optional[str] = None
    statusRole: Optional[bool] = None
    menuOptionIds: Optional[List[int]] = None

class RoleResponseDto(BaseModel):
    IdRole: int
    nameRole: str
    statusRole: bool

    model_config = ConfigDict(from_attributes=True)

class RoleDetailResponseDto(BaseModel):
    IdRole: int
    nameRole: str
    statusRole: bool
    menuOptions: List[MenuOptionResponseDto]

class AssignMenuOptionsToRoleDto(BaseModel):
    menuOptionIds: List[int] = Field(default_factory=list)