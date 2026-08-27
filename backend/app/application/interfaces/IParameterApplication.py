from app.domain.dtos.ParameterDto import ParameterCreateDto, ParameterUpdateDto, ParameterResponseDto
from abc import ABC, abstractmethod
from typing import List


class IParameterApplication(ABC):

    @abstractmethod
    def getAll(self) -> List[ParameterResponseDto]:
        pass

    @abstractmethod
    def getById(self, IdParameter: int) -> ParameterResponseDto:
        pass

    @abstractmethod
    def create(self, parameterData: ParameterCreateDto) -> ParameterResponseDto:
        pass

    @abstractmethod
    def update(self, IdParameter: int, parameterData: ParameterUpdateDto) -> ParameterResponseDto:
        pass

    @abstractmethod
    def delete(self, IdParameter: int) -> bool:
        pass
