from app.infrastructure.repositories.WordpressUserRepository import WordpressUserRepository
from app.application.services.WordpressPasswordVerifier import WordpressPasswordVerifier
from app.domain.interfaces.IApplicationUserRepository import IApplicationUserRepository
from app.domain.dtos.AuthDto import LoginDto, AuthResponseDto, AuthUserDto
from app.infrastructure.repositories.RoleRepository import RoleRepository
from app.application.interfaces.IAuthApplication import IAuthApplication
from app.application.services.JwtService import JwtService
from app.infrastructure.db.config import settings
import hashlib
import hmac
import time

class AuthApplication(IAuthApplication):

    def __init__(
        self,
        applicationUserRepository: IApplicationUserRepository,
        wordpressUserRepository: WordpressUserRepository,
        wordpressPasswordVerifier: WordpressPasswordVerifier,
        roleRepository: RoleRepository
    ):
        self.applicationUserRepository = applicationUserRepository
        self.wordpressUserRepository = wordpressUserRepository
        self.wordpressPasswordVerifier = wordpressPasswordVerifier
        self.roleRepository = roleRepository

    def login(self, loginData: LoginDto) -> AuthResponseDto:
        username = loginData.username.strip()

        wordpressUser = self.wordpressUserRepository.getByLoginOrEmail(username)

        if not wordpressUser:
            raise ValueError("Usuario o contraseña incorrectos.")

        passwordIsValid = self.wordpressPasswordVerifier.verify(loginData.password, wordpressUser["wordpressUserPass"])

        if not passwordIsValid:
            raise ValueError("Usuario o contraseña incorrectos.")

        return self._authorizeAndBuildAuthResponse(wordpressUser)

    def intranetAccess(self, userLogin: str, ts: int, sig: str) -> AuthResponseDto:
        self._validateIntranetSignature(userLogin, ts, sig)

        wordpressUser = self.wordpressUserRepository.getByLogin(userLogin)

        if not wordpressUser:
            raise PermissionError("Usuario de WordPress no encontrado.")

        return self._authorizeAndBuildAuthResponse(wordpressUser)

    def getCurrentUser(self, wordpressUserId: int) -> AuthResponseDto:
        wordpressUser = self.wordpressUserRepository.getById(wordpressUserId)

        if not wordpressUser:
            raise PermissionError("Usuario de WordPress no encontrado.")

        return self._authorizeAndBuildAuthResponse(wordpressUser)

    def _authorizeAndBuildAuthResponse(self, wordpressUser: dict) -> AuthResponseDto:
        applicationUser = self.applicationUserRepository.getByWordpressUserId(wordpressUser["wordpressUserId"])

        if not applicationUser:
            raise PermissionError("El usuario no está autorizado para ingresar al aplicativo.")

        if not applicationUser.statusApplicationUser:
            raise PermissionError("El usuario está inactivo en el aplicativo.")

        roles = self.applicationUserRepository.getRolesByApplicationUser(applicationUser.IdApplicationUser)

        if not roles:
            raise PermissionError("El usuario no tiene roles asignados.")

        menuOptions = self.applicationUserRepository.getMenuOptionsByApplicationUser(applicationUser.IdApplicationUser)

        tokenPayload = {
            "sub": str(wordpressUser["wordpressUserId"]),
            "wordpressUserId": wordpressUser["wordpressUserId"],
            "wordpressUserLogin": wordpressUser["wordpressUserLogin"],
            "IdApplicationUser": applicationUser.IdApplicationUser,
            "roleIds": [role.IdRole for role in roles],
            "roles": [role.nameRole for role in roles]
        }

        accessToken = JwtService.createToken(tokenPayload)

        return AuthResponseDto(
            accessToken=accessToken,
            user=AuthUserDto(
                IdApplicationUser=applicationUser.IdApplicationUser,
                wordpressUserId=wordpressUser["wordpressUserId"],
                wordpressUserLogin=wordpressUser["wordpressUserLogin"],
                wordpressUserEmail=wordpressUser["wordpressUserEmail"],
                wordpressDisplayName=wordpressUser["wordpressDisplayName"],
                roles=roles,
                menuOptions=menuOptions
            )
        )

    def _validateIntranetSignature(self, userLogin: str, ts: int, sig: str) -> None:
        now = int(time.time())

        if ts > now + 60:
            raise PermissionError("La firma de intranet tiene una fecha inválida.")

        if now - ts > settings.INTRANET_SSO_EXPIRE_SECONDS:
            raise PermissionError("El enlace de intranet expiró.")

        message = f"{userLogin}.{ts}".encode("utf-8")

        expectedSignature = hmac.new(
            settings.INTRANET_SSO_SECRET.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expectedSignature, sig):
            raise PermissionError("La firma de intranet no es válida.")