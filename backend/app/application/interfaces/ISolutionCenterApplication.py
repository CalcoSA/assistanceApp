from app.domain.dtos.SolutionCenterDto import (SolutionCenterCreateDto, SolutionCenterUpdateDto, SolutionCenterResponseDto)
from abc import ABC, abstractmethod
from typing import List

class ISolutionCenterApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[SolutionCenterResponseDto]:
        pass

    @abstractmethod
    def getById(self, IdSolutionCenter: int) -> SolutionCenterResponseDto:
        pass

    @abstractmethod
    def create(self, solutionCenterData: SolutionCenterCreateDto) -> SolutionCenterResponseDto:
        pass

    @abstractmethod
    def update(self, IdSolutionCenter: int, solutionCenterData: SolutionCenterUpdateDto) -> SolutionCenterResponseDto:
        pass

    @abstractmethod
    def delete(self, IdSolutionCenter: int) -> bool:
        pass