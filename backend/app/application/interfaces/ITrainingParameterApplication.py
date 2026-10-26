from abc import ABC, abstractmethod

from fastapi import UploadFile

from app.domain.dtos.TrainingParameterDto import (
    TrainingParameterCompleteCreateDto, TrainingParameterCreateDto, TrainingParameterUpdateDto,
)


class ITrainingParameterApplication(ABC):
    @abstractmethod
    def getAll(self, isActive: bool | None = None):
        pass

    @abstractmethod
    def getById(self, IdTrainingParameter: int):
        pass

    @abstractmethod
    def create(self, data: TrainingParameterCreateDto):
        pass

    @abstractmethod
    def createComplete(self, data: TrainingParameterCompleteCreateDto, file: UploadFile, userLogin: str | None = None):
        pass

    @abstractmethod
    def update(self, IdTrainingParameter: int, data: TrainingParameterUpdateDto):
        pass

    @abstractmethod
    def uploadPensum(self, IdTrainingParameter: int, file: UploadFile, userLogin: str | None = None):
        pass

    @abstractmethod
    def updatePensum(self, IdTrainingParameter: int, file: UploadFile, userLogin: str | None = None):
        pass

    @abstractmethod
    def getPensumReadUrl(self, IdTrainingParameter: int, download: bool = False) -> str:
        pass

    @abstractmethod
    def getVersions(self, IdTrainingParameter: int):
        pass

    @abstractmethod
    def getVersionReadUrl(self, IdTrainingParameter: int, versionId: int, download: bool = False):
        pass
