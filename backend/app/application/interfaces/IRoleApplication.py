from app.domain.dtos.RoleDto import RoleCreateDto, RoleUpdateDto
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Role import Role
from abc import ABC, abstractmethod
from typing import List

class IRoleApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[Role]:
        pass

    @abstractmethod
    def getById(self, IdRole: int) -> Role:
        pass

    @abstractmethod
    def create(self, roleData: RoleCreateDto) -> Role:
        pass

    @abstractmethod
    def update(self, IdRole: int, roleData: RoleUpdateDto) -> Role:
        pass

    @abstractmethod
    def delete(self, IdRole: int) -> bool:
        pass

    @abstractmethod
    def getMenuOptionsByRole(self, IdRole: int) -> List[MenuOption]:
        pass

    @abstractmethod
    def setMenuOptionsToRole(self, IdRole: int, menuOptionIds: List[int]) -> List[MenuOption]:
        pass