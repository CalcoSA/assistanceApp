from abc import ABC, abstractmethod
from typing import Callable

from app.domain.entities.TrainingParameter import TrainingParameter


class ITrainingParameterRepository(ABC):
    @abstractmethod
    def appendVersion(self, parameter: TrainingParameter, userLogin: str | None):
        """Append only, inside the caller's transaction and parent lock."""
        pass

    @abstractmethod
    def getVersions(self, IdTrainingParameter: int):
        pass

    @abstractmethod
    def getVersion(self, IdTrainingParameter: int, versionId: int):
        pass

    @abstractmethod
    def getAll(self, isActive: bool | None = None) -> list[TrainingParameter]:
        pass

    @abstractmethod
    def getById(self, IdTrainingParameter: int, *, forUpdate: bool = False) -> TrainingParameter | None:
        pass

    @abstractmethod
    def getByName(self, name: str) -> TrainingParameter | None:
        pass

    @abstractmethod
    def create(self, parameter: TrainingParameter) -> TrainingParameter:
        pass

    @abstractmethod
    def createComplete(
        self, parameter: TrainingParameter, prepare: Callable[[TrainingParameter], None],
    ) -> TrainingParameter:
        """Flush the new aggregate, prepare its document and activation, then commit once."""
        pass

    @abstractmethod
    def update(
        self, IdTrainingParameter: int, applyChanges: Callable[[TrainingParameter], None],
        topics: list[str] | None = None,
    ) -> TrainingParameter:
        """Apply changes under a parent row lock and commit the complete aggregate."""
        pass
