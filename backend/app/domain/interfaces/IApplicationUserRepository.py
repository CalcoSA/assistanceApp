from app.domain.dtos.ApplicationUserDto import ApplicationUserCreateDto, ApplicationUserUpdateDto
from app.domain.entities.ApplicationUser import ApplicationUser
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Role import Role
from abc import ABC, abstractmethod
from typing import List, Optional

class IApplicationUserRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[ApplicationUser]:
        pass

    @abstractmethod
    def getById(self, IdApplicationUser: int) -> Optional[ApplicationUser]:
        pass

    @abstractmethod
    def getByWordpressUserId(self, wordpressUserId: int) -> Optional[ApplicationUser]:
        pass

    @abstractmethod
    def getByWordpressUserLogin(self, wordpressUserLogin: str) -> Optional[ApplicationUser]:
        pass

    @abstractmethod
    def create(self, applicationUserData: ApplicationUserCreateDto) -> ApplicationUser:
        pass

    @abstractmethod
    def update(self, IdApplicationUser: int, applicationUserData: ApplicationUserUpdateDto) -> Optional[ApplicationUser]:
        pass

    @abstractmethod
    def delete(self, IdApplicationUser: int) -> bool:
        pass

    @abstractmethod
    def getRolesByApplicationUser(self, IdApplicationUser: int) -> List[Role]:
        pass

    @abstractmethod
    def setRolesToApplicationUser(self, IdApplicationUser: int, roleIds: List[int]) -> List[Role]:
        pass

    @abstractmethod
    def getMenuOptionsByApplicationUser(self, IdApplicationUser: int) -> List[MenuOption]:
        pass