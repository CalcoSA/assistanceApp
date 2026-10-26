from datetime import date, datetime, time

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.application.services.ReportApplication import ReportApplication
from app.domain.entities.AssistanceReason import AssistanceReason
from app.domain.entities.Attendance import Attendance
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.entities.Event import Event
from app.domain.entities.EventStatus import EventStatus
from app.domain.entities.PersonnelType import PersonnelType
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.ReportRepository import ReportRepository


@pytest.fixture
def repository():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def register_time_functions(connection, _):
        # Support the production MySQL duration expression in isolated SQLite.
        def timediff(end, start):
            return (
                datetime.combine(date.min, time.fromisoformat(end))
                - datetime.combine(date.min, time.fromisoformat(start))
            ).total_seconds()

        connection.create_function("timediff", 2, timediff)
        connection.create_function("time_to_sec", 1, lambda seconds: seconds)

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            EventStatus(IdEventStatus=1, nameEventStatus="Activo"),
            AssistanceReason(IdAssistanceReason=1, nameAssistanceReason=" Transversales "),
            AssistanceReason(IdAssistanceReason=2, nameAssistanceReason="Otro"),
            PersonnelType(IdPersonnelType=1, namePersonnelType=" Administrativo "),
            PersonnelType(IdPersonnelType=2, namePersonnelType="Operaciones"),
            *[
                AttendancePerson(
                    IdAttendancePerson=person_id,
                    documentNumberAttendancePerson=str(person_id),
                    fullNameAttendancePerson=f"Persona {person_id}",
                )
                for person_id in range(1, 5)
            ],
        ])
        db.commit()
        yield ReportRepository(db)
    engine.dispose()


def add_event(repository, event_id, *, induction=False, reason=2,
              end=time(10), attendees=(), event_date=date(2020, 1, 15)):
    repository.db.add(Event(
        IdEvent=event_id,
        titleEvent=f"Evento {event_id}",
        dateEvent=event_date,
        startTimeEvent=time(9),
        endTimeEvent=end,
        IdEventStatus=1,
        IdAssistanceReason=reason,
        isNewStaffInductionEvent=induction,
        attendanceStartDateTime=datetime.combine(event_date, time(9)),
        attendanceEndDateTime=datetime.combine(event_date, end),
        tokenEvent=f"report-test-{event_id}",
        createdByUserLogin="tester",
    ))
    repository.db.flush()
    repository.db.add_all([
        Attendance(IdEvent=event_id, IdAttendancePerson=person_id, IdPersonnelType=personnel_type)
        for person_id, personnel_type in attendees
    ])
    repository.db.commit()


def test_consolidates_sources_without_counting_overlap_twice(repository):
    add_event(repository, 1, induction=True, end=time(11), attendees=[(1, 1), (2, 2)])
    add_event(repository, 2, reason=1, end=time(10, 30), attendees=[(1, 1), (3, 2)])
    add_event(repository, 3, induction=True, reason=1, end=time(9, 45), attendees=[(1, 1), (2, 2)])
    add_event(repository, 4, end=time(14), attendees=[(4, 1)])
    add_event(repository, 5, induction=True, attendees=[(2, 2)])
    add_event(repository, 6, induction=True, end=time(11))

    result = ReportApplication(repository).getTransversalTrainingReport(None, None)

    assert result.totalTransversalTrainingHours == 6.5
    assert result.totalTransversalTrainingPeople == 3
    assert {
        row.documentNumberAttendancePerson: row.totalTransversalTrainingHours
        for row in result.byCollaborator
    } == {"1": 4.25, "2": 0.75, "3": 1.5}
    assert repository.getNewStaffInductionSummary(None, None) == {
        "totalNewStaffInductionHours": 5.75,
        "totalNewStaffInductionPeople": 2,
    }


@pytest.mark.parametrize("induction, reason, personnel_type, expected_hours", [
    (True, None, 1, 1.25),  # Historic administrative induction without a reason.
    (True, 2, 1, 1.25),
    (True, 1, 1, 1.25),  # Same attendance qualifies for both sources.
    (False, 1, 2, 1.25),
    (True, None, 2, 0),
    (False, 2, 1, 0),
])
def test_keeps_source_criteria_for_historical_records(
    repository, induction, reason, personnel_type, expected_hours,
):
    add_event(repository, 1, induction=induction, reason=reason,
              end=time(10, 15), attendees=[(1, personnel_type)])

    result = ReportApplication(repository).getTransversalTrainingReport(None, None)

    assert result.totalTransversalTrainingHours == expected_hours
    assert result.totalTransversalTrainingPeople == (1 if expected_hours else 0)
    assert sum(row.totalTransversalTrainingHours for row in result.byCollaborator) == expected_hours
    assert len(result.byCollaborator) == result.totalTransversalTrainingPeople


@pytest.mark.parametrize("date_from, date_to, expected_hours, expected_people", [
    (date(2020, 1, 15), date(2020, 1, 15), 3, 2),
    (None, date(2020, 1, 15), 4, 3),
    (date(2020, 1, 15), None, 4, 3),
    (date(2030, 1, 1), date(2030, 1, 31), 0, 0),
])
def test_keeps_date_filters_for_both_sources(repository, date_from, date_to, expected_hours, expected_people):
    add_event(repository, 1, induction=True, attendees=[(1, 1)], event_date=date(2020, 1, 14))
    add_event(repository, 2, induction=True, end=time(11), attendees=[(2, 1)])
    add_event(repository, 3, reason=1, attendees=[(3, 2)])
    add_event(repository, 4, reason=1, attendees=[(4, 2)], event_date=date(2020, 1, 16))

    result = ReportApplication(repository).getTransversalTrainingReport(date_from, date_to)

    assert result.totalTransversalTrainingHours == expected_hours
    assert result.totalTransversalTrainingPeople == expected_people
    assert sum(row.totalTransversalTrainingHours for row in result.byCollaborator) == expected_hours
    assert len(result.byCollaborator) == expected_people
