from app.domain.entities.EventCategory import EventCategory
from abc import ABC, abstractmethod
from typing import List

class IEventCategoryRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[EventCategory]:
        pass