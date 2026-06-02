from app.domain.dtos.SolutionCenterDto import SolutionCenterCreateDto, SolutionCenterUpdateDto
from app.domain.entities.SolutionCenter import SolutionCenter
from abc import ABC, abstractmethod
from typing import List, Optional

class ISolutionCenterRepository(ABC):

    @abstractmethod
    def getAll(self) -> List[SolutionCenter]:
        pass

    @abstractmethod
    def getById(self, IdSolutionCenter: int) -> Optional[SolutionCenter]:
        pass

    @abstractmethod
    def getByCodeInsensitive(self, codePointSale: str) -> Optional[SolutionCenter]:
        pass

    @abstractmethod
    def create(self, solutionCenterData: SolutionCenterCreateDto) -> SolutionCenter:
        pass

    @abstractmethod
    def update(self, IdSolutionCenter: int, solutionCenterData: SolutionCenterUpdateDto) -> Optional[SolutionCenter]:
        pass

    @abstractmethod
    def delete(self, IdSolutionCenter: int) -> bool:
        pass