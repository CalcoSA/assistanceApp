from app.domain.dtos.ApplicationUserDto import ApplicationUserCreateDto, ApplicationUserUpdateDto
from app.domain.interfaces.IApplicationUserRepository import IApplicationUserRepository
from app.domain.entities.ApplicationUserRole import ApplicationUserRole
from app.domain.entities.ApplicationUser import ApplicationUser
from app.domain.entities.RoleMenuOption import RoleMenuOption
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Role import Role
from sqlalchemy.orm import Session
from typing import List, Optional

class ApplicationUserRepository(IApplicationUserRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[ApplicationUser]:
        return (self.db.query(ApplicationUser).order_by(ApplicationUser.IdApplicationUser.asc()).all())

    def getById(self, IdApplicationUser: int) -> Optional[ApplicationUser]:
        return (self.db.query(ApplicationUser).filter(ApplicationUser.IdApplicationUser == IdApplicationUser).first())

    def getByWordpressUserId(self, wordpressUserId: int) -> Optional[ApplicationUser]:
        return (self.db.query(ApplicationUser).filter(ApplicationUser.wordpressUserId == wordpressUserId).first())

    def getByWordpressUserLogin(self, wordpressUserLogin: str) -> Optional[ApplicationUser]:
        return (self.db.query(ApplicationUser).filter(ApplicationUser.wordpressUserLogin == wordpressUserLogin.strip()).first())

    def create(self, applicationUserData: ApplicationUserCreateDto) -> ApplicationUser:
        try:
            newApplicationUser = ApplicationUser(
                wordpressUserId=applicationUserData.wordpressUserId,
                wordpressUserLogin=applicationUserData.wordpressUserLogin.strip(),
                statusApplicationUser=applicationUserData.statusApplicationUser
            )

            self.db.add(newApplicationUser)
            self.db.commit()
            self.db.refresh(newApplicationUser)

            return newApplicationUser

        except IntegrityError:
            self.db.rollback()
            raise ValueError("El usuario de WordPress ya está autorizado en el aplicativo.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear el usuario del aplicativo: {str(e)}")

    def update(self, IdApplicationUser: int, applicationUserData: ApplicationUserUpdateDto) -> Optional[ApplicationUser]:
        try:
            applicationUserFound = self.getById(IdApplicationUser)

            if not applicationUserFound:
                return None

            if applicationUserData.statusApplicationUser is not None:
                applicationUserFound.statusApplicationUser = applicationUserData.statusApplicationUser

            self.db.commit()
            self.db.refresh(applicationUserFound)

            return applicationUserFound

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el usuario del aplicativo: {str(e)}")

    def delete(self, IdApplicationUser: int) -> bool:
        try:
            applicationUserFound = self.getById(IdApplicationUser)

            if not applicationUserFound:
                return False

            self.db.delete(applicationUserFound)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar el usuario del aplicativo: {str(e)}")

    def getRolesByApplicationUser(self, IdApplicationUser: int) -> List[Role]:
        return (
            self.db.query(Role)
            .join(ApplicationUserRole, ApplicationUserRole.IdRole == Role.IdRole)
            .filter(ApplicationUserRole.IdApplicationUser == IdApplicationUser)
            .filter(ApplicationUserRole.statusApplicationUserRole == True)
            .filter(Role.statusRole == True)
            .order_by(Role.nameRole.asc())
            .all()
        )

    def setRolesToApplicationUser(self, IdApplicationUser: int, roleIds: List[int]) -> List[Role]:
        try:
            roleIds = list(dict.fromkeys(roleIds))

            self.db.query(ApplicationUserRole).filter(ApplicationUserRole.IdApplicationUser == IdApplicationUser).delete()

            for IdRole in roleIds:
                relation = ApplicationUserRole(IdApplicationUser=IdApplicationUser, IdRole=IdRole, statusApplicationUserRole=True)
                self.db.add(relation)

            self.db.commit()

            return self.getRolesByApplicationUser(IdApplicationUser)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Uno o varios roles no son válidos.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al asignar roles al usuario: {str(e)}")

    def getMenuOptionsByApplicationUser(self, IdApplicationUser: int) -> List[MenuOption]:
        return (
            self.db.query(MenuOption)
            .join(RoleMenuOption, RoleMenuOption.IdMenuOption == MenuOption.IdMenuOption)
            .join(Role, Role.IdRole == RoleMenuOption.IdRole)
            .join(ApplicationUserRole, ApplicationUserRole.IdRole == Role.IdRole)
            .filter(ApplicationUserRole.IdApplicationUser == IdApplicationUser)
            .filter(ApplicationUserRole.statusApplicationUserRole == True)
            .filter(Role.statusRole == True)
            .filter(MenuOption.statusMenuOption == True)
            .distinct()
            .order_by(MenuOption.orderMenuOption.asc())
            .all()
        )