from app.application.interfaces.IEventCategoryApplication import IEventCategoryApplication
from app.domain.interfaces.IEventCategoryRepository import IEventCategoryRepository
from app.domain.dtos.EventCategoryDto import EventCategoryDto
from typing import List

class EventCategoryApplication(IEventCategoryApplication):

    def __init__(self, eventCategoryRepository: IEventCategoryRepository):
        self.eventCategoryRepository = eventCategoryRepository

    def getAll(self) -> List[EventCategoryDto]:
        return self.eventCategoryRepository.getAll()