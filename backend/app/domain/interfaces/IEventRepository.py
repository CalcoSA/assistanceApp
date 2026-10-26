from app.domain.entities.Event import Event
from abc import ABC, abstractmethod
from typing import List, Optional
from typing import Callable
from datetime import date

class IEventRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[Event]:
        pass

    @abstractmethod
    def getByCreatedBy(self, createdByUserLogin: str) -> List[Event]:
        pass

    @abstractmethod
    def getById(self, IdEvent: int) -> Optional[Event]:
        pass

    @abstractmethod
    def getByToken(self, tokenEvent: str) -> Optional[Event]:
        pass

    @abstractmethod
    def getAttendancesByEvent(self, IdEvent: int):
        pass

    @abstractmethod
    def getAttendanceByEvent(self, IdEvent: int, IdAttendance: int):
        pass

    @abstractmethod
    def getPaginated(self, page: int, pageSize: int, status: Optional[str], createdByUserLogin: Optional[str],):
        pass

    @abstractmethod
    def create(self, eventData: Event, topics: Optional[List[str]], competencies: List[int]) -> Event:
        pass

    @abstractmethod
    def update(self, IdEvent: int, updateData: dict, topics, competencies) -> Optional[Event]:
        pass

    @abstractmethod
    def cancel(self, IdEvent: int, observationsEvent: str) -> Optional[Event]:
        pass

    @abstractmethod
    def getQrCleanupCandidates(self, throughDate: date, afterId: int, limit: int = 100) -> list[int]:
        pass

    @abstractmethod
    def cleanupQr(self, IdEvent: int, removeIfExpired: Callable[[Event], bool]) -> None:
        """Recheck eligibility and remove the file while holding the event row lock."""
        pass

    @abstractmethod
    def delete(self, IdEvent: int) -> bool:
        pass

    @abstractmethod
    def setStatus(self, IdEvent: int, IdEventStatus: int) -> Optional[Event]:
        pass

    @abstractmethod
    def countAttendances(self, IdEvent: int) -> int:
        pass

    @abstractmethod
    def setAttendedPeopleNumber(self, IdEvent: int, attendedPeopleNumber: int) -> Optional[Event]:
        pass

    @abstractmethod
    def updatePensum(self, IdEvent: int, pensumOriginalNameEvent: str, pensumPathEvent: str, pensumMimeTypeEvent: str, pensumSizeEvent: int, updatedByUserLogin: str) -> Optional[Event]:
        pass
