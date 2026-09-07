from app.domain.dtos.CompetencyDto import CompetencyCreateDto, CompetencyUpdateDto
from app.domain.entities.Competency import Competency
from abc import ABC, abstractmethod
from typing import List, Optional

class ICompetencyRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[Competency]:
        pass

    @abstractmethod
    def getById(self, IdCompetency: int) -> Optional[Competency]:
        pass

    @abstractmethod
    def getByNameInsensitive(self, nameCompetency: str) -> Optional[Competency]:
        pass

    @abstractmethod
    def isInUse(self, IdCompetency: int) -> bool:
        pass

    @abstractmethod
    def create(self, competencyData: CompetencyCreateDto) -> Competency:
        pass

    @abstractmethod
    def update(
        self,
        IdCompetency: int,
        competencyData: CompetencyUpdateDto,
    ) -> Optional[Competency]:
        pass

    @abstractmethod
    def delete(self, IdCompetency: int) -> bool:
        pass
