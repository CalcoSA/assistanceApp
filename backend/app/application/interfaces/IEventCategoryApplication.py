from app.domain.dtos.EventCategoryDto import EventCategoryDto
from abc import ABC, abstractmethod
from typing import List

class IEventCategoryApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[EventCategoryDto]:
        pass