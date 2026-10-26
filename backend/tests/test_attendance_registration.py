from datetime import date, datetime, time
import base64
from io import BytesIO
import importlib
import re
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from PIL import Image
from pydantic import SecretStr
import pytest
from sqlalchemy import create_engine, event as sqlalchemyEvent, update
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.application.services.AttendanceApplication import PublicAttendanceApplication
from app.application.services.EventApplication import EventApplication
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.entities.Event import Event
from app.domain.interfaces.IAttendanceRepository import AttendancePersistenceError
from app.infrastructure.db.config import settings
from app.infrastructure.db.base import Base
from app.infrastructure.db import catalogSeed
from app.domain.entities.Attendance import Attendance
from app.domain.entities.PersonnelType import PersonnelType
from app.infrastructure.repositories.AttendanceRepository import AttendanceRepository
from app.infrastructure.repositories.AttendancePersonRepository import AttendancePersonRepository
from app.infrastructure.repositories.EventRepository import EventRepository
from app.infrastructure.repositories.PersonnelTypeRepository import PersonnelTypeRepository
from app.infrastructure.storage.GcsStorage import GcsStorage, GcsStorageError


attendanceModule = importlib.import_module("app.application.services.AttendanceApplication")
eventModule = importlib.import_module("app.application.services.EventApplication")
imageBuffer = BytesIO()
Image.new("RGB", (2, 2), "black").save(imageBuffer, format="PNG")
PNG = imageBuffer.getvalue()
SIGNATURE = "data:image/png;base64," + base64.b64encode(PNG).decode()
OLD_PATH = "signatures/7/" + "a" * 32 + ".png"


@pytest.fixture
def storage(monkeypatch):
    configuration = SimpleNamespace(
        GCS_ENVIRONMENT="development", GCS_AUTH_MODE="hmac", GCS_BUCKET="calco-storage",
        GCS_PREFIX="assistanceApp_dev/", GCS_PROJECT_ID="calco-sa-508817",
        GCS_ENDPOINT="https://storage.googleapis.com", GCS_TIMEOUT_SECONDS=30,
        GCS_HMAC_ACCESS_KEY=SecretStr("unit-access"), GCS_HMAC_SECRET_KEY=SecretStr("unit-secret"),
        GCS_SIGNING_SERVICE_ACCOUNT_EMAIL=None,
    )
    def noNetwork(request):
        pytest.fail("Real GCS requests are forbidden in signature tests")
    with httpx.Client(transport=httpx.MockTransport(noNetwork)) as client:
        instance = GcsStorage(configuration, httpClient=client)
        instance.upload = Mock(return_value=123)
        instance.delete = Mock(return_value=True)
        instance.download = Mock(return_value=PNG)
        instance.close = Mock()
        monkeypatch.setattr(attendanceModule, "GcsStorage", lambda: instance)
        monkeypatch.setattr(eventModule, "GcsStorage", lambda: instance)
        yield instance


@pytest.fixture
def service(storage):
    person = SimpleNamespace(
        IdAttendancePerson=7,
        documentNumberAttendancePerson="123",
        fullNameAttendancePerson="Persona de prueba",
        positionAttendancePerson="Analista",
        IdSolutionCenter=2,
        phoneAttendancePerson="3001234567",
        signaturePathAttendancePerson="/uploads/signatures/123/old.png",
    )
    people = Mock()
    people.getByDocument.return_value = person
    people.update.return_value = person
    people.create.return_value = person
    attendances = Mock()
    attendances.getByEventAndPerson.return_value = None
    attendances.getLatestByPerson.return_value = SimpleNamespace(IdPersonnelType=1)
    def persist(eventId, data, ip, userAgent, saveSignature):
        saveSignature(7)
        return 22, 7, 1, person.signaturePathAttendancePerson
    attendances.registerWithSignature.side_effect = persist
    personnelTypes = Mock()
    personnelTypes.getById.return_value = SimpleNamespace(
        IdPersonnelType=1, namePersonnelType="Administrativo"
    )
    application = PublicAttendanceApplication(Mock(), people, attendances, personnelTypes)
    application._getValidEventByToken = Mock(return_value=SimpleNamespace(IdEvent=3))
    return application


def registration(**overrides):
    return AttendanceRegisterDto(**{
        "documentNumberAttendancePerson": "123",
        "fullNameAttendancePerson": "Persona de prueba",
        "IdPersonnelType": 1,
        "signatureBase64": SIGNATURE,
        **overrides,
    })


@pytest.mark.parametrize("signature", [None, "", "   "])
@pytest.mark.parametrize("existingPerson", [True, False])
def test_registration_requires_new_signature_even_with_saved_signature(service, storage, signature, existingPerson):
    if not existingPerson:
        service.attendancePersonRepository.getByDocument.return_value = None

    with pytest.raises(ValueError, match="Debe registrar la firma"):
        service.registerAttendance("token", registration(signatureBase64=signature), None, None)

    storage.upload.assert_not_called()
    service.attendancePersonRepository.create.assert_not_called()
    service.attendancePersonRepository.update.assert_not_called()
    service.attendanceRepository.registerWithSignature.assert_not_called()


@pytest.mark.parametrize("personnelTypeId, name", [(0, None), (999, None), (3, " No APLICA ")])
def test_registration_rejects_placeholder_unknown_and_legacy_personnel_type(service, storage, personnelTypeId, name):
    service.personnelTypeRepository.getById.return_value = (
        SimpleNamespace(IdPersonnelType=personnelTypeId, namePersonnelType=name) if name else None
    )

    with pytest.raises(ValueError, match="tipo de personal"):
        service.registerAttendance("token", registration(IdPersonnelType=personnelTypeId), None, None)

    storage.upload.assert_not_called()
    service.attendanceRepository.registerWithSignature.assert_not_called()


@pytest.mark.parametrize("existingPerson", [True, False])
def test_registration_accepts_external_personnel_with_new_signature(service, storage, existingPerson):
    service.personnelTypeRepository.getById.return_value = SimpleNamespace(
        IdPersonnelType=7, namePersonnelType="Externo"
    )
    if not existingPerson:
        service.attendancePersonRepository.getByDocument.return_value = None
    data = registration(IdPersonnelType=7)

    result = service.registerAttendance("token", data, None, None)

    assert result.IdAttendance == 22
    path, content, mime = storage.upload.call_args.args
    assert re.fullmatch(r"signatures/7/[0-9a-f]{32}\.png", path)
    assert content == PNG and mime == "image/png"
    service.attendancePersonRepository.update.assert_not_called()
    service.attendancePersonRepository.create.assert_not_called()
    service.attendanceRepository.registerWithSignature.assert_called_once()
    assert service.attendanceRepository.registerWithSignature.call_args.args[:4] == (3, data, None, None)
    storage.delete.assert_not_called()  # Never remove a historical local signature.


@pytest.mark.parametrize("name, expectedId", [("Administrativo", 1), ("Externo", 1), (" No APLICA ", None)])
def test_lookup_preserves_person_data_and_valid_type_without_returning_saved_signature(service, name, expectedId):
    service.personnelTypeRepository.getById.return_value.namePersonnelType = name

    result = service.getPersonByDocument(" 123 ").model_dump()

    assert result == {
        "IdAttendancePerson": 7,
        "documentNumberAttendancePerson": "123",
        "fullNameAttendancePerson": "Persona de prueba",
        "positionAttendancePerson": "Analista",
        "IdSolutionCenter": 2,
        "IdPersonnelType": expectedId,
        "phoneAttendancePerson": "3001234567",
    }
    service.attendancePersonRepository.getByDocument.assert_called_once_with("123")


def test_lookup_without_previous_attendance_requires_personnel_selection(service):
    service.attendanceRepository.getLatestByPerson.return_value = None
    assert service.getPersonByDocument("123").IdPersonnelType is None


def test_lookup_unknown_person_returns_none(service):
    service.attendancePersonRepository.getByDocument.return_value = None
    assert service.getPersonByDocument("456") is None


@pytest.mark.parametrize("signature", ["data:image/png;base64,bmV3", "%%%", "data:image/jpeg;base64," + SIGNATURE.split(",")[1]])
def test_signature_rejects_invalid_png_before_storage(service, storage, signature):
    with pytest.raises(ValueError, match="PNG"):
        service.registerAttendance("token", registration(signatureBase64=signature), None, None)
    storage.upload.assert_not_called()
    service.attendanceRepository.registerWithSignature.assert_not_called()


def test_registration_duplicate_does_not_replace_signature(service, storage):
    service.attendanceRepository.getByEventAndPerson.return_value = SimpleNamespace(IdAttendance=1)
    with pytest.raises(ValueError, match="ya registró"):
        service.registerAttendance("token", registration(), None, None)
    storage.upload.assert_not_called()
    storage.delete.assert_not_called()


@pytest.fixture
def persistedService(database, storage):
    for eventId in (3, 4):
        database.add(Event(
            IdEvent=eventId, titleEvent="Synthetic event", dateEvent=date(2100, 1, 1),
            startTimeEvent=time(9), endTimeEvent=time(10), IdEventStatus=1,
            attendanceStartDateTime=datetime(2100, 1, 1, 9),
            attendanceEndDateTime=datetime(2100, 1, 1, 10, 30),
            attendedPeopleNumber=0, tokenEvent=f"test-{eventId}", createdByUserLogin="owner",
        ))
    database.add(AttendancePerson(
        IdAttendancePerson=7, documentNumberAttendancePerson="123",
        fullNameAttendancePerson="Previous name",
        signaturePathAttendancePerson=storage.objectReference(OLD_PATH),
    ))
    database.add(PersonnelType(IdPersonnelType=1, namePersonnelType="Administrativo"))
    database.commit()
    application = PublicAttendanceApplication(
        Mock(), AttendancePersonRepository(database), AttendanceRepository(database),
        PersonnelTypeRepository(database),
    )
    application._getValidEventByToken = lambda token: database.get(Event, int(token))
    return application


def test_signature_upload_commit_and_delete_in_order(persistedService, database, storage):
    original = storage.objectReference(OLD_PATH)
    def upload(path, content, mime):
        assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == original
        assert database.query(Attendance).count() == 0
        assert content == PNG and mime == "image/png"
        return 123
    storage.upload.side_effect = upload
    def remove(path, **kwargs):
        assert path == OLD_PATH
        assert database.query(Attendance).count() == 1
        assert database.get(AttendancePerson, 7).signaturePathAttendancePerson != original
        return True
    storage.delete.side_effect = remove
    result = persistedService.registerAttendance("3", registration(), "127.0.0.1", None)
    assert result.attendedPeopleNumber == 1
    path = storage.upload.call_args.args[0]
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(path)
    assert database.get(Event, 3).attendedPeopleNumber == 1
    storage.delete.assert_called_once_with(OLD_PATH)


def test_signature_new_person_uses_internal_id(persistedService, database, storage):
    result = persistedService.registerAttendance("3", registration(documentNumberAttendancePerson="synthetic-doc"), None, None)
    path = storage.upload.call_args.args[0]
    assert path.startswith(f"signatures/{result.IdAttendancePerson}/")
    assert "synthetic-doc" not in path
    assert database.get(AttendancePerson, result.IdAttendancePerson).signaturePathAttendancePerson == storage.objectReference(path)
    storage.delete.assert_not_called()


@pytest.mark.parametrize("newPerson", [False, True])
def test_signature_gcs_failure_rolls_back_everything(persistedService, database, storage, newPerson):
    storage.upload.side_effect = GcsStorageError("Simulated upload failure")
    data = registration(documentNumberAttendancePerson="new-person" if newPerson else "123")
    with pytest.raises(GcsStorageError):
        persistedService.registerAttendance("3", data, None, None)
    assert database.query(Attendance).count() == 0
    assert database.query(AttendancePerson).count() == 1
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(OLD_PATH)
    assert database.get(Event, 3).attendedPeopleNumber == 0
    storage.delete.assert_not_called()


def test_signature_database_failure_cleans_only_uploaded_generation(persistedService, database, storage):
    def rejectAttendance(session, context, instances):
        if any(isinstance(row, Attendance) for row in session.new):
            raise SQLAlchemyError("Simulated flush failure")
    sqlalchemyEvent.listen(database, "before_flush", rejectAttendance)
    with pytest.raises(AttendancePersistenceError) as error:
        persistedService.registerAttendance("3", registration(), None, None)
    assert error.value.commitUncertain is False
    assert database.query(Attendance).count() == 0
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(OLD_PATH)
    assert database.get(Event, 3).attendedPeopleNumber == 0
    storage.delete.assert_called_once_with(storage.upload.call_args.args[0], expectedGeneration=123)


@pytest.mark.parametrize("committed", [False, True])
def test_signature_uncertain_commit_preserves_both_objects(persistedService, database, storage, monkeypatch, committed):
    commit = database.commit
    def lostAcknowledgement():
        if committed:
            commit()
        raise RuntimeError("Simulated lost acknowledgement")
    monkeypatch.setattr(database, "commit", lostAcknowledgement)
    with pytest.raises(AttendancePersistenceError) as error:
        persistedService.registerAttendance("3", registration(), None, None)
    assert error.value.commitUncertain is True
    assert database.query(Attendance).count() == int(committed)
    currentPath = storage.upload.call_args.args[0] if committed else OLD_PATH
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(currentPath)
    storage.delete.assert_not_called()


def test_signature_cleanup_and_close_failure_do_not_undo_committed_attendance(persistedService, database, storage, caplog):
    storage.delete.side_effect = GcsStorageError("sensitive transport details")
    storage.close.side_effect = RuntimeError("sensitive transport details")
    result = persistedService.registerAttendance("3", registration(), None, None)
    assert result.IdAttendance == database.query(Attendance).one().IdAttendance
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(storage.upload.call_args.args[0])
    assert "pendiente de limpieza" in caplog.text
    assert "sensitive transport details" not in caplog.text


def test_signature_interleaved_post_commit_cleanup_keeps_latest_person_signature(persistedService, database, storage):
    objects = {OLD_PATH}
    def upload(path, content, mime):
        assert path not in objects
        objects.add(path)
        return 123
    def remove(path, **kwargs):
        if path == OLD_PATH:
            # Request B commits while request A has not yet retired its old file.
            persistedService.registerAttendance("4", registration(), None, None)
        objects.remove(path)
        return True
    storage.upload.side_effect = upload
    storage.delete.side_effect = remove
    persistedService.registerAttendance("3", registration(), None, None)
    latestPath = storage.upload.call_args_list[-1].args[0]
    assert objects == {latestPath}
    assert database.query(Attendance).count() == 2
    for attendance in database.query(Attendance).all():
        assert attendance.attendancePerson.signaturePathAttendancePerson == storage.objectReference(latestPath)
    assert database.get(Event, 3).attendedPeopleNumber == 1
    assert database.get(Event, 4).attendedPeopleNumber == 1


def test_signature_locks_refresh_stale_person_and_recheck_duplicates(persistedService, database, storage):
    person = database.get(AttendancePerson, 7)
    currentPath = "signatures/7/" + "b" * 32 + ".png"
    database.execute(update(AttendancePerson).where(AttendancePerson.IdAttendancePerson == 7).values(
        signaturePathAttendancePerson=storage.objectReference(currentPath),
    ).execution_options(synchronize_session=False))
    assert person.signaturePathAttendancePerson == storage.objectReference(OLD_PATH)
    lockedQueries = []
    def recordLocks(state):
        sql = str(state.statement.compile(dialect=mysql.dialect()))
        if "FOR UPDATE" in sql:
            lockedQueries.append(sql)
    sqlalchemyEvent.listen(database, "do_orm_execute", recordLocks)
    persistedService.registerAttendance("3", registration(), None, None)
    storage.delete.assert_called_once_with(currentPath)
    assert len(lockedQueries) == 3  # Event, person and event attendees use current locking reads.
    assert "AttendancePerson" in lockedQueries[1]
    before = storage.upload.call_count
    with pytest.raises(ValueError, match="ya registró"):
        persistedService.attendanceRepository.registerWithSignature(3, registration(), None, None, storage.upload)
    assert storage.upload.call_count == before


def test_signature_retries_first_person_lock_race_before_upload(persistedService, database, storage, monkeypatch):
    query = database.query
    calls = 0
    def lockRace(*entities, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OperationalError("synthetic", {}, Exception(1213, "deadlock"))
        return query(*entities, **kwargs)
    monkeypatch.setattr(database, "query", lockRace)
    result = persistedService.attendanceRepository.registerWithSignature(
        3, registration(), None, None, lambda personId: "synthetic-signature-reference",
    )
    assert result[1] == 7
    assert database.query(Attendance).count() == 1


@pytest.mark.parametrize("reference", [
    "gs://calco-storage/assistanceApp_qa/signatures/7/" + "a" * 32 + ".png",
    "gs://calco-storage/assistanceApp_dev/signatures/8/" + "a" * 32 + ".png",
    "gs://calco-storage/assistanceApp_dev/pensum/file.png",
])
def test_signature_cleanup_never_deletes_outside_managed_person(service, storage, reference):
    service.attendancePersonRepository.getByDocument.return_value.signaturePathAttendancePerson = reference
    service.registerAttendance("token", registration(), None, None)
    storage.delete.assert_not_called()


@pytest.fixture
def signatureView(persistedService, database):
    database.add(Attendance(IdAttendance=22, IdAttendancePerson=7, IdEvent=3, IdPersonnelType=1))
    database.commit()
    return EventApplication(EventRepository(database))


def test_signature_view_uses_authorized_resource_without_mutating_reference(signatureView, database, storage):
    response = signatureView.getAttendancesByEventScope(3, "owner", [])
    assert response[0].attendancePerson.signaturePathAttendancePerson == "/events/3/attendances/22/signature"
    assert database.get(AttendancePerson, 7).signaturePathAttendancePerson == storage.objectReference(OLD_PATH)
    assert signatureView.getAttendanceSignatureByUserScope(3, 22, "owner", []) == PNG
    storage.download.assert_called_once_with(OLD_PATH)


@pytest.mark.parametrize("user, roles", [("owner", []), ("admin", ["administrador"])])
def test_signature_authorized_view_supports_owner_and_admin(signatureView, storage, user, roles):
    assert signatureView.getAttendanceSignatureByUserScope(3, 22, user, roles) == PNG


def test_signature_view_rejects_other_users_and_attendance_of_another_event(signatureView, storage):
    with pytest.raises(PermissionError):
        signatureView.getAttendanceSignatureByUserScope(3, 22, "other", [])
    with pytest.raises(ValueError):
        signatureView.getAttendanceSignatureByUserScope(4, 22, "owner", [])
    storage.download.assert_not_called()


@pytest.mark.parametrize("reference", [
    "gs://calco-storage/assistanceApp_qa/signatures/7/test.png",
    "gs://other-bucket/assistanceApp_dev/signatures/7/test.png",
    "gs://calco-storage/assistanceApp_dev/signatures/8/test.png",
    "gs://calco-storage/assistanceApp_dev/pensum/test.png",
    "gs://calco-storage/assistanceApp_dev/signatures/7/../8/test.png",
])
def test_signature_view_rejects_other_prefixes_and_persons(signatureView, database, storage, reference):
    database.get(AttendancePerson, 7).signaturePathAttendancePerson = reference
    database.commit()
    with pytest.raises(ValueError):
        signatureView.getAttendanceSignatureByUserScope(3, 22, "owner", [])
    storage.download.assert_not_called()


def test_signature_local_remains_readable_and_untouched_after_replacement(signatureView, persistedService, database, storage, tmp_path, monkeypatch):
    root = tmp_path / "uploads"
    oldFile = root / "signatures" / "123" / "old.png"
    oldFile.parent.mkdir(parents=True)
    oldFile.write_bytes(PNG)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(root))
    database.get(AttendancePerson, 7).signaturePathAttendancePerson = "/uploads/signatures/123/old.png"
    database.commit()
    assert signatureView.getAttendanceSignatureByUserScope(3, 22, "owner", []) == PNG
    storage.download.assert_not_called()
    persistedService.registerAttendance("4", registration(), None, None)
    assert oldFile.read_bytes() == PNG
    assert list(root.rglob("*.png")) == [oldFile]
    storage.delete.assert_not_called()
    # The old attendance displays the person's current signature, not a per-event copy.
    assert signatureView.getAttendanceSignatureByUserScope(3, 22, "owner", []) == PNG
    storage.download.assert_called_once_with(storage.upload.call_args.args[0])


@pytest.mark.parametrize("reference", ["/uploads/signatures/../../private.png", "/uploads/pensum/file.png", "C:/private.png"])
def test_signature_local_view_cannot_read_arbitrary_files(signatureView, database, storage, tmp_path, monkeypatch, reference):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    (tmp_path / "private.png").write_bytes(PNG)
    database.get(AttendancePerson, 7).signaturePathAttendancePerson = reference
    database.commit()
    with pytest.raises(ValueError):
        signatureView.getAttendanceSignatureByUserScope(3, 22, "owner", [])
    storage.download.assert_not_called()


def test_signature_http_access_requires_auth_and_never_exposes_storage_errors(signatureView, storage):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.eventController import router, getCurrentAuthContext, getEventApplication
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[getEventApplication] = lambda: signatureView
    with TestClient(application) as client:
        assert client.get("/events/3/attendances/22/signature").status_code in (401, 403)
        application.dependency_overrides[getCurrentAuthContext] = lambda: {"userLogin": "owner", "roles": []}
        response = client.get("/events/3/attendances/22/signature")
        assert response.status_code == 200 and response.content == PNG
        assert response.headers["cache-control"] == "private, no-store"
        assert response.headers["content-type"] == "image/png"
        storage.download.side_effect = GcsStorageError("secret transport details")
        response = client.get("/events/3/attendances/22/signature")
        assert response.status_code == 503 and "secret" not in response.text
        storage.download.side_effect = FileNotFoundError()
        assert client.get("/events/3/attendances/22/signature").status_code == 404
        application.dependency_overrides[getCurrentAuthContext] = lambda: {"userLogin": "other", "roles": []}
        assert client.get("/events/3/attendances/22/signature").status_code == 403


@pytest.fixture
def database():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def test_catalog_adds_external_once_and_excludes_legacy_option_without_changing_history(database, monkeypatch):
    database.add(PersonnelType(IdPersonnelType=3, namePersonnelType="No aplica"))
    database.commit()
    monkeypatch.setattr(catalogSeed, "SessionLocal", lambda: database)

    catalogSeed.seedRequiredCatalogs()
    catalogSeed.seedRequiredCatalogs()

    repository = PersonnelTypeRepository(database)
    assert [item.namePersonnelType for item in repository.getAll()] == ["Externo"]
    assert repository.getById(3).namePersonnelType == "No aplica"


def test_lookup_uses_most_recent_attendance_with_id_as_tiebreaker(database):
    database.add_all([
        Attendance(IdAttendance=1, IdAttendancePerson=7, IdEvent=1, IdPersonnelType=1, createdAt=datetime(2026, 1, 1)),
        Attendance(IdAttendance=2, IdAttendancePerson=7, IdEvent=2, IdPersonnelType=2, createdAt=datetime(2026, 1, 2)),
        Attendance(IdAttendance=3, IdAttendancePerson=7, IdEvent=3, IdPersonnelType=3, createdAt=datetime(2026, 1, 2)),
        Attendance(IdAttendance=4, IdAttendancePerson=8, IdEvent=4, IdPersonnelType=4, createdAt=datetime(2026, 1, 3)),
    ])
    database.commit()

    repository = AttendanceRepository(database)
    assert repository.getLatestByPerson(7).IdPersonnelType == 3
    assert repository.getLatestByPerson(9) is None
