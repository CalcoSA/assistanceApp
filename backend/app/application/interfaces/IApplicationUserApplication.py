from app.domain.dtos.ApplicationUserDto import ApplicationUserCreateDto, ApplicationUserUpdateDto, ApplicationUserResponseDto
from app.domain.dtos.WordpressUserDto import WordpressUserResponseDto
from abc import ABC, abstractmethod
from typing import List

class IApplicationUserApplication(ABC):

    @abstractmethod
    def searchWordpressUsers(self, search: str) -> List[WordpressUserResponseDto]:
        pass

    @abstractmethod
    def getAll(self) -> List[ApplicationUserResponseDto]:
        pass

    @abstractmethod
    def getById(self, IdApplicationUser: int) -> ApplicationUserResponseDto:
        pass

    @abstractmethod
    def create(self, applicationUserData: ApplicationUserCreateDto) -> ApplicationUserResponseDto:
        pass

    @abstractmethod
    def update(self, IdApplicationUser: int, applicationUserData: ApplicationUserUpdateDto) -> ApplicationUserResponseDto:
        pass

    @abstractmethod
    def delete(self, IdApplicationUser: int) -> bool:
        pass