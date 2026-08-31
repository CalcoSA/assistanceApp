from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from app.application.services.AttendanceApplication import (
    PublicAttendanceApplication,
)
from app.application.services.EventApplication import EventApplication
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto


class FakeEventRepository:
    def __init__(self, event):
        self.event = event
        self.statusUpdates: list[int] = []
        self.eventUpdates: list[dict] = []

    def getByToken(self, tokenEvent: str):
        return self.event if tokenEvent == "valid-token" else None

    def update(self, IdEvent: int, updateData: dict, topics, competencies):
        self.eventUpdates.append(updateData)

        for fieldName, value in updateData.items():
            setattr(self.event, fieldName, value)

        return self.event

    def setStatus(self, IdEvent: int, IdEventStatus: int):
        self.statusUpdates.append(IdEventStatus)
        self.event.IdEventStatus = IdEventStatus
        self.event.eventStatus.nameEventStatus = (
            "Activo" if IdEventStatus == EventApplication.STATUS_ACTIVE else "Inactivo"
        )
        return self.event


def buildEvent(
    *,
    status: int = EventApplication.STATUS_ACTIVE,
    attendanceEndDateTime: datetime | None = None,
):
    eventDate = date(2026, 8, 31)
    eventEndTime = time(11, 0)

    return SimpleNamespace(
        IdEvent=1,
        dateEvent=eventDate,
        startTimeEvent=time(9, 0),
        endTimeEvent=eventEndTime,
        attendanceStartDateTime=datetime(2026, 8, 31, 8, 0),
        attendanceEndDateTime=(
            attendanceEndDateTime
            if attendanceEndDateTime is not None
            else datetime(2026, 8, 31, 11, 30)
        ),
        IdEventStatus=status,
        eventStatus=SimpleNamespace(
            nameEventStatus=(
                "Activo"
                if status == EventApplication.STATUS_ACTIVE
                else "Inactivo"
            )
        ),
    )


def buildEventApplication(event, now: datetime):
    service = EventApplication.__new__(EventApplication)
    service.eventRepository = FakeEventRepository(event)
    service._currentDateTime = lambda: now
    return service


def buildAttendanceApplication(event, now: datetime):
    service = PublicAttendanceApplication.__new__(PublicAttendanceApplication)
    service.eventRepository = FakeEventRepository(event)
    service._currentDateTime = lambda: now
    return service


def test_attendance_window_remains_open_before_event_start():
    event = buildEvent()
    service = buildAttendanceApplication(
        event,
        datetime(2026, 8, 31, 8, 30),
    )

    assert service._getValidEventByToken("valid-token") is event
    assert service.eventRepository.statusUpdates == []


def test_event_remains_active_at_exact_grace_period_boundary():
    event = buildEvent()
    service = buildEventApplication(
        event,
        datetime(2026, 8, 31, 11, 30),
    )

    synchronizedEvent = service._syncStatusByEndDateTime(event)

    assert synchronizedEvent.IdEventStatus == EventApplication.STATUS_ACTIVE
    assert service.eventRepository.statusUpdates == []


def test_event_is_inactivated_after_grace_period():
    event = buildEvent()
    service = buildEventApplication(
        event,
        datetime(2026, 8, 31, 11, 30) + timedelta(microseconds=1),
    )

    synchronizedEvent = service._syncStatusByEndDateTime(event)

    assert synchronizedEvent.IdEventStatus == EventApplication.STATUS_INACTIVE
    assert service.eventRepository.statusUpdates == [
        EventApplication.STATUS_INACTIVE
    ]


def test_public_form_closes_and_inactivates_event_after_grace_period():
    event = buildEvent()
    service = buildAttendanceApplication(
        event,
        datetime(2026, 8, 31, 11, 31),
    )

    with pytest.raises(ValueError, match="ya no está disponible"):
        service._getValidEventByToken("valid-token")

    assert service.eventRepository.statusUpdates == [
        EventApplication.STATUS_INACTIVE
    ]


def test_legacy_inactive_event_is_reactivated_during_new_grace_period():
    event = buildEvent(
        status=EventApplication.STATUS_INACTIVE,
        attendanceEndDateTime=datetime(2026, 8, 31, 11, 0),
    )
    service = buildAttendanceApplication(
        event,
        datetime(2026, 8, 31, 11, 15),
    )

    assert service._getValidEventByToken("valid-token") is event
    assert event.attendanceEndDateTime == datetime(2026, 8, 31, 11, 30)
    assert service.eventRepository.statusUpdates == [
        EventApplication.STATUS_ACTIVE
    ]


def test_legacy_inactive_event_is_reactivated_before_event_ends():
    event = buildEvent(
        status=EventApplication.STATUS_INACTIVE,
        attendanceEndDateTime=datetime(2026, 8, 31, 11, 0),
    )
    service = buildEventApplication(
        event,
        datetime(2026, 8, 31, 10, 30),
    )

    synchronizedEvent = service._syncStatusByEndDateTime(event)

    assert synchronizedEvent.IdEventStatus == EventApplication.STATUS_ACTIVE
    assert event.attendanceEndDateTime == datetime(2026, 8, 31, 11, 30)
    assert service.eventRepository.statusUpdates == [
        EventApplication.STATUS_ACTIVE
    ]


def test_grace_period_handles_event_end_near_midnight():
    service = EventApplication.__new__(EventApplication)

    assert service._getAttendanceEndDateTime(
        date(2026, 8, 31),
        time(23, 50),
    ) == datetime(2026, 9, 1, 0, 20)


def test_registration_is_allowed_above_scheduled_people():
    event = buildEvent()
    event.scheduledPeopleNumber = 1
    person = SimpleNamespace(
        IdAttendancePerson=7,
        signaturePathAttendancePerson="/uploads/signatures/123/signature_123.png",
    )

    class FakeAttendancePersonRepository:
        def getByDocument(self, documentNumber: str):
            return person

        def update(self, attendancePerson, data, signaturePath):
            return attendancePerson

    class FakeAttendanceRepository:
        def getByEventAndPerson(self, IdEvent: int, IdAttendancePerson: int):
            return None

        def createAndCount(self, *args):
            return SimpleNamespace(IdAttendance=22), 2

    class FakePersonnelTypeRepository:
        def getById(self, IdPersonnelType: int):
            return SimpleNamespace(IdPersonnelType=IdPersonnelType)

    service = buildAttendanceApplication(
        event,
        datetime(2026, 8, 31, 10, 0),
    )
    service.attendancePersonRepository = FakeAttendancePersonRepository()
    service.attendanceRepository = FakeAttendanceRepository()
    service.personnelTypeRepository = FakePersonnelTypeRepository()

    result = service.registerAttendance(
        "valid-token",
        AttendanceRegisterDto(
            documentNumberAttendancePerson="123",
            fullNameAttendancePerson="Persona dos",
            IdPersonnelType=1,
        ),
        "127.0.0.1",
        "pytest",
    )

    assert result.attendedPeopleNumber == 2
    assert result.IdEvent == event.IdEvent
