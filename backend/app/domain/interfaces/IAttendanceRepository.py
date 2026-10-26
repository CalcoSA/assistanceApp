from app.domain.entities.Attendance import Attendance
from abc import ABC, abstractmethod
from typing import Optional
from typing import Callable
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto


class AttendancePersistenceError(RuntimeError):
    def __init__(self, commitUncertain: bool):
        super().__init__("No fue posible confirmar el registro de asistencia.")
        self.commitUncertain = commitUncertain

class IAttendanceRepository(ABC):

    @abstractmethod
    def registerWithSignature(
        self, IdEvent: int, data: AttendanceRegisterDto,
        ipAddress: str | None, userAgent: str | None,
        saveSignature: Callable[[int], str],
    ) -> tuple[int, int, int, str | None]:
        """Atomically save person, current signature and attendance under row locks."""
        pass

    @abstractmethod
    def getLatestByPerson(self, IdAttendancePerson: int) -> Optional[Attendance]:
        pass

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
