from app.domain.entities.SpecificTrainingProgram import SpecificTrainingProgram
from abc import ABC, abstractmethod
from typing import List

class ISpecificTrainingProgramRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[SpecificTrainingProgram]:
        pass