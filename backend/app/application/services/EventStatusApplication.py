from app.application.interfaces.IEventStatusApplication import IEventStatusApplication
from app.domain.interfaces.IEventStatusRepository import IEventStatusRepository
from app.domain.dtos.EventStatusDto import EventStatusDto
from typing import List

class EventStatusApplication(IEventStatusApplication):

    def __init__(self, eventStatusRepository: IEventStatusRepository):
        self.eventStatusRepository = eventStatusRepository

    def getAll(self) -> List[EventStatusDto]:
        return self.eventStatusRepository.getAll()