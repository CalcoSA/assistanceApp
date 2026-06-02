from app.domain.interfaces.IMenuOptionRepository import IMenuOptionRepository
from app.application.interfaces.IRoleApplication import IRoleApplication
from app.domain.interfaces.IRoleRepository import IRoleRepository
from app.domain.dtos.RoleDto import RoleCreateDto, RoleUpdateDto
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Role import Role
from typing import List

class RoleApplication(IRoleApplication):

    def __init__(self, roleRepository: IRoleRepository, menuOptionRepository: IMenuOptionRepository):
        self.roleRepository = roleRepository
        self.menuOptionRepository = menuOptionRepository

    def getAll(self) -> List[Role]:
        return self.roleRepository.getAll()

    def getById(self, IdRole: int) -> Role:
        roleFound = self.roleRepository.getById(IdRole)

        if not roleFound:
            raise ValueError("Rol no encontrado.")

        return roleFound

    def create(self, roleData: RoleCreateDto) -> Role:
        nameRole = roleData.nameRole.strip()

        if not nameRole:
            raise ValueError("El nombre del rol es obligatorio.")

        roleExists = self.roleRepository.getByName(nameRole)

        if roleExists:
            raise ValueError("Ya existe un rol con ese nombre.")

        roleData.nameRole = nameRole

        roleCreated = self.roleRepository.create(roleData)

        if roleData.menuOptionIds:
            self.setMenuOptionsToRole(roleCreated.IdRole, roleData.menuOptionIds)

        return roleCreated

    def update(self, IdRole: int, roleData: RoleUpdateDto) -> Role:
        roleFound = self.roleRepository.getById(IdRole)

        if not roleFound:
            raise ValueError("Rol no encontrado.")

        if roleData.nameRole is not None:
            nameRole = roleData.nameRole.strip()

            if not nameRole:
                raise ValueError("El nombre del rol es obligatorio.")

            roleExists = self.roleRepository.getByName(nameRole)

            if roleExists and roleExists.IdRole != IdRole:
                raise ValueError("Ya existe un rol con ese nombre.")

            roleData.nameRole = nameRole

        roleUpdated = self.roleRepository.update(IdRole, roleData)

        if not roleUpdated:
            raise ValueError("Rol no encontrado.")

        if roleData.menuOptionIds is not None:
            self.setMenuOptionsToRole(IdRole, roleData.menuOptionIds)

        return roleUpdated

    def delete(self, IdRole: int) -> bool:
        roleFound = self.roleRepository.getById(IdRole)

        if not roleFound:
            raise ValueError("Rol no encontrado.")

        return self.roleRepository.delete(IdRole)

    def getMenuOptionsByRole(self, IdRole: int) -> List[MenuOption]:
        roleFound = self.roleRepository.getById(IdRole)

        if not roleFound:
            raise ValueError("Rol no encontrado.")

        return self.roleRepository.getMenuOptionsByRole(IdRole)

    def setMenuOptionsToRole(self, IdRole: int, menuOptionIds: List[int]) -> List[MenuOption]:
        roleFound = self.roleRepository.getById(IdRole)

        if not roleFound:
            raise ValueError("Rol no encontrado.")

        availableOptions = self.menuOptionRepository.getAll()
        availableIds = [item.IdMenuOption for item in availableOptions]

        for IdMenuOption in menuOptionIds:
            if IdMenuOption not in availableIds:
                raise ValueError(f"La opción de menú {IdMenuOption} no existe.")

        return self.roleRepository.setMenuOptionsToRole(IdRole, menuOptionIds)