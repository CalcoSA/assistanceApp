from app.domain.dtos.EventDto import (EventCreateDto, EventQrResponseDto, EventResponseDto, EventUpdateDto,)
from abc import ABC, abstractmethod
from typing import List, Optional

class IEventApplication(ABC):

    @abstractmethod
    def getAllByUserScope(self, userLogin: str, roles: list[str]) -> List[EventResponseDto]:
        pass

    @abstractmethod
    def getByIdByUserScope(self, IdEvent: int, userLogin: str, roles: list[str]) -> EventResponseDto:
        pass

    @abstractmethod
    def getAttendancesByEventScope(self, IdEvent: int, userLogin: str, roles: list[str]):
        pass

    @abstractmethod
    def getPaginatedByUserScope(self, page: int, pageSize: int, status: Optional[str], userLogin: str, roles: list[str],):
        pass

    @abstractmethod
    def create(self, eventData: EventCreateDto, userLogin: str, roles: list[str]) -> EventResponseDto:
        pass

    @abstractmethod
    def update(self, IdEvent: int, eventData: EventUpdateDto, userLogin: str, roles: list[str]) -> EventResponseDto:
        pass

    @abstractmethod
    def cancel(self, IdEvent: int, userLogin: str, roles: list[str]) -> EventResponseDto:
        pass

    @abstractmethod
    def delete(self, IdEvent: int, userLogin: str, roles: list[str]) -> bool:
        pass

    @abstractmethod
    def getQrInfo(self, IdEvent: int, userLogin: str, roles: list[str]) -> EventQrResponseDto:
        pass

    @abstractmethod
    def uploadPensum(self, IdEvent: int, file, userLogin: str, roles: list[str]) -> EventResponseDto:
        pass