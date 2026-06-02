from app.application.interfaces.ISpecificTrainingProgramApplication import ISpecificTrainingProgramApplication
from app.domain.interfaces.ISpecificTrainingProgramRepository import ISpecificTrainingProgramRepository
from app.domain.dtos.SpecificTrainingProgramDto import SpecificTrainingProgramDto
from typing import List

class SpecificTrainingProgramApplication(ISpecificTrainingProgramApplication):

    def __init__(self, specificTrainingProgramRepository: ISpecificTrainingProgramRepository):
        self.specificTrainingProgramRepository = specificTrainingProgramRepository

    def getAll(self) -> List[SpecificTrainingProgramDto]:
        return self.specificTrainingProgramRepository.getAll()