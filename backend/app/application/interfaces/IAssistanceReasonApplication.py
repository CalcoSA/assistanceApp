from app.domain.dtos.AssistanceReasonDto import AssistanceReasonDto
from abc import ABC, abstractmethod
from typing import List

class IAssistanceReasonApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[AssistanceReasonDto]:
        pass