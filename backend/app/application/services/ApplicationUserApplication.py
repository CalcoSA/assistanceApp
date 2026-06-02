from app.domain.dtos.ApplicationUserDto import (ApplicationUserCreateDto, ApplicationUserUpdateDto, ApplicationUserResponseDto)
from app.application.interfaces.IApplicationUserApplication import IApplicationUserApplication
from app.infrastructure.repositories.WordpressUserRepository import WordpressUserRepository
from app.domain.interfaces.IApplicationUserRepository import IApplicationUserRepository
from app.domain.dtos.WordpressUserDto import WordpressUserResponseDto
from app.domain.interfaces.IRoleRepository import IRoleRepository
from typing import List

class ApplicationUserApplication(IApplicationUserApplication):

    def __init__(self, applicationUserRepository: IApplicationUserRepository, roleRepository: IRoleRepository, wordpressUserRepository: WordpressUserRepository):
        self.applicationUserRepository = applicationUserRepository
        self.roleRepository = roleRepository
        self.wordpressUserRepository = wordpressUserRepository

    def searchWordpressUsers(self, search: str) -> List[WordpressUserResponseDto]:
        searchValue = search.strip()

        if len(searchValue) < 3:
            raise ValueError("Debes ingresar mínimo 3 caracteres para buscar usuarios.")

        return self.wordpressUserRepository.searchUsers(searchValue)

    def getAll(self) -> List[ApplicationUserResponseDto]:
        users = self.applicationUserRepository.getAll()
        return [self._buildResponse(user) for user in users]

    def getById(self, IdApplicationUser: int) -> ApplicationUserResponseDto:
        userFound = self.applicationUserRepository.getById(IdApplicationUser)

        if not userFound:
            raise ValueError("Usuario del aplicativo no encontrado.")

        return self._buildResponse(userFound)

    def create(self, applicationUserData: ApplicationUserCreateDto) -> ApplicationUserResponseDto:
        wordpressUser = self.wordpressUserRepository.getById(applicationUserData.wordpressUserId)

        if not wordpressUser:
            raise ValueError("Usuario de WordPress no encontrado.")

        if wordpressUser["wordpressUserLogin"] != applicationUserData.wordpressUserLogin.strip():
            raise ValueError("El ID y el usuario de WordPress no coinciden.")

        userExists = self.applicationUserRepository.getByWordpressUserId(applicationUserData.wordpressUserId)

        if userExists:
            raise ValueError("Este usuario de WordPress ya está autorizado en el aplicativo.")

        self._validateRoles(applicationUserData.roleIds)

        userCreated = self.applicationUserRepository.create(applicationUserData)

        if applicationUserData.roleIds:
            self.applicationUserRepository.setRolesToApplicationUser(userCreated.IdApplicationUser, applicationUserData.roleIds)

        return self._buildResponse(userCreated)

    def update(self, IdApplicationUser: int, applicationUserData: ApplicationUserUpdateDto) -> ApplicationUserResponseDto:
        userFound = self.applicationUserRepository.getById(IdApplicationUser)

        if not userFound:
            raise ValueError("Usuario del aplicativo no encontrado.")

        if applicationUserData.roleIds is not None:
            self._validateRoles(applicationUserData.roleIds)

        userUpdated = self.applicationUserRepository.update(IdApplicationUser, applicationUserData)

        if not userUpdated:
            raise ValueError("Usuario del aplicativo no encontrado.")

        if applicationUserData.roleIds is not None:
            self.applicationUserRepository.setRolesToApplicationUser(IdApplicationUser, applicationUserData.roleIds)

        return self._buildResponse(userUpdated)

    def delete(self, IdApplicationUser: int) -> bool:
        userFound = self.applicationUserRepository.getById(IdApplicationUser)

        if not userFound:
            raise ValueError("Usuario del aplicativo no encontrado.")

        return self.applicationUserRepository.delete(IdApplicationUser)

    def _validateRoles(self, roleIds: List[int]) -> None:
        availableRoles = self.roleRepository.getAll()
        availableRoleIds = [role.IdRole for role in availableRoles]

        for IdRole in roleIds:
            if IdRole not in availableRoleIds:
                raise ValueError(f"El rol {IdRole} no existe.")

    def _buildResponse(self, applicationUser) -> ApplicationUserResponseDto:
        roles = self.applicationUserRepository.getRolesByApplicationUser(applicationUser.IdApplicationUser)

        return ApplicationUserResponseDto(
            IdApplicationUser=applicationUser.IdApplicationUser,
            wordpressUserId=applicationUser.wordpressUserId,
            wordpressUserLogin=applicationUser.wordpressUserLogin,
            statusApplicationUser=applicationUser.statusApplicationUser,
            roles=roles
        )