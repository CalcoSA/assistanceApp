from app.domain.dtos.MenuOptionDto import MenuOptionResponseDto
from pydantic import BaseModel, EmailStr, ConfigDict
from app.domain.dtos.RoleDto import RoleResponseDto
from typing import List, Optional

class LoginDto(BaseModel):
    username: str
    password: str

class AuthUserDto(BaseModel):
    IdApplicationUser: Optional[int] = None
    wordpressUserId: Optional[int] = None
    wordpressUserLogin: str
    wordpressUserEmail: str
    wordpressDisplayName: str
    pointSaleEmailId: Optional[int] = None
    pointSaleEmail: Optional[str] = None
    roles: List[RoleResponseDto]
    menuOptions: List[MenuOptionResponseDto]

    model_config = ConfigDict(from_attributes=True)

class AuthResponseDto(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: AuthUserDto

class IntranetAccessDto(BaseModel):
    userLogin: str
    ts: int
    sig: str