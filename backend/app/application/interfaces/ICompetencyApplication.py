from app.domain.dtos.CompetencyDto import (
    CompetencyCreateDto,
    CompetencyResponseDto,
    CompetencyUpdateDto,
)
from abc import ABC, abstractmethod
from typing import List

class ICompetencyApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[CompetencyResponseDto]:
        pass

    @abstractmethod
    def getById(self, IdCompetency: int) -> CompetencyResponseDto:
        pass

    @abstractmethod
    def create(
        self,
        competencyData: CompetencyCreateDto,
    ) -> CompetencyResponseDto:
        pass

    @abstractmethod
    def update(
        self,
        IdCompetency: int,
        competencyData: CompetencyUpdateDto,
    ) -> CompetencyResponseDto:
        pass

    @abstractmethod
    def delete(self, IdCompetency: int) -> bool:
        pass
