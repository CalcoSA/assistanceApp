from datetime import date, datetime, time, timedelta
import asyncio
import importlib
from pathlib import Path
import threading
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sqlalchemyEvent, update
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.eventController import (
    getCurrentAuthContext,
    getEventApplication,
    router,
)
from app.application.services.EventApplication import EventApplication
from app.application.services.EventApplication import eventQrLifespan
from app.domain.dtos.EventDto import EventCancelDto
from app.domain.entities.Event import Event
from app.domain.entities.EventStatus import EventStatus
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.EventRepository import EventRepository


@pytest.fixture
def service(tmp_path):
    # Only this isolated, in-memory database is used; no application DB or email.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            EventStatus(IdEventStatus=1, nameEventStatus="Activo"),
            EventStatus(IdEventStatus=2, nameEventStatus="Inactivo"),
            EventStatus(IdEventStatus=3, nameEventStatus="Cancelado"),
            Event(
                IdEvent=1,
                titleEvent="Evento histórico",
                dateEvent=date(2026, 10, 8),
                startTimeEvent=time(9),
                endTimeEvent=time(10),
                IdEventStatus=1,
                observationsEvent="Evento dirigido al equipo comercial",
                attendanceStartDateTime=datetime(2026, 10, 8, 9),
                attendanceEndDateTime=datetime(2026, 10, 8, 10, 30),
                tokenEvent="cancellation-test-token",
                publicUrlEvent="https://example.test/attendance/cancellation-test-token",
                eventPlace="Medellín",
                createdByUserLogin="tester",
            ),
        ])
        db.commit()
        application = EventApplication(EventRepository(db))
        application.uploadDir = str(tmp_path / "uploads")
        application._currentDateTime = lambda: datetime(2026, 10, 7, 8)
        yield application
    engine.dispose()


@pytest.fixture
def client(service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[getEventApplication] = lambda: service
    app.dependency_overrides[getCurrentAuthContext] = lambda: {
        "userLogin": "tester", "roles": ["formador"],
    }
    with TestClient(app) as test_client:
        yield test_client


def cancel(service, reason="Se canceló por indisponibilidad del facilitador"):
    return service.cancel(
        1, EventCancelDto(cancellationReason=reason), "tester", ["formador"],
    )


def reload_event(service):
    service.eventRepository.db.expire_all()
    return service.getByIdByUserScope(1, "tester", ["formador"])


@pytest.mark.parametrize("observations, expected_prefix", [
    (None, ""), ("", ""), (" \t\n ", ""),
    ("Evento dirigido al equipo comercial", "Evento dirigido al equipo comercial\n"),
    ("  Observación original.\nSegunda línea  ", "  Observación original.\nSegunda línea\n"),
    ("Observación existente \n\r\n\t ", "Observación existente\n"),
])
def test_cancel_appends_reason_preserving_existing_content_and_other_event_data(service, observations, expected_prefix):
    repository = service.eventRepository
    repository.getById(1).observationsEvent = observations
    repository.db.commit()
    before = reload_event(service).model_dump()

    cancelled = cancel(service, "  Se canceló por indisponibilidad del facilitador  ")
    reloaded = reload_event(service)
    expected = expected_prefix + "Motivo de cancelación: Se canceló por indisponibilidad del facilitador"

    for response in (cancelled, reloaded):
        assert response.IdEventStatus == 3
        assert response.eventStatus.nameEventStatus == "Cancelado"
        assert response.observationsEvent == expected
        expected_data = {
            **before,
            "IdEventStatus": 3,
            "eventStatus": {"IdEventStatus": 3, "nameEventStatus": "Cancelado"},
            "observationsEvent": expected,
        }
        assert response.model_dump() == expected_data


def test_repeated_cancellation_cannot_duplicate_observations(service):
    cancelled = cancel(service)

    with pytest.raises(ValueError, match="ya se encuentra cancelado"):
        cancel(service)

    assert reload_event(service).observationsEvent == cancelled.observationsEvent


@pytest.mark.parametrize("reason", ["", " ", "\n\t", " \u00a0 "])
def test_empty_reason_is_rejected_before_any_event_changes(service, reason):
    before = reload_event(service).model_dump()

    with pytest.raises(ValueError, match="motivo de cancelación es obligatorio"):
        cancel(service, reason)

    assert reload_event(service).model_dump() == before


@pytest.mark.parametrize("payload, expected_status", [
    ({}, 422),
    ({"cancellationReason": None}, 422),
    ({"cancellationReason": []}, 422),
    ({"cancellationReason": ""}, 400),
    ({"cancellationReason": " \n\t "}, 400),
])
def test_cancel_endpoint_rejects_invalid_reason_without_changes(client, service, payload, expected_status):
    before = reload_event(service).model_dump()

    response = client.patch("/events/1/cancel", json=payload)

    assert response.status_code == expected_status
    assert reload_event(service).model_dump() == before


def test_cancel_endpoint_persists_reason_and_returns_it_in_existing_observations(client):
    response = client.patch("/events/1/cancel", json={"cancellationReason": " Cambio de agenda "})

    assert response.status_code == 200
    assert response.json()["isSuccess"] is True
    event = response.json()["result"]
    assert event["IdEventStatus"] == 3
    assert event["observationsEvent"] == (
        "Evento dirigido al equipo comercial\nMotivo de cancelación: Cambio de agenda"
    )
    consultation = client.get("/events/1")
    assert consultation.status_code == 200
    assert consultation.json()["result"] == event


@pytest.mark.parametrize("status, error", [(2, "evento inactivo"), (3, "ya se encuentra cancelado")])
def test_existing_state_restrictions_remain_unchanged(service, status, error):
    service.eventRepository.setStatus(1, status)
    before = reload_event(service).model_dump()

    with pytest.raises(ValueError, match=error):
        cancel(service)

    assert reload_event(service).model_dump() == before


def test_other_user_cannot_cancel_or_change_observations(service):
    before = reload_event(service).model_dump()

    with pytest.raises(PermissionError, match="No tiene permisos"):
        service.cancel(1, EventCancelDto(cancellationReason="Motivo"), "other-user", ["formador"])

    assert reload_event(service).model_dump() == before


def test_started_event_with_attendees_still_cannot_be_cancelled(service):
    service._currentDateTime = lambda: datetime(2026, 10, 8, 9, 30)
    service.eventRepository.countAttendances = Mock(return_value=1)
    before = reload_event(service).model_dump()

    with pytest.raises(ValueError, match="ya inició y tiene asistentes registrados"):
        cancel(service)

    assert reload_event(service).model_dump() == before


def test_started_event_without_attendees_can_still_be_cancelled(service):
    service._currentDateTime = lambda: datetime(2026, 10, 8, 9, 30)

    assert cancel(service).IdEventStatus == 3


def test_failed_persistence_rolls_back_status_and_observations_together(service, monkeypatch):
    path = storeQr(service)
    before = reload_event(service).model_dump()
    monkeypatch.setattr(service.eventRepository.db, "commit", Mock(side_effect=SQLAlchemyError("failure")))

    with pytest.raises(Exception, match="Error al cancelar el evento"):
        cancel(service)

    assert reload_event(service).model_dump() == before
    assert path.is_file()


def storeQr(service, eventId=1):
    event = service.eventRepository.getById(eventId)
    event.qrPathEvent = service._generateQr(event.tokenEvent, event.publicUrlEvent)
    service.eventRepository.db.commit()
    return Path(service.uploadDir) / "qrs" / f"qr_event_{event.tokenEvent}.png"


def test_qr_generation_keeps_original_url_and_local_png(service, monkeypatch):
    module = importlib.import_module("app.application.services.EventApplication")
    make = Mock(wraps=module.qrcode.make)
    monkeypatch.setattr(module.qrcode, "make", make)
    path = storeQr(service)
    event = service.eventRepository.getById(1)
    make.assert_called_once_with(event.publicUrlEvent)
    assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert service.getQrInfo(1, "tester", []).qrPathEvent == event.qrPathEvent


def test_qr_cancel_removes_file_only_after_cancel_commit_and_keeps_history(service, client, monkeypatch):
    path = storeQr(service)
    db = service.eventRepository.db
    committed = []
    commit = db.commit
    def recordCommit():
        commit()
        committed.append(True)
    monkeypatch.setattr(db, "commit", recordCommit)
    unlink = Path.unlink
    def verifyOrder(file, **kwargs):
        assert committed
        assert db.get(Event, 1).IdEventStatus == 3
        return unlink(file, **kwargs)
    monkeypatch.setattr(Path, "unlink", verifyOrder)
    response = cancel(service, "Motivo conservado")
    assert not path.exists()
    assert response.qrPathEvent is None
    event = service.eventRepository.getById(1)
    assert event.qrPathEvent is None
    assert event.tokenEvent == "cancellation-test-token"
    assert event.publicUrlEvent.endswith("/cancellation-test-token")
    assert event.observationsEvent.endswith("Motivo de cancelación: Motivo conservado")
    assert client.get("/events/1").status_code == 200
    assert client.get("/events/1/attendances").status_code == 200
    assert client.get("/events/1/qr").json()["result"]["qrPathEvent"] is None
    assert client.get("/events/1/qr/download").status_code == 404


def test_qr_delete_failure_preserves_retry_reference_without_failing_cancel(service, client, monkeypatch, caplog):
    path = storeQr(service)
    reference = service.eventRepository.getById(1).qrPathEvent
    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", Mock(side_effect=PermissionError("file busy")))
        assert cancel(service).IdEventStatus == 3
        assert path.is_file()
        assert service.eventRepository.getById(1).qrPathEvent == reference
        assert client.get("/events/1").json()["result"]["qrPathEvent"] is None
        assert client.get("/events/1/qr/download").status_code == 404
    assert "Limpieza de QR pendiente" in caplog.text
    service.cleanupExpiredQrs()
    service.cleanupExpiredQrs()
    assert not path.exists()
    assert service.eventRepository.getById(1).qrPathEvent is None


def test_qr_null_persistence_failure_is_reconciled_on_next_pass(service, monkeypatch):
    path = storeQr(service)
    db = service.eventRepository.db
    reference = service.eventRepository.getById(1).qrPathEvent
    commit = db.commit
    calls = 0
    def failCleanupCommit():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SQLAlchemyError("cleanup commit failure")
        commit()
    with monkeypatch.context() as patch:
        patch.setattr(db, "commit", failCleanupCommit)
        assert cancel(service).IdEventStatus == 3
    assert not path.exists()
    assert service.eventRepository.getById(1).qrPathEvent == reference
    service.cleanupExpiredQrs()
    assert service.eventRepository.getById(1).qrPathEvent is None


@pytest.mark.parametrize("status", [1, 2])
@pytest.mark.parametrize("offset, removed", [(-1, False), (0, False), (1, True)])
def test_qr_cleanup_respects_exact_grace_boundary_and_legacy_inactive_status(service, status, offset, removed):
    path = storeQr(service)
    event = service.eventRepository.getById(1)
    event.IdEventStatus = status
    event.attendanceEndDateTime = datetime(2026, 10, 8, 10)  # Legacy stored deadline.
    service.eventRepository.db.commit()
    service._currentDateTime = lambda: datetime(2026, 10, 8, 10, 30) + timedelta(microseconds=offset)
    service.cleanupExpiredQrs()
    assert path.exists() is not removed
    assert (service.eventRepository.getById(1).qrPathEvent is None) is removed


def test_qr_midnight_grace_and_future_events_are_preserved(service):
    path = storeQr(service)
    event = service.eventRepository.getById(1)
    event.endTimeEvent = time(23, 50)
    service.eventRepository.db.commit()
    service.cleanupExpiredQrs()  # Event has not started yet.
    assert path.exists()
    service._currentDateTime = lambda: datetime(2026, 10, 9, 0, 20)
    service.cleanupExpiredQrs()
    assert path.exists()
    service._currentDateTime = lambda: datetime(2026, 10, 9, 0, 20, 1)
    service.cleanupExpiredQrs()
    assert not path.exists()


def test_qr_missing_files_are_idempotent_and_never_regenerated(service, monkeypatch):
    path = storeQr(service)
    path.unlink()
    module = importlib.import_module("app.application.services.EventApplication")
    make = Mock(side_effect=AssertionError("QR must not be regenerated"))
    monkeypatch.setattr(module.qrcode, "make", make)
    assert service.getQrInfo(1, "tester", []).qrPathEvent is None
    service._currentDateTime = lambda: datetime(2026, 10, 8, 10, 31)
    service.cleanupExpiredQrs()
    service.cleanupExpiredQrs()
    assert service.getQrInfo(1, "tester", []).qrPathEvent is None
    assert service.eventRepository.getById(1).qrPathEvent is None
    make.assert_not_called()


@pytest.mark.parametrize("reference", [
    "/uploads/qrs/qr_event_other-token.png", "/uploads/qrs/../keep.png",
    "/uploads/signatures/keep.png", "/uploads/pensum/keep.png",
    "gs://bucket/qr_event_cancellation-test-token.png",
])
def test_qr_cleanup_rejects_non_owned_paths_and_leaves_other_files(service, reference):
    path = storeQr(service)
    other = path.parent / "qr_event_other-token.png"
    other.write_bytes(b"unrelated")
    keep = path.parent.parent / "keep.png"
    keep.write_bytes(b"unrelated")
    event = service.eventRepository.getById(1)
    event.qrPathEvent = reference
    service.eventRepository.db.commit()
    cancel(service)
    service.cleanupExpiredQrs()
    assert path.is_file() and other.read_bytes() == b"unrelated" and keep.read_bytes() == b"unrelated"
    assert service.eventRepository.getById(1).qrPathEvent == reference


def test_qr_cleanup_rejects_symlinked_files(service, monkeypatch):
    path = storeQr(service)
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda candidate: candidate == path or original(candidate))
    cancel(service)
    assert path.is_file()
    assert service.eventRepository.getById(1).qrPathEvent is not None


def test_qr_cleanup_refreshes_event_under_mysql_lock_before_checking_expiry(service):
    path = storeQr(service)
    db = service.eventRepository.db
    event = db.get(Event, 1)
    service._currentDateTime = lambda: datetime(2026, 10, 8, 10, 31)
    # Model a candidate that was rescheduled after discovery, leaving a stale ORM object.
    db.execute(update(Event).where(Event.IdEvent == 1).values(dateEvent=date(2026, 10, 9)).execution_options(synchronize_session=False))
    assert event.dateEvent == date(2026, 10, 8)
    queries = []
    def recordQuery(state):
        queries.append(str(state.statement.compile(dialect=mysql.dialect())))
    sqlalchemyEvent.listen(db, "do_orm_execute", recordQuery)
    service._cleanupEventQr(1)
    assert any("FOR UPDATE" in query for query in queries)
    assert path.is_file()
    assert db.get(Event, 1).dateEvent == date(2026, 10, 9)


def test_qr_download_handles_disappearance_before_read(service, client, monkeypatch):
    storeQr(service)
    assert client.get("/events/1/qr/download").status_code == 200
    monkeypatch.setattr(Path, "read_bytes", Mock(side_effect=FileNotFoundError()))
    assert client.get("/events/1/qr/download").status_code == 404


def test_qr_periodic_cleanup_runs_at_startup_retries_and_stops(monkeypatch):
    module = importlib.import_module("app.application.services.EventApplication")
    calls = []
    def cleanup():
        calls.append(threading.get_ident())
        if len(calls) == 1:
            raise RuntimeError("database temporarily unavailable")
    monkeypatch.setattr(module, "cleanupEventQrs", cleanup)
    assert module.QR_CLEANUP_INTERVAL_SECONDS == 300
    monkeypatch.setattr(module, "QR_CLEANUP_INTERVAL_SECONDS", 0.01)
    async def run():
        async with eventQrLifespan(FastAPI()):
            assert len(calls) == 1
            tasks = [task for task in asyncio.all_tasks() if task.get_name() == "event-qr-cleanup"]
            assert len(tasks) == 1
            for _ in range(100):
                if len(calls) >= 2:
                    break
                await asyncio.sleep(0.01)
            assert len(calls) >= 2
        assert tasks[0].done()
        stoppedAt = len(calls)
        await asyncio.sleep(0.03)
        assert len(calls) == stoppedAt
    asyncio.run(run())
    assert all(thread != threading.get_ident() for thread in calls)


def test_qr_shutdown_waits_for_cleanup_in_progress(monkeypatch):
    module = importlib.import_module("app.application.services.EventApplication")
    entered, release, completed = threading.Event(), threading.Event(), threading.Event()
    calls = []
    def cleanup():
        calls.append(True)
        if len(calls) > 1:
            entered.set()
            assert release.wait(5)
            completed.set()
    monkeypatch.setattr(module, "cleanupEventQrs", cleanup)
    monkeypatch.setattr(module, "QR_CLEANUP_INTERVAL_SECONDS", 0.01)
    async def run():
        lifespan = eventQrLifespan(FastAPI())
        await lifespan.__aenter__()
        assert await asyncio.to_thread(entered.wait, 5)
        shutdown = asyncio.create_task(lifespan.__aexit__(None, None, None))
        try:
            await asyncio.sleep(0.01)
            assert not shutdown.done()
        finally:
            release.set()
        await asyncio.wait_for(shutdown, 5)
        assert completed.is_set()
    asyncio.run(run())
