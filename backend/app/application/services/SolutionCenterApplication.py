from app.domain.dtos.SolutionCenterDto import (SolutionCenterCreateDto, SolutionCenterUpdateDto, SolutionCenterResponseDto)
from app.application.interfaces.ISolutionCenterApplication import ISolutionCenterApplication
from app.domain.interfaces.ISolutionCenterRepository import ISolutionCenterRepository
from app.domain.entities.SolutionCenter import SolutionCenter
from typing import List

class SolutionCenterApplication(ISolutionCenterApplication):

    def __init__(self, solutionCenterRepository: ISolutionCenterRepository):
        self.solutionCenterRepository = solutionCenterRepository

    def getAll(self) -> List[SolutionCenterResponseDto]:
        return self.solutionCenterRepository.getAll()

    def getById(self, IdSolutionCenter: int) -> SolutionCenterResponseDto:
        solutionCenterFound = self.solutionCenterRepository.getById(IdSolutionCenter)

        if not solutionCenterFound:
            raise ValueError("El centro de soluciones no existe.")

        return solutionCenterFound

    def create(self, solutionCenterData: SolutionCenterCreateDto) -> SolutionCenterResponseDto:
        codeSolutionCenter = solutionCenterData.codeSolutionCenter.strip()

        if not codeSolutionCenter:
            raise ValueError("El código del centro de soluciones o punto de venta es requerido.")
        
        nameSolutionCenter = solutionCenterData.nameSolutionCenter.strip()

        if not nameSolutionCenter:
            raise ValueError("El nombre del centro de soluciones o punto de venta es requerido.")
        
        existingSolutionCenter = self.solutionCenterRepository.getByCodeInsensitive(solutionCenterData.codeSolutionCenter)

        if existingSolutionCenter:
            raise ValueError("Ya existe el centro de soluciones o punto de venta.")

        solutionCenterCreated = self.solutionCenterRepository.create(solutionCenterData)
        return solutionCenterCreated

    def update(self, IdSolutionCenter: int, solutionCenterData: SolutionCenterUpdateDto) -> SolutionCenterResponseDto:
        solutionCenterFound = self.solutionCenterRepository.getById(IdSolutionCenter)

        if not solutionCenterFound:
            return None
        
        if solutionCenterData.codeSolutionCenter is not None:
            existingSolutionCenter = self.solutionCenterRepository.getByCodeInsensitive(solutionCenterData.codeSolutionCenter)

            if existingSolutionCenter and existingSolutionCenter.IdSolutionCenter != IdSolutionCenter:
                raise ValueError("Ya existe un centro de soluciones o punto de venta con ese código.")

        solutionCenterUpdated = self.solutionCenterRepository.update(IdSolutionCenter, solutionCenterData)

        if not solutionCenterUpdated:
            raise ValueError("El centro de soluciones no existe.")

        return solutionCenterUpdated

    def delete(self, IdSolutionCenter: int) -> bool:
        deleted = self.solutionCenterRepository.delete(IdSolutionCenter)

        if not deleted:
            raise ValueError("El centro de soluciones no existe.")

        return deleted