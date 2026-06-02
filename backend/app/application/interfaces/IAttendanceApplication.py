from app.domain.dtos.AttendanceDto import (PublicEventResponseDto, AttendancePersonResponseDto, AttendanceRegisterDto, AttendanceRegisterResponseDto,)
from abc import ABC, abstractmethod
from typing import Optional

class IPublicAttendanceApplication(ABC):

    @abstractmethod
    def getEventByToken(self, tokenEvent: str) -> PublicEventResponseDto:
        pass

    @abstractmethod
    def getPersonByDocument(self, documentNumber: str) -> Optional[AttendancePersonResponseDto]:
        pass

    @abstractmethod
    def registerAttendance(self, tokenEvent: str, data: AttendanceRegisterDto, ipAddress: str | None, userAgent: str | None) -> AttendanceRegisterResponseDto:
        pass