from app.domain.entities.SpecificTrainingProgram import SpecificTrainingProgram
from abc import ABC, abstractmethod
from typing import List

class ISpecificTrainingProgramApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[SpecificTrainingProgram]:
        pass