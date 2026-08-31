from app.domain.entities.Attendance import Attendance
from abc import ABC, abstractmethod
from typing import Optional

class IAttendanceRepository(ABC):

    @abstractmethod
    def getByEventAndPerson(self, IdEvent: int, IdAttendancePerson: int) -> Optional[Attendance]:
        pass

    @abstractmethod
    def create(self, IdEvent: int, IdAttendancePerson: int, IdPersonnelType: int, ipAddress: str | None, userAgent: str | None) -> Attendance:
        pass

    @abstractmethod
    def createAndCount(self, IdEvent: int, IdAttendancePerson: int, IdPersonnelType: int, ipAddress: str | None, userAgent: str | None) -> tuple[Attendance, int]:
        pass

    @abstractmethod
    def countByEvent(self, IdEvent: int) -> int:
        pass
