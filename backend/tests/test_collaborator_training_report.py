from datetime import date
from types import SimpleNamespace

import pytest

from app.application.services.ReportApplication import ReportApplication


class FakeCollaboratorHistoryRepository:
    def __init__(self, rows):
        self.rows = rows
        self.receivedArguments = None

    def getCollaboratorTrainingHistory(self, search, dateFrom, dateTo):
        self.receivedArguments = (search, dateFrom, dateTo)
        return self.rows


def historyRow(
    attendancePersonId,
    documentNumber,
    fullName,
    eventId,
    title,
    trainingDate,
    trainingCenter,
    trainingHours,
    personCenter="TECNOLOGÍA",
):
    return SimpleNamespace(
        IdAttendancePerson=attendancePersonId,
        documentNumberAttendancePerson=documentNumber,
        fullNameAttendancePerson=fullName,
        personSolutionCenterName=personCenter,
        IdEvent=eventId,
        titleEvent=title,
        dateEvent=trainingDate,
        trainingSolutionCenterName=trainingCenter,
        trainingHours=trainingHours,
    )


def test_collaborator_history_deduplicates_the_same_person_and_event():
    duplicate = historyRow(
        10,
        "1000653613",
        "JUAN PABLO ZAPATA",
        7,
        "CAPACITACIÓN DE SERVICIO",
        date(2026, 9, 2),
        "CALIDAD",
        1.5,
    )
    repository = FakeCollaboratorHistoryRepository(
        [
            duplicate,
            duplicate,
            historyRow(
                10,
                "1000653613",
                "JUAN PABLO ZAPATA",
                8,
                "CAPACITACIÓN DE PRODUCTO",
                date(2026, 9, 3),
                "TECNOLOGÍA",
                0.75,
            ),
        ]
    )

    result = ReportApplication(repository).getCollaboratorTrainingReport(
        "  Juan   Zapata  ",
        date(2026, 9, 1),
        date(2026, 9, 30),
    )

    assert repository.receivedArguments == (
        "Juan Zapata",
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert len(result.collaborators) == 1
    collaborator = result.collaborators[0]
    assert collaborator.totalTrainings == 2
    assert collaborator.totalTrainingHours == 2.25
    assert [training.IdEvent for training in collaborator.trainings] == [7, 8]
    assert {
        item.nameSolutionCenter: (
            item.totalTrainings,
            item.totalTrainingHours,
        )
        for item in collaborator.byTrainingSolutionCenter
    } == {
        "CALIDAD": (1, 1.5),
        "TECNOLOGÍA": (1, 0.75),
    }


def test_collaborator_history_keeps_different_attendees_separate():
    repository = FakeCollaboratorHistoryRepository(
        [
            historyRow(
                20,
                "100",
                "ANA PÉREZ",
                11,
                "EVENTO A",
                date(2026, 9, 1),
                "SST",
                1,
            ),
            historyRow(
                21,
                "200",
                "ANA MARÍA PÉREZ",
                11,
                "EVENTO A",
                date(2026, 9, 1),
                "SST",
                1,
            ),
        ]
    )

    result = ReportApplication(repository).getCollaboratorTrainingReport(
        "Ana Pérez",
        None,
        None,
    )

    assert len(result.collaborators) == 2
    assert {item.documentNumberAttendancePerson for item in result.collaborators} == {
        "100",
        "200",
    }


def test_collaborator_history_rejects_an_inverted_date_range():
    repository = FakeCollaboratorHistoryRepository([])

    with pytest.raises(ValueError, match="fecha inicial"):
        ReportApplication(repository).getCollaboratorTrainingReport(
            "1000653613",
            date(2026, 9, 30),
            date(2026, 9, 1),
        )

    assert repository.receivedArguments is None
