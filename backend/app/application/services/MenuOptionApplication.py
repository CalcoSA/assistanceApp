from app.application.interfaces.IMenuOptionApplication import IMenuOptionApplication
from app.domain.dtos.MenuOptionDto import MenuOptionCreateDto, MenuOptionUpdateDto
from app.domain.interfaces.IMenuOptionRepository import IMenuOptionRepository
from app.domain.entities.MenuOption import MenuOption
from typing import List

class MenuOptionApplication(IMenuOptionApplication):

    def __init__(self, menuOptionRepository: IMenuOptionRepository):
        self.menuOptionRepository = menuOptionRepository

    def getAll(self) -> List[MenuOption]:
        return self.menuOptionRepository.getAll()

    def getById(self, IdMenuOption: int) -> MenuOption:
        menuOptionFound = self.menuOptionRepository.getById(IdMenuOption)

        if not menuOptionFound:
            raise ValueError("Opción de menú no encontrada.")

        return menuOptionFound

    def create(self, menuOptionData: MenuOptionCreateDto) -> MenuOption:
        if not menuOptionData.nameMenuOption.strip():
            raise ValueError("El nombre de la opción de menú es obligatorio.")

        return self.menuOptionRepository.create(menuOptionData)

    def update(self, IdMenuOption: int, menuOptionData: MenuOptionUpdateDto) -> MenuOption:
        menuOptionFound = self.menuOptionRepository.getById(IdMenuOption)

        if not menuOptionFound:
            raise ValueError("Opción de menú no encontrada.")

        if menuOptionData.nameMenuOption is not None and not menuOptionData.nameMenuOption.strip():
            raise ValueError("El nombre de la opción de menú es obligatorio.")

        updatedMenuOption = self.menuOptionRepository.update(IdMenuOption, menuOptionData)

        if not updatedMenuOption:
            raise ValueError("Opción de menú no encontrada.")

        return updatedMenuOption

    def delete(self, IdMenuOption: int) -> bool:
        menuOptionFound = self.menuOptionRepository.getById(IdMenuOption)

        if not menuOptionFound:
            raise ValueError("Opción de menú no encontrada.")

        return self.menuOptionRepository.delete(IdMenuOption)