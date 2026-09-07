from app.application.interfaces.ICompetencyApplication import ICompetencyApplication
from app.domain.interfaces.ICompetencyRepository import ICompetencyRepository
from app.domain.dtos.CompetencyDto import (
    CompetencyCreateDto,
    CompetencyResponseDto,
    CompetencyUpdateDto,
)
from typing import List

class CompetencyApplication(ICompetencyApplication):

    def __init__(self, competencyRepository: ICompetencyRepository):
        self.competencyRepository = competencyRepository

    def getAll(self) -> List[CompetencyResponseDto]:
        return self.competencyRepository.getAll()

    def getById(self, IdCompetency: int) -> CompetencyResponseDto:
        competencyFound = self.competencyRepository.getById(IdCompetency)

        if not competencyFound:
            raise ValueError("La competencia no existe.")

        return competencyFound

    def create(
        self,
        competencyData: CompetencyCreateDto,
    ) -> CompetencyResponseDto:
        nameCompetency = self._normalizeName(competencyData.nameCompetency)
        existingCompetency = self.competencyRepository.getByNameInsensitive(
            nameCompetency
        )

        if existingCompetency:
            raise ValueError("Ya existe una competencia con ese nombre.")

        competencyData.nameCompetency = nameCompetency
        return self.competencyRepository.create(competencyData)

    def update(
        self,
        IdCompetency: int,
        competencyData: CompetencyUpdateDto,
    ) -> CompetencyResponseDto:
        competencyFound = self.competencyRepository.getById(IdCompetency)

        if not competencyFound:
            raise ValueError("La competencia no existe.")

        nameCompetency = self._normalizeName(competencyData.nameCompetency)
        existingCompetency = self.competencyRepository.getByNameInsensitive(
            nameCompetency
        )

        if (
            existingCompetency
            and existingCompetency.IdCompetency != IdCompetency
        ):
            raise ValueError("Ya existe una competencia con ese nombre.")

        competencyData.nameCompetency = nameCompetency

        competencyUpdated = self.competencyRepository.update(
            IdCompetency,
            competencyData,
        )

        if not competencyUpdated:
            raise ValueError("La competencia no existe.")

        return competencyUpdated

    def delete(self, IdCompetency: int) -> bool:
        competencyFound = self.competencyRepository.getById(IdCompetency)

        if not competencyFound:
            raise ValueError("La competencia no existe.")

        if self.competencyRepository.isInUse(IdCompetency):
            raise ValueError(
                "No se puede eliminar la competencia porque está relacionada "
                "con uno o más eventos."
            )

        deleted = self.competencyRepository.delete(IdCompetency)

        if not deleted:
            raise ValueError("La competencia no existe.")

        return deleted

    @staticmethod
    def _normalizeName(nameCompetency: str) -> str:
        normalizedName = " ".join(nameCompetency.split()).upper()

        if not normalizedName:
            raise ValueError("El nombre de la competencia es obligatorio.")

        if len(normalizedName) > 200:
            raise ValueError(
                "El nombre de la competencia no puede superar 200 caracteres."
            )

        return normalizedName
