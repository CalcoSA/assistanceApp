from app.domain.entities.PersonnelType import PersonnelType
from abc import ABC, abstractmethod
from typing import Optional

class IPersonnelTypeRepository(ABC):

    @abstractmethod
    def getAll(self) -> list[PersonnelType]:
        pass

    @abstractmethod
    def getById(self, IdPersonnelType: int) -> Optional[PersonnelType]:
        pass