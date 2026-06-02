from app.domain.entities.AssistanceReason import AssistanceReason
from abc import ABC, abstractmethod
from typing import List

class IAssistanceReasonRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[AssistanceReason]:
        pass