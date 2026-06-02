from app.application.interfaces.ICompetencyApplication import ICompetencyApplication
from app.domain.interfaces.ICompetencyRepository import ICompetencyRepository
from app.domain.dtos.CompetencyDto import CompetencyDto
from typing import List

class CompetencyApplication(ICompetencyApplication):

    def __init__(self, competencyRepository: ICompetencyRepository):
        self.competencyRepository = competencyRepository

    def getAll(self) -> List[CompetencyDto]:
        return self.competencyRepository.getAll()