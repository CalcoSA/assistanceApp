from app.domain.entities.Competency import Competency
from abc import ABC, abstractmethod
from typing import List

class ICompetencyRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[Competency]:
        pass