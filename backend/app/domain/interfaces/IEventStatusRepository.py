from app.domain.entities.EventStatus import EventStatus
from abc import ABC, abstractmethod
from typing import List

class IEventStatusRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[EventStatus]:
        pass