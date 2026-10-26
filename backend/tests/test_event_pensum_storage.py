from datetime import date, datetime, time
from io import BytesIO
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.datastructures import Headers
from sqlalchemy.exc import IntegrityError

from app.api.eventController import getCurrentAuthContext, getEventApplication, router
from app.application.services.EventApplication import EventApplication
from app.application.services.OnlyOfficeApplication import OnlyOfficeApplication
from app.infrastructure.db.config import settings
from app.infrastructure.storage.GcsStorage import GcsStorage, GcsStorageError
from app.api.authController import getCurrentPayload
from app.api.trainingParameterController import (
    getTrainingParameterApplication, router as trainingParameterRouter,
)
from app.application.services.TrainingParameterApplication import TrainingParameterApplication
from app.domain.dtos.EventDto import EventCreateDto, EventUpdateDto
from app.domain.dtos.TrainingParameterDto import TrainingParameterCreateDto, TrainingParameterUpdateDto
from app.domain.entities.TrainingParameter import TrainingParameter
from app.domain.entities.ParameterTopic import ParameterTopic
from app.domain.entities.TrainingParameterVersion import TrainingParameterVersion
from app.domain.dtos.TrainingParameterDto import TrainingParameterCompleteCreateDto
from app.application.services.PensumHistoryApplication import PensumHistoryApplication
from app.infrastructure.repositories.PensumHistoryRepository import PensumHistoryRepository
from app.api.pensumHistoryController import router as historyRouter, historyPermission, getPensumHistoryApplication
from app.domain.entities.Event import Event
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.TrainingParameterRepository import TrainingParameterRepository
from app.infrastructure.repositories.EventRepository import EventRepository


eventModule = importlib.import_module("app.application.services.EventApplication")
officeModule = importlib.import_module("app.application.services.OnlyOfficeApplication")
trainingModule = importlib.import_module("app.application.services.TrainingParameterApplication")


@pytest.fixture
def storage(monkeypatch):
    configuration = SimpleNamespace(
        GCS_ENVIRONMENT="development", GCS_AUTH_MODE="hmac", GCS_BUCKET="calco-storage",
        GCS_PREFIX="assistanceApp_dev/", GCS_PROJECT_ID="calco-sa-508817",
        GCS_ENDPOINT="https://storage.googleapis.com", GCS_TIMEOUT_SECONDS=30,
        GCS_HMAC_ACCESS_KEY=SecretStr("unit-access"),
        GCS_HMAC_SECRET_KEY=SecretStr("unit-secret"), GCS_SIGNING_SERVICE_ACCOUNT_EMAIL=None,
    )
    def noNetwork(request):
        pytest.fail("No real GCS requests are allowed in these tests")

    with httpx.Client(transport=httpx.MockTransport(noNetwork)) as client:
        instance = GcsStorage(configuration, httpClient=client)
        # Keep the real reference validation and V4 URL generation; only I/O is mocked.
        instance.upload = Mock(return_value=123)
        instance.delete = Mock(return_value=True)
        instance.exists = Mock(return_value=True)
        monkeypatch.setattr(eventModule, "GcsStorage", lambda: instance)
        monkeypatch.setattr(officeModule, "GcsStorage", lambda: instance)
        monkeypatch.setattr(trainingModule, "GcsStorage", lambda: instance)
        yield instance


@pytest.fixture
def service(storage, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "ONLYOFFICE_TEMP_DIR", str(tmp_path / "private"))
    monkeypatch.setattr(settings, "ONLYOFFICE_JWT_SECRET", "onlyoffice-test-" * 4)
    monkeypatch.setattr(settings, "ONLYOFFICE_PUBLIC_URL", "https://office.test")
    monkeypatch.setattr(settings, "ONLYOFFICE_STORAGE_BASE_URL", "https://backend.test")
    event = SimpleNamespace(
        IdEvent=7, titleEvent="Evento", dateEvent=date(2100, 1, 1),
        startTimeEvent=time(9), endTimeEvent=time(10), IdEventStatus=1,
        eventStatus=SimpleNamespace(IdEventStatus=1, nameEventStatus="Activo"),
        attendanceStartDateTime=datetime(2100, 1, 1, 9),
        attendanceEndDateTime=datetime(2100, 1, 1, 10, 30),
        tokenEvent="test-event", createdByUserLogin="tester",
        facilitatorNameEvent=None, facilitatorCompanyEvent=None,
        secondFacilitatorNameEvent=None, secondFacilitatorCompanyEvent=None,
        thirdFacilitatorNameEvent=None, thirdFacilitatorCompanyEvent=None,
        pensumPathEvent=None, pensumOriginalNameEvent=None,
        pensumMimeTypeEvent=None, pensumSizeEvent=None,
    )
    repository = Mock()
    repository.getById.return_value = event

    def update(**values):
        for key, value in values.items():
            setattr(event, key, value)
        return event

    repository.updatePensum.side_effect = update
    return EventApplication(repository)


def upload(service, name="Plan académico.pdf", mime="application/pdf", content=b"synthetic document"):
    return service.uploadPensum(
        7, UploadFile(filename=name, file=BytesIO(content), headers=Headers({"content-type": mime})),
        "tester", [],
    )


def installOldGcsPensum(service, storage):
    oldPath = "pensum/7/pensum_event_7_" + "a" * 32 + ".docx"
    service.eventRepository.getById.return_value.pensumPathEvent = storage.objectReference(oldPath)
    return oldPath


@pytest.mark.parametrize("name, mime", [
    ("Plan académico.pdf", "application/pdf"),
    ("Plan.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("Plan.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
])
def test_new_pensum_stores_permanent_reference_metadata_and_no_local_copy(service, storage, name, mime):
    result = upload(service, name, mime)
    relativePath, content, contentType = storage.upload.call_args.args
    assert relativePath.startswith("pensum/7/pensum_event_7_")
    assert relativePath.endswith(Path(name).suffix)
    assert content == b"synthetic document" and contentType == mime
    event = service.eventRepository.getById.return_value
    assert event.pensumPathEvent == storage.objectReference(relativePath)
    assert result.pensumPathEvent == event.pensumPathEvent
    assert "?" not in result.pensumPathEvent
    assert result.pensumOriginalNameEvent == name
    assert result.pensumMimeTypeEvent == mime
    assert result.pensumSizeEvent == len(content)
    assert not Path("uploads/pensum").exists()
    storage.delete.assert_not_called()


def test_replacing_local_pensum_never_removes_historical_file(service, storage):
    oldFile = Path("uploads/pensum/7/old.docx")
    oldFile.parent.mkdir(parents=True)
    oldFile.write_bytes(b"historical")
    service.eventRepository.getById.return_value.pensumPathEvent = "/uploads/pensum/7/old.docx"
    upload(service)
    assert oldFile.read_bytes() == b"historical"
    assert list(oldFile.parent.iterdir()) == [oldFile]
    storage.delete.assert_not_called()


def test_gcs_failure_never_changes_db_or_removes_previous_pensum(service, storage):
    oldPath = installOldGcsPensum(service, storage)
    storage.upload.side_effect = GcsStorageError("Upload failed")
    with pytest.raises(GcsStorageError):
        upload(service)
    service.eventRepository.updatePensum.assert_not_called()
    assert service.eventRepository.getById.return_value.pensumPathEvent == storage.objectReference(oldPath)
    storage.delete.assert_not_called()


def test_db_error_preserves_old_and_new_pensum_for_recovery(service, storage):
    oldPath = installOldGcsPensum(service, storage)
    service.eventRepository.updatePensum.side_effect = RuntimeError("DB rollback")
    with pytest.raises(RuntimeError, match="DB rollback"):
        upload(service)
    storage.delete.assert_not_called()
    assert service.eventRepository.getById.return_value.pensumPathEvent == storage.objectReference(oldPath)


def test_event_disappearing_before_db_update_removes_only_new_generation(service, storage):
    installOldGcsPensum(service, storage)
    service.eventRepository.updatePensum.side_effect = None
    service.eventRepository.updatePensum.return_value = None
    with pytest.raises(ValueError, match="El evento no existe"):
        upload(service)
    storage.delete.assert_called_once_with(storage.upload.call_args.args[0], expectedGeneration=123)


def test_error_after_committed_update_never_deletes_referenced_new_object(service, storage):
    installOldGcsPensum(service, storage)
    event = service.eventRepository.getById.return_value

    def committedButRefreshFailed(**values):
        event.pensumPathEvent = values["pensumPathEvent"]
        raise RuntimeError("Refresh failed after commit")

    service.eventRepository.updatePensum.side_effect = committedButRefreshFailed
    with pytest.raises(RuntimeError, match="Refresh failed"):
        upload(service)
    assert event.pensumPathEvent == storage.objectReference(storage.upload.call_args.args[0])
    storage.delete.assert_not_called()


def test_uncertain_db_outcome_preserves_both_objects(service, storage):
    installOldGcsPensum(service, storage)
    event = service.eventRepository.getById.return_value
    service.eventRepository.getById.side_effect = [event, RuntimeError("DB unavailable")]
    service.eventRepository.updatePensum.side_effect = RuntimeError("Commit outcome unknown")
    with pytest.raises(RuntimeError, match="Commit outcome unknown"):
        upload(service)
    storage.delete.assert_not_called()


def test_successful_replacement_removes_old_gcs_only_after_db_update(service, storage):
    oldPath = installOldGcsPensum(service, storage)
    event = service.eventRepository.getById.return_value

    def safeDelete(path, **kwargs):
        assert path == oldPath
        assert event.pensumPathEvent != storage.objectReference(oldPath)
        assert event.pensumPathEvent == storage.objectReference(storage.upload.call_args.args[0])
        return True

    storage.delete.side_effect = safeDelete
    upload(service)
    storage.delete.assert_called_once_with(oldPath)


def test_old_object_cleanup_failure_does_not_undo_successful_replacement(service, storage):
    installOldGcsPensum(service, storage)
    storage.delete.side_effect = GcsStorageError("Delete failed")
    result = upload(service)
    assert result.pensumPathEvent == storage.objectReference(storage.upload.call_args.args[0])


@pytest.mark.parametrize("name, content", [("blocked.exe", b"x"), ("empty.pdf", b"")])
def test_invalid_upload_fails_before_gcs_or_db_write(service, storage, name, content):
    with pytest.raises(ValueError):
        upload(service, name=name, content=content)
    storage.upload.assert_not_called()
    service.eventRepository.updatePensum.assert_not_called()


@pytest.mark.parametrize("download, dispositionType", [(False, "inline"), (True, "attachment")])
def test_access_url_requires_event_permission_and_preserves_db_reference(service, storage, download, dispositionType):
    path = installOldGcsPensum(service, storage)
    event = service.eventRepository.getById.return_value
    event.pensumOriginalNameEvent = "Plan académico.docx"
    reference = event.pensumPathEvent
    with pytest.raises(PermissionError):
        service.getPensumReadUrl(7, "someone-else", [])
    storage.exists.assert_not_called()
    url = service.getPensumReadUrl(7, "tester", [], download=download)
    assert urlsplit(url).path.endswith(path)
    disposition = parse_qs(urlsplit(url).query)["response-content-disposition"][0]
    assert disposition == f"{dispositionType}; filename*=UTF-8''Plan%20acad%C3%A9mico.docx"
    assert event.pensumPathEvent == reference
    assert service.getPensumReadUrl(7, "admin", ["administrador"])


def test_adc_download_preserves_original_filename_in_signed_response(storage):
    storage._mode = "adc"
    storage._prefix = "assistanceApp_qa/"
    storage._adcClient = Mock()
    storage._adcCredentials = SimpleNamespace(
        valid=True, token="unit-token", service_account_email="vm@example.iam.gserviceaccount.com",
    )
    blob = storage._adcClient.bucket.return_value.blob.return_value
    blob.generate_signed_url.return_value = "https://storage.test/signed"
    assert storage.generateReadUrl("pensum/7/file.pdf", fileName="Plan académico.pdf", download=True)
    storage._adcClient.bucket.assert_called_once_with("calco-storage")
    storage._adcClient.bucket.return_value.blob.assert_called_once_with("assistanceApp_qa/pensum/7/file.pdf")
    assert blob.generate_signed_url.call_args.kwargs["response_disposition"] == (
        "attachment; filename*=UTF-8''Plan%20acad%C3%A9mico.pdf"
    )


@pytest.mark.parametrize("reference", [
    "gs://other-bucket/assistanceApp_dev/pensum/7/a.docx",
    "gs://calco-storage/assistanceApp_qa/pensum/7/a.docx",
    "gs://calco-storage/assistanceApp_dev/pensum/../a.docx",
    "gs://calco-storage/assistanceApp_dev/signatures/a.png",
])
def test_access_and_onlyoffice_reject_foreign_or_unsafe_references(service, storage, reference):
    event = service.eventRepository.getById.return_value
    event.pensumPathEvent = reference
    event.pensumOriginalNameEvent = "Plan.docx"
    with pytest.raises(ValueError):
        service.getPensumReadUrl(7, "tester", [])
    with pytest.raises(ValueError):
        OnlyOfficeApplication(service.eventRepository).createEventPensumPreview(7, "tester", [])
    storage.exists.assert_not_called()


def test_local_access_does_not_require_gcs(service, storage, monkeypatch):
    reference = "/uploads/pensum/7/historical.pdf"
    service.eventRepository.getById.return_value.pensumPathEvent = reference
    monkeypatch.setattr(eventModule, "GcsStorage", Mock(side_effect=AssertionError("No GCS for local files")))
    assert service.getPensumReadUrl(7, "tester", []) == reference


def test_access_endpoint_uses_authentication_and_disables_caching(service, storage):
    installOldGcsPensum(service, storage)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[getEventApplication] = lambda: service
    with TestClient(app) as client:
        assert client.get("/events/7/pensum/access").status_code in (401, 403)
        app.dependency_overrides[getCurrentAuthContext] = lambda: {"userLogin": "tester", "roles": []}
        response = client.get("/events/7/pensum/access")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-store"
        assert response.json()["result"].startswith("https://storage.googleapis.com/")
        storage.exists.return_value = False
        assert client.get("/events/7/pensum/access").status_code == 404


@pytest.mark.parametrize("extension, documentType", [("docx", "word"), ("xlsx", "cell"), ("pptx", "slide")])
def test_onlyoffice_reads_gcs_directly_with_signed_config_and_no_local_copy(service, storage, extension, documentType):
    event = service.eventRepository.getById.return_value
    event.pensumPathEvent = storage.objectReference(f"pensum/7/new.{extension}")
    event.pensumOriginalNameEvent = f"Plan.{extension}"
    office = OnlyOfficeApplication(service.eventRepository)
    preview = office.createEventPensumPreview(7, "tester", [])
    assert preview.config["documentType"] == documentType
    assert preview.config["document"]["url"].startswith("https://storage.googleapis.com/")
    signedConfig = jwt.decode(preview.config["token"], settings.ONLYOFFICE_JWT_SECRET, algorithms=["HS256"])
    assert signedConfig["document"] == preview.config["document"]
    assert not Path(settings.UPLOAD_DIR).exists()
    assert not office.previewDirectory.exists()
    same = office.createEventPensumPreview(7, "tester", [])
    assert same.config["document"]["key"] == preview.config["document"]["key"]
    event.pensumPathEvent = storage.objectReference(f"pensum/7/replaced.{extension}")
    replaced = office.createEventPensumPreview(7, "tester", [])
    assert replaced.config["document"]["key"] != preview.config["document"]["key"]


def test_onlyoffice_local_pensum_still_uses_secure_backend_endpoint(service, storage, monkeypatch):
    file = Path(settings.UPLOAD_DIR) / "pensum/7/old.docx"
    file.parent.mkdir(parents=True)
    file.write_bytes(b"historical")
    event = service.eventRepository.getById.return_value
    event.pensumPathEvent = "/uploads/pensum/7/old.docx"
    event.pensumOriginalNameEvent = "old.docx"
    monkeypatch.setattr(officeModule, "GcsStorage", Mock(side_effect=AssertionError("No GCS for local files")))
    office = OnlyOfficeApplication(service.eventRepository)
    preview = office.createEventPensumPreview(7, "tester", [])
    url = preview.config["document"]["url"]
    assert url.startswith("https://backend.test/onlyoffice/files/")
    assert Path(office.resolveFileAccess(url.rsplit("/", 1)[1])[0]) == file
    assert file.read_bytes() == b"historical"


@pytest.fixture
def training(storage):
    # Exercise real repository transactions with a mocked Session: no SQL or DB I/O.
    parameter = TrainingParameter(
        IdTrainingParameter=12, nameTrainingParameter="SEGURIDAD", isActive=False,
        createdAt=datetime(2026, 10, 20),
        topics=[ParameterTopic(
            IdParameterTopic=1, IdTrainingParameter=12,
            nameParameterTopic="INTRODUCCIÓN", sortOrder=0,
        )],
    )
    repository = TrainingParameterRepository(Mock())
    repository.getById = Mock(return_value=parameter)
    repository.getByName = Mock(return_value=None)
    # Existing storage tests isolate version persistence; dedicated tests below exercise it.
    repository.appendVersion = Mock()
    return TrainingParameterApplication(repository)


def setOfficialPensum(training, storage):
    parameter = training.getById(12)
    parameter.pensumPathTrainingParameter = storage.objectReference(
        "pensum/parameters/12/" + "a" * 32 + ".docx",
    )
    parameter.pensumOriginalNameTrainingParameter = "Plan.docx"
    parameter.pensumMimeTypeTrainingParameter = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    parameter.pensumSizeTrainingParameter = 42
    return parameter


def officialUpload(training, **kwargs):
    return training.uploadPensum(12, UploadFile(
        filename=kwargs.get("name", "Plan.docx"),
        file=BytesIO(kwargs.get("content", b"official document")),
        headers=Headers({"content-type": "application/octet-stream"}),
    ))


@pytest.mark.parametrize("values", [
    {"nameTrainingParameter": " "},
    {"nameTrainingParameter": "a" * 201},
    {"topics": [" "]},
    {"topics": ["a" * 301]},
    {"topics": ["  tema  Uno ", "TEMA UNO"]},
    {"topics": ["introducción", "INTRODUCCION"]},
    {"topics": ["ß" * 151]},
    {"pensumPathTrainingParameter": "gs://client/file"},
])
def test_parameter_dto_rejects_invalid_names_duplicates_and_client_document(values):
    with pytest.raises(ValueError):
        TrainingParameterCreateDto(**{"nameTrainingParameter": "Seguridad", **values})


@pytest.mark.parametrize("field", ["nameTrainingParameter", "topics", "isActive"])
def test_parameter_update_rejects_explicit_null(field):
    with pytest.raises(ValueError):
        TrainingParameterUpdateDto(**{field: None})


def test_parameter_create_normalizes_names_and_preserves_topic_order(training):
    data = TrainingParameterCreateDto(
        nameTrainingParameter="  seguridad \t general ",
        topics=["  tema  uno ", "tema dos"],
    )
    training.create(data)
    saved = training.repository.db.add.call_args.args[0]
    assert saved.nameTrainingParameter == "SEGURIDAD GENERAL"
    assert not saved.isActive
    assert [(t.nameParameterTopic, t.sortOrder) for t in saved.topics] == [
        ("TEMA UNO", 0), ("TEMA DOS", 1),
    ]
    training.repository.db.commit.assert_called_once()
    # No global lookup of topic names: the same topic is allowed in another parameter.
    training.create(TrainingParameterCreateDto(nameTrainingParameter="Otro", topics=["tema uno"]))


def test_duplicate_parameter_and_racing_unique_constraint_are_rejected(training):
    training.repository.getByName.return_value = training.getById(12)
    with pytest.raises(ValueError, match="Ya existe"):
        training.create(TrainingParameterCreateDto(nameTrainingParameter="seguridad"))
    training.repository.db.add.assert_not_called()
    training.repository.getByName.return_value = None
    training.repository.db.commit.side_effect = IntegrityError("synthetic", {}, Exception())
    with pytest.raises(ValueError, match="Ya existe"):
        training.create(TrainingParameterCreateDto(nameTrainingParameter="Otro"))
    training.repository.db.rollback.assert_called_once()


def test_activation_requires_official_document_topics_and_existing_object(training, storage):
    with pytest.raises(ValueError, match="inactivo"):
        training.create(TrainingParameterCreateDto(nameTrainingParameter="Nuevo", isActive=True))
    with pytest.raises(ValueError, match="PÉNSUM"):
        training.update(12, TrainingParameterUpdateDto(isActive=True))
    setOfficialPensum(training, storage)
    with pytest.raises(ValueError, match="tema"):
        training.update(12, TrainingParameterUpdateDto(isActive=True, topics=[]))
    storage.exists.return_value = False
    with pytest.raises(ValueError, match="GCS"):
        training.update(12, TrainingParameterUpdateDto(isActive=True))
    storage.exists.return_value = True
    assert training.update(12, TrainingParameterUpdateDto(isActive=True)).isActive
    assert not training.update(12, TrainingParameterUpdateDto(isActive=False)).isActive


def test_catalog_topic_reorder_is_atomic_and_does_not_query_events(training):
    result = training.update(12, TrainingParameterUpdateDto(topics=["nuevo", "introducción"]))
    assert [(t.nameParameterTopic, t.sortOrder) for t in result.topics] == [
        ("NUEVO", 0), ("INTRODUCCIÓN", 1),
    ]
    training.repository.getById.assert_any_call(12, forUpdate=True)
    training.repository.db.flush.assert_called_once()
    training.repository.db.commit.assert_called_once()
    training.repository.db.query.assert_not_called()


def test_initial_official_upload_stores_metadata_once_without_deletion(training, storage):
    result = officialUpload(training)
    path, content, mime = storage.upload.call_args.args
    assert path.startswith("pensum/parameters/12/") and path.endswith(".docx")
    assert len(Path(path).stem) == 32
    assert result.pensumPathTrainingParameter == storage.objectReference(path)
    assert result.pensumSizeTrainingParameter == len(content)
    assert result.pensumMimeTypeTrainingParameter == mime
    assert result.pensumOriginalNameTrainingParameter == "Plan.docx"
    with pytest.raises(FileExistsError):
        officialUpload(training)
    storage.upload.assert_called_once()
    storage.delete.assert_not_called()


def test_competing_initial_upload_rechecks_document_under_lock(training, storage):
    empty = TrainingParameter(IdTrainingParameter=12)
    committed = setOfficialPensum(training, storage)
    training.repository.getById.side_effect = [empty, committed]
    with pytest.raises(FileExistsError):
        officialUpload(training)
    storage.upload.assert_not_called()
    training.repository.db.commit.assert_not_called()
    training.repository.db.rollback.assert_called_once()


@pytest.mark.parametrize("failure", ["upload", "commit", "refresh"])
def test_official_upload_uncertain_outcomes_never_delete_objects(training, storage, failure):
    parameter = training.getById(12)
    if failure == "upload":
        storage.upload.side_effect = GcsStorageError("uncertain upload")
    else:
        getattr(training.repository.db, failure).side_effect = RuntimeError("uncertain persistence")
    with pytest.raises((GcsStorageError, RuntimeError)):
        officialUpload(training)
    storage.delete.assert_not_called()
    training.repository.db.rollback.assert_called_once()
    if failure == "upload":
        assert parameter.pensumPathTrainingParameter is None
        training.repository.db.commit.assert_not_called()


@pytest.mark.parametrize("name, content", [("bad.exe", b"x"), ("empty.pdf", b"")])
def test_invalid_official_document_fails_before_upload(training, storage, name, content):
    with pytest.raises(ValueError):
        officialUpload(training, name=name, content=content)
    storage.upload.assert_not_called()
    training.repository.db.commit.assert_not_called()


def test_parameter_snapshot_and_final_topics_share_event_transaction(training, storage, monkeypatch):
    parameter = setOfficialPensum(training, storage)
    parameter.isActive = True
    repoModule = importlib.import_module("app.infrastructure.repositories.EventRepository")
    monkeypatch.setattr(repoModule, "TrainingParameterRepository", lambda db: training.repository)
    repo = EventRepository(Mock())
    event = Event(IdEvent=7, IdTrainingParameter=12, titleEvent="TÍTULO EDITADO")
    repo.getById = Mock(return_value=event)
    repo._replaceTopics = Mock()
    repo._replaceCompetencies = Mock()
    repo.create(event, None, [3])
    training.repository.getById.assert_any_call(12, forUpdate=True)
    assert event.titleEvent == "TÍTULO EDITADO" and event.IdTrainingParameter == 12
    assert event.pensumPathEvent == parameter.pensumPathTrainingParameter
    assert event.pensumOriginalNameEvent == parameter.pensumOriginalNameTrainingParameter
    assert event.pensumMimeTypeEvent == parameter.pensumMimeTypeTrainingParameter
    assert event.pensumSizeEvent == parameter.pensumSizeTrainingParameter
    repo._replaceTopics.assert_called_once_with(7, ["INTRODUCCIÓN"])
    repo.db.commit.assert_called_once()
    original = event.pensumPathEvent
    training.update(12, TrainingParameterUpdateDto(topics=["Otro"], isActive=False))
    assert event.pensumPathEvent == original
    repo._replaceTopics.assert_called_once_with(7, ["INTRODUCCIÓN"])
    parameter.isActive = True
    repo.create(event, ["  mi   tema "], [])
    repo._replaceTopics.assert_called_with(7, ["MI TEMA"])


@pytest.mark.parametrize("scenario", ["missing", "inactive", "no_document", "empty_topics", "topic_failure"])
def test_parameter_event_failures_roll_back_the_whole_transaction(training, storage, monkeypatch, scenario):
    parameter = setOfficialPensum(training, storage)
    parameter.isActive = True
    if scenario == "missing":
        training.repository.getById.return_value = None
    elif scenario == "inactive":
        parameter.isActive = False
    elif scenario == "no_document":
        parameter.pensumPathTrainingParameter = None
    repoModule = importlib.import_module("app.infrastructure.repositories.EventRepository")
    monkeypatch.setattr(repoModule, "TrainingParameterRepository", lambda db: training.repository)
    repo = EventRepository(Mock())
    repo._replaceTopics = Mock(side_effect=RuntimeError("topic failure"))
    with pytest.raises((ValueError, RuntimeError)):
        repo.create(
            Event(IdEvent=7, IdTrainingParameter=12),
            [] if scenario == "empty_topics" else None, [],
        )
    repo.db.commit.assert_not_called()
    repo.db.rollback.assert_called_once()


def test_locked_catalog_reads_refresh_both_parent_and_ordered_topics(training):
    parameter = training.getById(12)
    topic = parameter.topics[0]
    db = Mock()
    parentQuery, topicQuery = Mock(), Mock()
    db.query.side_effect = [parentQuery, topicQuery]
    parentQuery.filter.return_value.populate_existing.return_value.with_for_update.return_value.first.return_value = parameter
    topicQuery.filter.return_value.order_by.return_value.populate_existing.return_value.with_for_update.return_value.all.return_value = [topic]
    assert TrainingParameterRepository(db).getById(12, forUpdate=True) is parameter
    parentQuery.filter.return_value.populate_existing.return_value.with_for_update.assert_called_once()
    topicQuery.filter.return_value.order_by.return_value.populate_existing.return_value.with_for_update.assert_called_once()
    db.commit.assert_not_called()


def test_event_create_passes_explicit_selection_and_distinguishes_omitted_topics(service):
    service._generateQr = Mock(return_value="/uploads/qrs/test.png")
    service._buildResponse = Mock(side_effect=lambda event: event)
    service.eventRepository.create.side_effect = lambda event, topics, competencies: event
    values = dict(
        titleEvent="seguridad", dateEvent=date(2100, 1, 1), startTimeEvent=time(9),
        endTimeEvent=time(10), isPaidTrainingEvent=False,
        facilitatorNameEvent="Formador", facilitatorTypeEvent="INTERNO",
        facilitatorPositionEvent="Instructor",
    )
    free = service.create(EventCreateDto(**values), "tester", ["formador"])
    assert free.IdTrainingParameter is None
    assert service.eventRepository.create.call_args.args[1] == []
    service.create(EventCreateDto(**values, IdTrainingParameter=12), "tester", ["formador"])
    assert service.eventRepository.create.call_args.args[1] is None
    service.create(EventCreateDto(**values, IdTrainingParameter=12, topics=["Editado"]), "tester", ["formador"])
    assert service.eventRepository.create.call_args.args[1] == ["EDITADO"]
    with pytest.raises(ValueError, match="tema"):
        service.create(EventCreateDto(**values, IdTrainingParameter=12, topics=[]), "tester", ["formador"])


@pytest.mark.parametrize("selection", [None, 12, 99])
def test_event_update_rejects_parameter_assignment_change_or_removal(selection):
    with pytest.raises(ValueError, match="IdTrainingParameter"):
        EventUpdateDto(IdTrainingParameter=selection)


def test_official_reference_cannot_be_supplied_by_client():
    with pytest.raises(ValueError, match="exclusivamente"):
        EventCreateDto(
            titleEvent="Título", dateEvent=date(2100, 1, 1), startTimeEvent=time(9),
            endTimeEvent=time(10), IdTrainingParameter=12, pensumPathEvent="gs://attacker/file",
        )


def test_parameter_event_blocks_upload_and_repository_bypasses(service, storage):
    event = service.eventRepository.getById.return_value
    event.IdTrainingParameter = 12
    with pytest.raises(ValueError, match="parametrizado"):
        upload(service)
    storage.upload.assert_not_called()
    repo = EventRepository(Mock())
    repo.getById = Mock(return_value=event)
    with pytest.raises(ValueError, match="parametrizado"):
        repo.updatePensum(7, "bad.pdf", "gs://bad/file", "application/pdf", 4, "tester")
    with pytest.raises(ValueError, match="IdTrainingParameter"):
        repo.update(7, {"IdTrainingParameter": None}, None, None)
    with pytest.raises(ValueError, match="parametrizado"):
        repo.update(7, {"pensumPathEvent": "gs://bad/file"}, None, None)
    repo.db.commit.assert_not_called()


def test_onlyoffice_uses_the_event_snapshot_of_parameter_document(service, training, storage):
    parameter = setOfficialPensum(training, storage)
    event = service.eventRepository.getById.return_value
    event.IdTrainingParameter = 12
    event.pensumPathEvent = parameter.pensumPathTrainingParameter
    event.pensumOriginalNameEvent = parameter.pensumOriginalNameTrainingParameter
    preview = OnlyOfficeApplication(service.eventRepository).createEventPensumPreview(7, "tester", [])
    assert "/pensum/parameters/12/" in preview.config["document"]["url"]
    assert preview.config["documentType"] == "word"
    storage.delete.assert_not_called()


@pytest.mark.parametrize("method, path, body", [
    ("post", "/training-parameters/", {"nameTrainingParameter": "Nuevo"}),
    ("put", "/training-parameters/12", {"nameTrainingParameter": "Nuevo"}),
    ("patch", "/training-parameters/12/status", {"isActive": False}),
    ("post", "/training-parameters/12/pensum", None),
    ("put", "/training-parameters/12/pensum", None),
])
def test_catalog_administrative_writes_reject_regular_authenticated_users(training, method, path, body):
    app = FastAPI()
    app.include_router(trainingParameterRouter)
    app.dependency_overrides[getTrainingParameterApplication] = lambda: training
    app.dependency_overrides[getCurrentPayload] = lambda: {"userLogin": "trainer", "roles": ["formador"]}
    kwargs = {"json": body} if body is not None else {"files": {"file": ("Plan.pdf", b"test", "application/pdf")}}
    with TestClient(app) as client:
        assert client.request(method, path, **kwargs).status_code == 403
    training.repository.db.commit.assert_not_called()


def test_catalog_routes_authentication_contract_and_temporary_access(training, storage):
    setOfficialPensum(training, storage)
    app = FastAPI()
    app.include_router(trainingParameterRouter)
    app.dependency_overrides[getTrainingParameterApplication] = lambda: training
    training.repository.getAll = Mock(return_value=[training.getById(12)])
    with TestClient(app) as client:
        assert client.get("/training-parameters/12").status_code in (401, 403)
        assert client.get("/training-parameters/12/pensum/access").status_code in (401, 403)
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["administrador"], "userLogin": "admin-test"}
        assert client.get("/training-parameters/?isActive=true").status_code == 200
        training.repository.getAll.assert_called_with(True)
        result = client.get("/training-parameters/12").json()["result"]
        assert result["topics"][0]["sortOrder"] == 0
        response = client.get("/training-parameters/12/pensum/access")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-store"
        assert "X-Goog-Expires=300" in response.json()["result"]
        assert client.post("/training-parameters/12/pensum", files={"file": ("Plan.pdf", b"x")}).status_code == 409
        assert client.patch("/training-parameters/12/status", json={"isActive": True}).status_code == 200
        training.repository.getById.return_value = None
        assert client.get("/training-parameters/999").status_code == 404


@pytest.fixture
def completeClient(training):
    db = training.repository.db

    def assignIds():
        parameter = db.add.call_args.args[0]
        parameter.IdTrainingParameter = 24
        for index, topic in enumerate(parameter.topics):
            topic.IdParameterTopic = index + 1
            topic.IdTrainingParameter = 24

    db.flush.side_effect = assignIds
    training.repository.getById.side_effect = lambda *args, **kwargs: db.add.call_args.args[0]
    app = FastAPI()
    app.include_router(trainingParameterRouter)
    app.dependency_overrides[getTrainingParameterApplication] = lambda: training
    app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["administrador"], "userLogin": "admin-test"}
    with TestClient(app) as client:
        yield client


def completeRequest(client, **overrides):
    request = {
        "data": {
            "nameTrainingParameter": "  seguridad   general ",
            "topics": json.dumps([" práctica ", "  introducción  "]),
        },
        "files": {"file": ("Plan.pdf", b"official document", "application/pdf")},
    }
    return client.post("/training-parameters/complete", **{**request, **overrides})


def test_complete_creation_commits_once_after_upload_and_returns_active_aggregate(completeClient, training, storage):
    db = training.repository.db

    def uploaded(path, content, mime):
        parameter = db.add.call_args.args[0]
        assert parameter.IdTrainingParameter == 24 and not parameter.isActive
        db.flush.assert_called_once()
        db.commit.assert_not_called()
        return 123

    def committed():
        parameter = db.add.call_args.args[0]
        parameter.validateReady()
        assert parameter.isActive
        assert db.flush.call_count == 2

    storage.upload.side_effect = uploaded
    db.commit.side_effect = committed
    response = completeRequest(completeClient)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["isSuccess"] is True and body["Message"]
    result = body["result"]
    assert result["IdTrainingParameter"] == 24 and result["isActive"] is True
    assert result["nameTrainingParameter"] == "SEGURIDAD GENERAL"
    assert [(t["nameParameterTopic"], t["sortOrder"]) for t in result["topics"]] == [
        ("PRÁCTICA", 0), ("INTRODUCCIÓN", 1),
    ]
    path, content, mime = storage.upload.call_args.args
    assert path.startswith("pensum/parameters/24/") and path.endswith(".pdf")
    assert len(path.rsplit("/", 1)[1]) == 36
    assert result["pensumPathTrainingParameter"] == storage.objectReference(path)
    assert result["pensumOriginalNameTrainingParameter"] == "Plan.pdf"
    assert result["pensumMimeTypeTrainingParameter"] == mime == "application/pdf"
    assert result["pensumSizeTrainingParameter"] == len(content)
    db.commit.assert_called_once()
    db.rollback.assert_not_called()
    storage.upload.assert_called_once()
    storage.delete.assert_not_called()

    schema = completeClient.get("/openapi.json").json()
    bodySchema = schema["paths"]["/training-parameters/complete"]["post"]["requestBody"]
    reference = bodySchema["content"]["multipart/form-data"]["schema"]["$ref"]
    fields = schema["components"]["schemas"][reference.rsplit("/", 1)[1]]
    assert set(fields["required"]) == {"nameTrainingParameter", "topics", "file"}
    assert fields["properties"]["topics"]["type"] == "string"
    assert "anyOf" not in fields["properties"]["topics"]
    assert bodySchema["content"]["multipart/form-data"]["encoding"]["topics"] == {
        "contentType": "application/json",
    }


@pytest.mark.parametrize("filename", [None, "blob"])
def test_complete_accepts_json_topics_as_text_or_swagger_blob(completeClient, filename):
    topicsText = '["INTRODUCCION","PRACTICA"]'
    response = completeRequest(
        completeClient,
        data={"nameTrainingParameter": "Seguridad"},
        files={
            "topics": (filename, topicsText, "application/json"),
            "file": ("Plan.pdf", b"official document", "application/pdf"),
        },
    )
    assert response.status_code == 201, response.text
    assert topicsText.encode() in response.request.content
    assert [topic["nameParameterTopic"] for topic in response.json()["result"]["topics"]] == [
        "INTRODUCCION", "PRACTICA",
    ]


@pytest.mark.parametrize("filename, topicsText", [
    (None, "INTRODUCCION,PRACTICA"),
    ("blob", "INTRODUCCION,PRACTICA"),
    (None, '["INTRODUCCION",]'),
    ("blob", b"\xff"),
])
def test_complete_reports_clear_error_for_invalid_json_topics(completeClient, training, storage, filename, topicsText):
    response = completeRequest(
        completeClient,
        data={"nameTrainingParameter": "Seguridad"},
        files={
            "topics": (filename, topicsText, "application/json"),
            "file": ("Plan.pdf", b"official document", "application/pdf"),
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El campo topics debe contener un arreglo JSON válido de temas."
    training.repository.db.add.assert_not_called()
    storage.upload.assert_not_called()


@pytest.mark.parametrize("name, topics", [
    (" ", '["Tema"]'),
    ("x" * 201, '["Tema"]'),
    ("Seguridad", "not json"),
    ("Seguridad", '"Tema"'),
    ("Seguridad", "{}"),
    ("Seguridad", "null"),
    ("Seguridad", "[]"),
    ("Seguridad", '[" "]'),
    ("Seguridad", json.dumps(["x" * 301])),
    ("Seguridad", '[" introducción ", "INTRODUCCION"]'),
    ("Seguridad", "[123]"),
])
def test_complete_rejects_invalid_name_or_topics_before_persistence(completeClient, training, storage, name, topics):
    response = completeRequest(completeClient, data={"nameTrainingParameter": name, "topics": topics})
    assert response.status_code == 400
    training.repository.db.add.assert_not_called()
    storage.upload.assert_not_called()


@pytest.mark.parametrize("files, status", [
    ({}, 422),
    ({"file": ("Plan.exe", b"invalid", "application/octet-stream")}, 400),
    ({"file": ("Plan.pdf", b"", "application/pdf")}, 400),
    ({"file": ("Plan.pdf", b"x", "x" * 151)}, 400),
])
def test_complete_requires_valid_document(completeClient, training, storage, files, status):
    assert completeRequest(completeClient, files=files).status_code == status
    training.repository.db.add.assert_not_called()
    storage.upload.assert_not_called()


def test_complete_reuses_storage_mime_validation(completeClient, training, storage):
    storage.upload.side_effect = lambda *args: GcsStorage.upload(storage, *args)
    response = completeRequest(completeClient, files={"file": ("Plan.pdf", b"x", "invalid-mime")})
    assert response.status_code == 400
    training.repository.db.commit.assert_not_called()
    training.repository.db.rollback.assert_called_once()
    storage.delete.assert_not_called()


@pytest.mark.parametrize("racing", [False, True])
def test_complete_rejects_duplicate_names_including_concurrent_insert(completeClient, training, storage, racing):
    if racing:
        training.repository.db.flush.side_effect = IntegrityError("synthetic", {}, Exception())
    else:
        training.repository.getByName.return_value = TrainingParameter(IdTrainingParameter=12)
    assert completeRequest(completeClient).status_code == 400
    storage.upload.assert_not_called()
    training.repository.db.commit.assert_not_called()
    if racing:
        training.repository.db.rollback.assert_called_once()
    else:
        training.repository.db.add.assert_not_called()


@pytest.mark.parametrize("failure", ["flush", "upload", "metadata", "commit", "refresh", "readback"])
def test_complete_failures_roll_back_and_never_delete_uncertain_objects(
    completeClient, training, storage, caplog, failure,
):
    db = training.repository.db
    if failure == "upload":
        storage.upload.side_effect = GcsStorageError("synthetic upload failure")
    elif failure == "metadata":
        assignIds = db.flush.side_effect

        def failMetadata():
            if db.flush.call_count == 2:
                raise RuntimeError("synthetic metadata failure")
            assignIds()

        db.flush.side_effect = failMetadata
    elif failure == "readback":
        training.repository.getById.side_effect = RuntimeError("synthetic readback failure")
    else:
        getattr(db, failure).side_effect = RuntimeError("synthetic persistence failure")

    response = completeRequest(completeClient)
    assert response.status_code == (503 if failure == "upload" else 500)
    db.rollback.assert_called_once()
    storage.delete.assert_not_called()
    if failure in ("flush", "upload", "metadata"):
        db.commit.assert_not_called()
    else:
        db.commit.assert_called_once()
    if failure == "flush":
        storage.upload.assert_not_called()
    else:
        assert "conservar PÉNSUM para revisión" in caplog.text
        assert "IdTrainingParameter=24" in caplog.text
        assert storage.objectReference(storage.upload.call_args.args[0]) in caplog.text
        if failure != "upload":
            assert "generation=123" in caplog.text


def test_complete_preserves_original_error_and_object_when_rollback_also_fails(completeClient, training, storage, caplog):
    training.repository.db.commit.side_effect = RuntimeError("synthetic commit failure")
    training.repository.db.rollback.side_effect = RuntimeError("synthetic rollback failure")
    assert completeRequest(completeClient).status_code == 500
    assert "No fue posible revertir" in caplog.text
    assert "synthetic commit failure" in caplog.text
    storage.delete.assert_not_called()


@pytest.mark.parametrize("roles", [None, [], ["formador"]])
def test_complete_requires_authenticated_administrator(completeClient, training, storage, roles):
    if roles is None:
        del completeClient.app.dependency_overrides[getCurrentPayload]
    else:
        completeClient.app.dependency_overrides[getCurrentPayload] = lambda: {"roles": roles}
    assert completeRequest(completeClient).status_code in (401, 403)
    training.repository.db.add.assert_not_called()
    storage.upload.assert_not_called()


def test_complete_addition_preserves_legacy_create_upload_update_activate_flow(completeClient, training, storage):
    # Simulate IDs generated by commit for the legacy create, which has no explicit flush.
    training.repository.db.commit.side_effect = training.repository.db.flush.side_effect
    response = completeClient.post("/training-parameters/", json={"nameTrainingParameter": "Legacy"})
    assert response.status_code == 201 and response.json()["result"]["isActive"] is False
    assert response.json()["result"]["topics"] == []
    storage.upload.assert_not_called()
    response = completeClient.put("/training-parameters/24", json={"topics": ["Tema"]})
    assert response.status_code == 200
    response = completeClient.post(
        "/training-parameters/24/pensum", files={"file": ("Plan.pdf", b"legacy", "application/pdf")},
    )
    assert response.status_code == 200 and response.json()["result"]["isActive"] is False
    response = completeClient.patch("/training-parameters/24/status", json={"isActive": True})
    assert response.status_code == 200 and response.json()["result"]["isActive"] is True
    assert completeClient.get("/training-parameters/24").status_code == 200
    assert completeClient.get("/training-parameters/24/pensum/access").status_code == 200


def replacementUpload(training, name="Plan_2027.pdf", content=b"new official document", mime="application/pdf"):
    return training.updatePensum(12, UploadFile(
        filename=name, file=BytesIO(content), headers=Headers({"content-type": mime}),
    ))


@pytest.mark.parametrize("active", [False, True])
def test_pensum_replacement_only_changes_document_and_keeps_each_object(training, storage, active):
    parameter = setOfficialPensum(training, storage)
    parameter.isActive = active
    original = parameter.pensumPathTrainingParameter
    preserved = (parameter.IdTrainingParameter, parameter.nameTrainingParameter, parameter.createdAt, parameter.topics[:])
    result = replacementUpload(training)
    path, content, mime = storage.upload.call_args.args
    assert path.startswith("pensum/parameters/12/") and path.endswith(".pdf")
    assert len(Path(path).stem) == 32
    assert result.pensumPathTrainingParameter == storage.objectReference(path) != original
    assert result.pensumOriginalNameTrainingParameter == "Plan_2027.pdf"
    assert result.pensumMimeTypeTrainingParameter == mime
    assert result.pensumSizeTrainingParameter == len(content)
    assert result.updatedAt is not None and result.isActive is active
    assert (result.IdTrainingParameter, result.nameTrainingParameter, result.createdAt, result.topics[:]) == preserved
    training.repository.getById.assert_any_call(12, forUpdate=True)
    training.repository.db.commit.assert_called_once()
    training.repository.db.query.assert_not_called()
    replacementUpload(training)
    assert storage.upload.call_args_list[0].args[0] != storage.upload.call_args_list[1].args[0]
    storage.delete.assert_not_called()
    with pytest.raises(FileExistsError):
        officialUpload(training)


@pytest.mark.parametrize("name, content, mime", [
    ("bad.exe", b"x", "application/octet-stream"),
    ("empty.pdf", b"", "application/pdf"),
    ("x" * 256 + ".pdf", b"x", "application/pdf"),
    ("Plan.pdf", b"x", "x" * 151),
])
def test_pensum_replacement_invalid_file_preserves_original(training, storage, name, content, mime):
    parameter = setOfficialPensum(training, storage)
    original = parameter.pensumPathTrainingParameter
    with pytest.raises(ValueError):
        replacementUpload(training, name, content, mime)
    assert parameter.pensumPathTrainingParameter == original
    storage.upload.assert_not_called()
    storage.delete.assert_not_called()
    training.repository.db.commit.assert_not_called()


@pytest.mark.parametrize("failure", ["upload", "commit", "refresh"])
def test_pensum_replacement_failures_keep_objects_and_log_references(training, storage, caplog, failure):
    parameter = setOfficialPensum(training, storage)
    original = parameter.pensumPathTrainingParameter
    if failure == "upload":
        storage.upload.side_effect = GcsStorageError("uncertain upload")
    else:
        getattr(training.repository.db, failure).side_effect = RuntimeError("uncertain persistence")
    with pytest.raises((GcsStorageError, RuntimeError)):
        replacementUpload(training)
    training.repository.db.rollback.assert_called_once()
    storage.delete.assert_not_called()
    assert original in caplog.text
    assert storage.objectReference(storage.upload.call_args.args[0]) in caplog.text
    if failure == "upload":
        training.repository.db.commit.assert_not_called()
        assert parameter.pensumPathTrainingParameter == original
    else:
        training.repository.db.commit.assert_called_once()
        assert "generation=123" in caplog.text


def test_pensum_replacement_rejects_overlapping_update_before_second_upload(training, storage):
    parameter = setOfficialPensum(training, storage)
    # Interleave a second administrator after the first read, before its locking read.
    # Both reads return the same ORM instance, as in SQLAlchemy's identity map.
    stream = Mock()
    winner = []

    def otherAdministratorCommits():
        winner.append(replacementUpload(training).pensumPathTrainingParameter)
        return b"stale update"

    stream.read.side_effect = otherAdministratorCommits
    with pytest.raises(FileExistsError, match="Otro administrador"):
        training.updatePensum(12, UploadFile(filename="stale.pdf", file=stream))
    assert parameter.pensumPathTrainingParameter == winner[0]
    storage.upload.assert_called_once()
    storage.delete.assert_not_called()
    training.repository.db.commit.assert_called_once()
    training.repository.db.rollback.assert_called_once()


def test_pensum_replacement_keeps_old_event_snapshot_and_new_events_use_current(training, storage, monkeypatch):
    parameter = setOfficialPensum(training, storage)
    parameter.isActive = True
    repoModule = importlib.import_module("app.infrastructure.repositories.EventRepository")
    monkeypatch.setattr(repoModule, "TrainingParameterRepository", lambda db: training.repository)
    repository = EventRepository(Mock())
    repository._replaceTopics = Mock()
    repository._replaceCompetencies = Mock()

    def createEvent(id):
        event = Event(IdEvent=id, IdTrainingParameter=12, titleEvent="Evento")
        repository.getById = Mock(return_value=event)
        return repository.create(event, None, [])

    def document(event):
        return (event.IdTrainingParameter, event.pensumPathEvent, event.pensumOriginalNameEvent,
                event.pensumMimeTypeEvent, event.pensumSizeEvent)

    oldEvent = createEvent(7)
    oldDocument = document(oldEvent)
    replacementUpload(training)
    newEvent = createEvent(8)
    assert document(oldEvent) == oldDocument
    assert document(newEvent) == (
        12, parameter.pensumPathTrainingParameter, parameter.pensumOriginalNameTrainingParameter,
        parameter.pensumMimeTypeTrainingParameter, parameter.pensumSizeTrainingParameter,
    )
    assert newEvent.pensumPathEvent != oldEvent.pensumPathEvent
    storage.upload.assert_called_once()  # Event creation adds no GCS copies.
    storage.delete.assert_not_called()


def test_pensum_replacement_http_contract_permissions_and_initial_upload(training, storage):
    app = FastAPI()
    app.include_router(trainingParameterRouter)
    app.dependency_overrides[getTrainingParameterApplication] = lambda: training
    files = {"file": ("Plan.pdf", b"new official", "application/pdf")}
    with TestClient(app) as client:
        assert client.put("/training-parameters/12/pensum", files=files).status_code in (401, 403)
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["administrador"], "userLogin": "admin-test"}
        assert client.put("/training-parameters/12/pensum").status_code == 422
        assert client.put("/training-parameters/12/pensum", files=files).status_code == 400
        storage.upload.assert_not_called()
        assert client.post("/training-parameters/12/pensum", files=files).status_code == 200
        response = client.put("/training-parameters/12/pensum", files=files)
        assert response.status_code == 200
        assert response.json()["isSuccess"] is True
        assert response.json()["result"]["pensumOriginalNameTrainingParameter"] == "Plan.pdf"
        assert response.json()["result"]["topics"][0]["nameParameterTopic"] == "INTRODUCCIÓN"
        assert client.post("/training-parameters/12/pensum", files=files).status_code == 409
        storage.upload.side_effect = GcsStorageError("unavailable")
        assert client.put("/training-parameters/12/pensum", files=files).status_code == 503
        storage.upload.side_effect = None
        training.repository.db.commit.side_effect = RuntimeError("uncertain commit")
        assert client.put("/training-parameters/12/pensum", files=files).status_code == 500
        training.repository.getById.return_value = None
        assert client.put("/training-parameters/999/pensum", files=files).status_code == 404
    storage.delete.assert_not_called()


def versionSnapshot(parameter, number=1, baseline=False):
    return TrainingParameterVersion(
        IdTrainingParameterVersion=number, IdTrainingParameter=parameter.IdTrainingParameter, versionNumber=number,
        pensumPathTrainingParameterVersion=parameter.pensumPathTrainingParameter,
        pensumOriginalNameTrainingParameterVersion=parameter.pensumOriginalNameTrainingParameter,
        pensumMimeTypeTrainingParameterVersion=parameter.pensumMimeTypeTrainingParameter,
        pensumSizeTrainingParameterVersion=parameter.pensumSizeTrainingParameter,
        createdAt=datetime(2026, 10, 20), createdByUserLogin=None if baseline else "admin-test", isBaseline=baseline,
    )


@pytest.mark.parametrize("flow", ["complete", "initial", "replacement"])
def test_version_publication_shares_commit_and_upload_with_parameter(training, storage, flow):
    repository, added = training.repository, []
    parameter = training.getById(12)
    baseline = versionSnapshot(setOfficialPensum(training, storage), baseline=True) if flow == "replacement" else None
    repository.appendVersion = TrainingParameterRepository.appendVersion.__get__(repository)
    repository.db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = baseline
    repository.db.add.side_effect = added.append

    def flush():
        for item in added:
            if isinstance(item, TrainingParameter):
                item.IdTrainingParameter = 24

    def commit():
        versions = [v for v in added if isinstance(v, TrainingParameterVersion)]
        assert len(versions) == 1
        version = versions[0]
        current = next((p for p in added if isinstance(p, TrainingParameter)), parameter)
        assert version.pensumPathTrainingParameterVersion == current.pensumPathTrainingParameter
        assert version.pensumOriginalNameTrainingParameterVersion == current.pensumOriginalNameTrainingParameter
        assert version.createdByUserLogin == "session-user" and version.isBaseline is False
        assert version.versionNumber == (2 if flow == "replacement" else 1)
        storage.upload.assert_called_once()

    repository.db.flush.side_effect = flush
    repository.db.commit.side_effect = commit
    file = UploadFile(filename="new.pdf", file=BytesIO(b"official"))
    if flow == "complete":
        training.createComplete(TrainingParameterCompleteCreateDto(nameTrainingParameter="Nuevo", topics=["Tema"]), file, "session-user")
    elif flow == "initial":
        training.uploadPensum(12, file, "session-user")
    else:
        training.updatePensum(12, file, "session-user")
        assert baseline.isBaseline and baseline.createdByUserLogin is None and baseline.versionNumber == 1
        assert baseline.pensumPathTrainingParameterVersion != parameter.pensumPathTrainingParameter
    repository.db.commit.assert_called_once()
    storage.delete.assert_not_called()


@pytest.mark.parametrize("failure", ["insert", "commit", "refresh"])
def test_version_failure_rolls_back_and_never_deletes_objects(training, storage, failure):
    setOfficialPensum(training, storage)
    training.repository.appendVersion = TrainingParameterRepository.appendVersion.__get__(training.repository)
    training.repository.db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
    if failure == "insert":
        training.repository.db.flush.side_effect = IntegrityError("synthetic version constraint", {}, Exception())
        errorType = FileExistsError
    else:
        getattr(training.repository.db, failure).side_effect = RuntimeError("uncertain persistence")
        errorType = RuntimeError
    with pytest.raises(errorType):
        replacementUpload(training)
    training.repository.db.rollback.assert_called_once()
    if failure == "insert":
        training.repository.db.commit.assert_not_called()
    storage.delete.assert_not_called()


def test_versions_baseline_current_and_authorized_access(training, storage):
    parameter = setOfficialPensum(training, storage)
    baseline = versionSnapshot(parameter, baseline=True)
    replacementUpload(training)
    current = versionSnapshot(parameter, number=2)
    training.repository.getVersions = Mock(return_value=[current, baseline])
    versions = training.getVersions(12)
    assert [(v.versionNumber, v.isCurrent, v.isBaseline) for v in versions] == [(2, True, False), (1, False, True)]
    assert versions[1].createdByUserLogin is None
    training.repository.getVersion = Mock(return_value=baseline)
    assert "X-Goog-" in training.getVersionReadUrl(12, 1)
    training.repository.getVersion.assert_called_once_with(12, 1)
    training.repository.getVersion.return_value = None
    with pytest.raises(LookupError):
        training.getVersionReadUrl(99, 1)
    storage.upload.assert_called_once()
    storage.delete.assert_not_called()


def test_history_scope_reuses_event_rules_without_listing_events():
    repository = Mock()
    application = PensumHistoryApplication(repository)
    filters = dict(page=1, pageSize=20, search="", origin="all", versionState="all")
    application.getPage("owner", ["superadmin"], **filters)
    repository.getPage.assert_called_with(userLogin="owner", allEvents=False, **filters)
    application.getPage("admin", ["administrador"], **filters)
    repository.getPage.assert_called_with(userLogin="admin", allEvents=True, **filters)
    repository.getEvent.return_value = None
    with pytest.raises(LookupError):
        application.getLocalDocument(99, "owner", ["superadmin"])
    repository.getEvent.assert_called_once_with(99, "owner", False)


def test_history_queries_group_references_and_apply_scope_before_pagination():
    from sqlalchemy.orm import Session
    from sqlalchemy.dialects import mysql
    # Compile only: no connection, tables, schema changes or SQL execution.
    repository = PensumHistoryRepository(Session())
    query = repository._documents("owner", False, "Plan%", "parameterEvent", "previous")
    compiled = query.statement.compile(dialect=mysql.dialect())
    sql = str(compiled)
    assert "UNION ALL" in sql and "GROUP BY" in sql
    assert "createdByUserLogin" in sql and "owner" in compiled.params.values()
    assert "COLLATE utf8mb4_bin" in sql
    assert "parameterEvent" in compiled.params.values()
    assert "IS false" in sql
    assert "UPDATE" not in sql and "DELETE" not in sql


def test_history_page_groups_shared_document_and_limits_associations(training, storage):
    parameter = setOfficialPensum(training, storage)
    version = versionSnapshot(parameter, baseline=True)
    event = Event(IdEvent=7, titleEvent="Evento", IdTrainingParameter=12, createdAt=datetime(2026, 10, 20),
                  pensumPathEvent=parameter.pensumPathTrainingParameter)
    db = Mock()
    repository = PensumHistoryRepository(db)
    documents = Mock()
    repository._documents = Mock(return_value=documents)
    documents.count.return_value = 1
    documents.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [SimpleNamespace(reference=parameter.pensumPathTrainingParameter)]
    db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [(version, parameter)]
    events = Mock()
    repository._events = Mock(return_value=Mock(filter=Mock(return_value=events)))
    events.count.return_value = 25
    events.order_by.return_value.limit.return_value.all.return_value = [event]
    page = repository.getPage("admin", True, 2, 10, "", "all", "all")
    assert page["total"] == 1 and len(page["items"]) == 1
    assert page["items"][0]["eventCount"] == 25
    assert len(page["items"][0]["versions"]) == 1
    events.order_by.return_value.limit.assert_called_once_with(5)
    documents.order_by.return_value.offset.assert_called_once_with(10)
    db.commit.assert_not_called()
    db.flush.assert_not_called()


def test_history_local_document_containment_and_scoped_access(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    root = tmp_path / "uploads"
    root.mkdir()
    (root / "old.pdf").write_bytes(b"historical pdf")
    repository = Mock()
    repository.getEvent.return_value = SimpleNamespace(pensumPathEvent="/uploads/old.pdf", pensumOriginalNameEvent="old.pdf")
    application = PensumHistoryApplication(repository)
    path, name, mime = application.getLocalDocument(7, "owner", [])
    assert path == root / "old.pdf" and name == "old.pdf" and mime == "application/pdf"
    repository.getEvent.assert_called_with(7, "owner", False)
    repository.getEvent.return_value.pensumPathEvent = "/uploads/../../private.pdf"
    with pytest.raises(PermissionError):
        application.getLocalDocument(7, "owner", [])


def test_history_routes_require_both_admin_and_menu_permission():
    from fastapi import HTTPException
    application = Mock()
    application.getPage.return_value = dict(items=[], total=0, page=1, pageSize=20)
    app = FastAPI()
    app.include_router(historyRouter)
    app.dependency_overrides[getPensumHistoryApplication] = lambda: application
    app.dependency_overrides[historyPermission] = lambda: None
    with TestClient(app) as client:
        assert client.get("/pensum-history").status_code in (401, 403)
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["formador"], "userLogin": "owner"}
        assert client.get("/pensum-history").status_code == 403
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["administrador"], "userLogin": "admin"}
        def denied():
            raise HTTPException(403, "Missing menu permission")
        app.dependency_overrides[historyPermission] = denied
        assert client.get("/pensum-history").status_code == 403
        application.getPage.assert_not_called()
        app.dependency_overrides[historyPermission] = lambda: None
        assert client.get("/pensum-history").status_code == 200
        assert client.get("/pensum-history?pageSize=1000").status_code == 422
        assert client.get("/pensum-history/events?eventId=7&versionId=1").status_code == 400


def test_version_routes_check_admin_and_publication_author_comes_from_session(training, storage):
    setOfficialPensum(training, storage)
    app = FastAPI()
    app.include_router(trainingParameterRouter)
    app.dependency_overrides[getTrainingParameterApplication] = lambda: training
    with TestClient(app) as client:
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["formador"], "userLogin": "trainer"}
        assert client.get("/training-parameters/12/versions").status_code == 403
        assert client.get("/training-parameters/12/versions/1/pensum/access").status_code == 403
        app.dependency_overrides[getCurrentPayload] = lambda: {"roles": ["administrador"], "userLogin": "real-author"}
        response = client.put("/training-parameters/12/pensum", data={"createdByUserLogin": "forged"},
                              files={"file": ("Plan.pdf", b"new", "application/pdf")})
        assert response.status_code == 200
        assert training.repository.appendVersion.call_args.args[1] == "real-author"


def test_version_numbers_advance_from_current_locked_read_without_mutating_baseline(training, storage):
    parameter = setOfficialPensum(training, storage)
    baseline = versionSnapshot(parameter, baseline=True)
    repository = training.repository
    repository.appendVersion = TrainingParameterRepository.appendVersion.__get__(repository)
    latest = repository.db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first
    latest.return_value = baseline
    replacementUpload(training)
    second = repository.db.add.call_args.args[0]
    latest.return_value = second
    replacementUpload(training)
    third = repository.db.add.call_args.args[0]
    assert (baseline.versionNumber, second.versionNumber, third.versionNumber) == (1, 2, 3)
    assert len({baseline.pensumPathTrainingParameterVersion, second.pensumPathTrainingParameterVersion,
                third.pensumPathTrainingParameterVersion}) == 3
    assert baseline.isBaseline and baseline.createdByUserLogin is None
    assert repository.db.commit.call_count == 2
    assert repository.getById.call_args_list.count(((12,), {"forUpdate": True})) == 2
    storage.delete.assert_not_called()
