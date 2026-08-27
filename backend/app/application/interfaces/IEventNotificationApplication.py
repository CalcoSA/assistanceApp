from app.domain.dtos.EventDto import EventResponseDto
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EventNotificationResult:
    sent: bool
    message: str


class IEventNotificationApplication(ABC):

    @abstractmethod
    def notifyEventCreated(
        self, event: EventResponseDto
    ) -> EventNotificationResult:
        pass
