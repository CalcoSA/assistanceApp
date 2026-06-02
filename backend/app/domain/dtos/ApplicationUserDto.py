from app.domain.dtos.RoleDto import RoleResponseDto
from pydantic import BaseModel, Field
from typing import List, Optional

class ApplicationUserCreateDto(BaseModel):
    wordpressUserId: int
    wordpressUserLogin: str
    statusApplicationUser: bool = True
    roleIds: List[int] = Field(default_factory=list)

class ApplicationUserUpdateDto(BaseModel):
    statusApplicationUser: Optional[bool] = None
    roleIds: Optional[List[int]] = None

class AssignRolesToApplicationUserDto(BaseModel):
    roleIds: List[int] = Field(default_factory=list)

class ApplicationUserResponseDto(BaseModel):
    IdApplicationUser: int
    wordpressUserId: int
    wordpressUserLogin: str
    statusApplicationUser: bool
    roles: List[RoleResponseDto]