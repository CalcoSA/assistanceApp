from app.domain.dtos.CompetencyDto import CompetencyDto
from abc import ABC, abstractmethod
from typing import List

class ICompetencyApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[CompetencyDto]:
        pass