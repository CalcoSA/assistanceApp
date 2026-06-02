from app.domain.dtos.AuthDto import LoginDto, AuthResponseDto
from abc import ABC, abstractmethod

class IAuthApplication(ABC):

    @abstractmethod
    def login(self, loginData: LoginDto) -> AuthResponseDto:
        pass

    @abstractmethod
    def intranetAccess(self, userLogin: str, ts: int, sig: str) -> AuthResponseDto:
        pass

    @abstractmethod
    def getCurrentUser(self, wordpressUserId: int) -> AuthResponseDto:
        pass