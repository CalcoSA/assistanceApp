from app.domain.dtos.EventStatusDto import EventStatusDto
from abc import ABC, abstractmethod
from typing import List

class IEventStatusApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[EventStatusDto]:
        pass