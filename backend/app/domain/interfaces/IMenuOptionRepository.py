from app.domain.dtos.MenuOptionDto import MenuOptionCreateDto, MenuOptionUpdateDto
from app.domain.entities.MenuOption import MenuOption
from abc import ABC, abstractmethod
from typing import List, Optional

class IMenuOptionRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[MenuOption]:
        pass

    @abstractmethod
    def getById(self, IdMenuOption: int) -> Optional[MenuOption]:
        pass

    @abstractmethod
    def create(self, menuOptionData: MenuOptionCreateDto) -> MenuOption:
        pass

    @abstractmethod
    def update(self, IdMenuOption: int, menuOptionData: MenuOptionUpdateDto) -> Optional[MenuOption]:
        pass

    @abstractmethod
    def delete(self, IdMenuOption: int) -> bool:
        pass