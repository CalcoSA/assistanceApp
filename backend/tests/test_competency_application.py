from types import SimpleNamespace

import pytest

from app.application.services.CompetencyApplication import CompetencyApplication
from app.domain.dtos.CompetencyDto import (
    CompetencyCreateDto,
    CompetencyUpdateDto,
)


class FakeCompetencyRepository:
    def __init__(self, competencies=None, usedIds=None):
        self.competencies = {
            competency.IdCompetency: competency
            for competency in (competencies or [])
        }
        self.usedIds = set(usedIds or [])
        self.nextId = max(self.competencies.keys(), default=0) + 1

    def getAll(self):
        return list(self.competencies.values())

    def getById(self, IdCompetency: int):
        return self.competencies.get(IdCompetency)

    def getByNameInsensitive(self, nameCompetency: str):
        normalizedName = nameCompetency.strip().casefold()
        return next(
            (
                competency
                for competency in self.competencies.values()
                if competency.nameCompetency.strip().casefold()
                == normalizedName
            ),
            None,
        )

    def isInUse(self, IdCompetency: int):
        return IdCompetency in self.usedIds

    def create(self, competencyData: CompetencyCreateDto):
        competency = SimpleNamespace(
            IdCompetency=self.nextId,
            nameCompetency=competencyData.nameCompetency,
        )
        self.competencies[self.nextId] = competency
        self.nextId += 1
        return competency

    def update(
        self,
        IdCompetency: int,
        competencyData: CompetencyUpdateDto,
    ):
        competency = self.getById(IdCompetency)
        if not competency:
            return None
        competency.nameCompetency = competencyData.nameCompetency
        return competency

    def delete(self, IdCompetency: int):
        return self.competencies.pop(IdCompetency, None) is not None


def buildCompetency(IdCompetency: int, nameCompetency: str):
    return SimpleNamespace(
        IdCompetency=IdCompetency,
        nameCompetency=nameCompetency,
    )


def test_create_normalizes_competency_name():
    repository = FakeCompetencyRepository()
    service = CompetencyApplication(repository)

    created = service.create(
        CompetencyCreateDto(nameCompetency="  comunicación   efectiva  ")
    )

    assert created.nameCompetency == "COMUNICACIÓN EFECTIVA"


def test_create_rejects_duplicate_name_ignoring_case():
    repository = FakeCompetencyRepository(
        [buildCompetency(1, "COMUNICACIÓN EFECTIVA")]
    )
    service = CompetencyApplication(repository)

    with pytest.raises(ValueError, match="Ya existe una competencia"):
        service.create(
            CompetencyCreateDto(nameCompetency="comunicación efectiva")
        )


def test_update_rejects_name_used_by_another_competency():
    repository = FakeCompetencyRepository(
        [
            buildCompetency(1, "COMUNICACIÓN EFECTIVA"),
            buildCompetency(2, "ADAPTACIÓN AL CAMBIO"),
        ]
    )
    service = CompetencyApplication(repository)

    with pytest.raises(ValueError, match="Ya existe una competencia"):
        service.update(
            2,
            CompetencyUpdateDto(nameCompetency="comunicación efectiva"),
        )


def test_update_rejects_blank_name():
    repository = FakeCompetencyRepository(
        [buildCompetency(1, "COMUNICACIÓN EFECTIVA")]
    )
    service = CompetencyApplication(repository)

    with pytest.raises(ValueError, match="nombre de la competencia es obligatorio"):
        service.update(1, CompetencyUpdateDto(nameCompetency="   "))


def test_delete_rejects_competency_related_to_events():
    repository = FakeCompetencyRepository(
        [buildCompetency(1, "COMUNICACIÓN EFECTIVA")],
        usedIds={1},
    )
    service = CompetencyApplication(repository)

    with pytest.raises(ValueError, match="relacionada con uno o más eventos"):
        service.delete(1)

    assert repository.getById(1) is not None


def test_delete_removes_unused_competency():
    repository = FakeCompetencyRepository(
        [buildCompetency(1, "COMUNICACIÓN EFECTIVA")]
    )
    service = CompetencyApplication(repository)

    assert service.delete(1) is True
    assert repository.getById(1) is None
