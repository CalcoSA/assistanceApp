from app.domain.dtos.OnlyOfficeDto import OnlyOfficePreviewResponseDto
from abc import ABC, abstractmethod


class IOnlyOfficeApplication(ABC):

    @abstractmethod
    def createTemporaryPensumPreview(
        self,
        file,
        userLogin: str,
    ) -> OnlyOfficePreviewResponseDto:
        pass

    @abstractmethod
    def createEventPensumPreview(
        self,
        IdEvent: int,
        userLogin: str,
        roles: list[str],
    ) -> OnlyOfficePreviewResponseDto:
        pass

    @abstractmethod
    def resolveFileAccess(self, accessToken: str) -> tuple[str, str, str]:
        pass

