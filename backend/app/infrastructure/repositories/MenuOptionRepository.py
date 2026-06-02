from app.domain.dtos.MenuOptionDto import MenuOptionCreateDto, MenuOptionUpdateDto
from app.domain.interfaces.IMenuOptionRepository import IMenuOptionRepository
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.MenuOption import MenuOption
from sqlalchemy.orm import Session
from typing import List, Optional

class MenuOptionRepository(IMenuOptionRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[MenuOption]:
        return (self.db.query(MenuOption).order_by(MenuOption.orderMenuOption.asc()).all())

    def getById(self, IdMenuOption: int) -> Optional[MenuOption]:
        return (self.db.query(MenuOption).filter(MenuOption.IdMenuOption == IdMenuOption).first())

    def create(self, menuOptionData: MenuOptionCreateDto) -> MenuOption:
        try:
            newMenuOption = MenuOption(
                nameMenuOption=menuOptionData.nameMenuOption.strip(),
                pathMenuOption=menuOptionData.pathMenuOption,
                iconMenuOption=menuOptionData.iconMenuOption,
                parentMenuOption=menuOptionData.parentMenuOption,
                orderMenuOption=menuOptionData.orderMenuOption,
                statusMenuOption=menuOptionData.statusMenuOption
            )

            self.db.add(newMenuOption)
            self.db.commit()
            self.db.refresh(newMenuOption)

            return newMenuOption

        except IntegrityError:
            self.db.rollback()
            raise ValueError("La opción de menú no es válida.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear la opción de menú: {str(e)}")

    def update(self, IdMenuOption: int, menuOptionData: MenuOptionUpdateDto) -> Optional[MenuOption]:
        try:
            menuOptionFound = self.getById(IdMenuOption)

            if not menuOptionFound:
                return None

            if menuOptionData.nameMenuOption is not None:
                menuOptionFound.nameMenuOption = menuOptionData.nameMenuOption.strip()

            if menuOptionData.pathMenuOption is not None:
                menuOptionFound.pathMenuOption = menuOptionData.pathMenuOption

            if menuOptionData.iconMenuOption is not None:
                menuOptionFound.iconMenuOption = menuOptionData.iconMenuOption

            if menuOptionData.parentMenuOption is not None:
                menuOptionFound.parentMenuOption = menuOptionData.parentMenuOption

            if menuOptionData.orderMenuOption is not None:
                menuOptionFound.orderMenuOption = menuOptionData.orderMenuOption

            if menuOptionData.statusMenuOption is not None:
                menuOptionFound.statusMenuOption = menuOptionData.statusMenuOption

            self.db.commit()
            self.db.refresh(menuOptionFound)

            return menuOptionFound

        except IntegrityError:
            self.db.rollback()
            raise ValueError("La opción de menú no es válida.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar la opción de menú: {str(e)}")

    def delete(self, IdMenuOption: int) -> bool:
        try:
            menuOptionFound = self.getById(IdMenuOption)

            if not menuOptionFound:
                return False

            self.db.delete(menuOptionFound)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar la opción de menú: {str(e)}")