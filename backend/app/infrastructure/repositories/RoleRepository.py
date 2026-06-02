from app.domain.interfaces.IRoleRepository import IRoleRepository
from app.domain.dtos.RoleDto import RoleCreateDto, RoleUpdateDto
from app.domain.entities.RoleMenuOption import RoleMenuOption
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Role import Role
from sqlalchemy.orm import Session
from typing import List, Optional

class RoleRepository(IRoleRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[Role]:
        return self.db.query(Role).order_by(Role.IdRole.asc()).all()

    def getById(self, IdRole: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.IdRole == IdRole).first()

    def getByName(self, nameRole: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.nameRole == nameRole.strip()).first()

    def create(self, roleData: RoleCreateDto) -> Role:
        try:
            newRole = Role(nameRole=roleData.nameRole.strip(), statusRole=roleData.statusRole)

            self.db.add(newRole)
            self.db.commit()
            self.db.refresh(newRole)

            return newRole

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un rol con ese nombre.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear el rol: {str(e)}")

    def update(self, IdRole: int, roleData: RoleUpdateDto) -> Optional[Role]:
        try:
            roleFound = self.getById(IdRole)

            if not roleFound:
                return None

            if roleData.nameRole is not None:
                roleFound.nameRole = roleData.nameRole.strip()

            if roleData.statusRole is not None:
                roleFound.statusRole = roleData.statusRole

            self.db.commit()
            self.db.refresh(roleFound)

            return roleFound

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un rol con ese nombre.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el rol: {str(e)}")

    def delete(self, IdRole: int) -> bool:
        try:
            roleFound = self.getById(IdRole)

            if not roleFound:
                return False

            self.db.delete(roleFound)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar el rol: {str(e)}")

    def getMenuOptionsByRole(self, IdRole: int) -> List[MenuOption]:
        return (
            self.db.query(MenuOption)
            .join(RoleMenuOption, RoleMenuOption.IdMenuOption == MenuOption.IdMenuOption)
            .filter(RoleMenuOption.IdRole == IdRole)
            .filter(MenuOption.statusMenuOption == True)
            .order_by(MenuOption.orderMenuOption.asc())
            .all()
        )

    def setMenuOptionsToRole(self, IdRole: int, menuOptionIds: List[int]) -> List[MenuOption]:
        try:
            menuOptionIds = list(dict.fromkeys(menuOptionIds))

            self.db.query(RoleMenuOption).filter(RoleMenuOption.IdRole == IdRole).delete()

            for IdMenuOption in menuOptionIds:
                relation = RoleMenuOption(IdRole=IdRole, IdMenuOption=IdMenuOption)
                self.db.add(relation)

            self.db.commit()

            return self.getMenuOptionsByRole(IdRole)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Una o varias opciones de menú no son válidas.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al asignar opciones de menú al rol: {str(e)}")