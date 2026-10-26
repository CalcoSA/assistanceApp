import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import importlib
import multiprocessing
import os
from pathlib import Path
import threading
import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.api.onlyOfficeController import (
    getCurrentAuthContext,
    getOnlyOfficeApplication,
    getOnlyOfficeFile,
    router,
)
from app.application.services.OnlyOfficeApplication import (
    OnlyOfficeApplication,
    temporaryPensumLifespan,
)
from app.infrastructure.db.config import settings


applicationModule = importlib.import_module(
    "app.application.services.OnlyOfficeApplication"
)


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "ONLYOFFICE_TEMP_DIR", str(tmp_path / "private"))
    monkeypatch.setattr(settings, "ONLYOFFICE_TEMP_FILE_EXPIRE_MINUTES", 60)
    monkeypatch.setattr(settings, "ONLYOFFICE_TOKEN_EXPIRE_MINUTES", 30)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-file-access-secret-" * 3)
    monkeypatch.setattr(settings, "ONLYOFFICE_JWT_SECRET", "test-onlyoffice-secret-" * 3)
    monkeypatch.setattr(settings, "ONLYOFFICE_PUBLIC_URL", "http://office.test")
    monkeypatch.setattr(settings, "ONLYOFFICE_STORAGE_BASE_URL", "http://backend.test")
    instance = OnlyOfficeApplication(None)
    instance.uploadRoot.mkdir()
    return instance


def createPreview(service, extension=".docx"):
    return service.createTemporaryPensumPreview(
        UploadFile(filename=f"Pénsum{extension}", file=BytesIO(b"document contents")),
        "tester",
    )


def tokenFrom(preview):
    return preview.config["document"]["url"].rsplit("/", 1)[1]


def storedFile(service, preview):
    return Path(service.resolveFileAccess(tokenFrom(preview))[0])


def age(file, seconds=3601):
    modified = time.time() - seconds
    os.utime(file, (modified, modified))


def clientFor(service):
    app = FastAPI()
    app.include_router(router)
    app.mount("/uploads", StaticFiles(directory=service.uploadRoot))
    app.dependency_overrides[getOnlyOfficeApplication] = lambda: service
    app.dependency_overrides[getCurrentAuthContext] = lambda: {
        "userLogin": "tester", "roles": [],
    }
    return TestClient(app)


@pytest.mark.parametrize("extension", sorted(OnlyOfficeApplication.SUPPORTED_EXTENSIONS))
def test_supported_formats_keep_signed_configuration_and_private_delivery(service, extension):
    preview = createPreview(service, extension)
    token = tokenFrom(preview)
    file = storedFile(service, preview)
    assert file.parent == service.previewDirectory
    assert service.uploadRoot not in file.parents
    assert preview.documentServerUrl == "http://office.test"
    assert preview.config["documentType"] == service._getDocumentType(extension)
    signedConfig = jwt.decode(
        preview.config["token"], settings.ONLYOFFICE_JWT_SECRET, algorithms=["HS256"]
    )
    assert signedConfig["document"] == preview.config["document"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["storage"] == "temporary"
    assert payload["path"] == file.name
    with clientFor(service) as client:
        response = client.get(f"/onlyoffice/files/{token}")
        assert response.status_code == 200
        assert response.content == b"document contents"
        assert "filename*=" in response.headers["content-disposition"]
        assert client.get(f"/uploads/pensum-previews/{file.name}").status_code == 404
        assert client.get(f"/uploads/{file.name}").status_code == 404


def test_react_preview_endpoint_contract(service):
    with clientFor(service) as client:
        response = client.post(
            "/onlyoffice/pensum/preview",
            files={"file": ("pensum.xlsx", b"spreadsheet")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["isSuccess"] is True
        assert payload["result"]["config"]["documentType"] == "cell"


def test_cleanup_only_expired_managed_files_and_preserves_legacy(service, monkeypatch):
    expired = storedFile(service, createPreview(service))
    fresh = storedFile(service, createPreview(service))
    boundary = storedFile(service, createPreview(service))
    unrelated = service.previewDirectory / "notes.docx"
    unrelated.write_bytes(b"keep")
    legacy = service.uploadRoot / "pensum-previews" / ("a" * 32 + ".docx")
    legacy.parent.mkdir()
    legacy.write_bytes(b"legacy")
    folder = service.previewDirectory / ("preview-" + "b" * 32 + ".docx")
    folder.mkdir()
    for file in (expired, unrelated, legacy, folder):
        age(file)
    now = time.time()
    os.utime(boundary, (now - 3599, now - 3599))
    monkeypatch.setattr(applicationModule.time, "time", lambda: now)
    service._cleanupExpiredTemporaryFiles()
    service._cleanupExpiredTemporaryFiles()
    assert not expired.exists()
    assert all(file.exists() for file in (fresh, boundary, unrelated, legacy, folder))


@pytest.mark.parametrize("relative", [
    "../secret.docx", "/etc/passwd", "C:\\secret.docx", "notes.docx",
    "preview-" + "a" * 32 + ".exe", "../private/preview-" + "a" * 32 + ".docx",
])
def test_signed_temporary_tokens_cannot_escape_private_storage(service, relative):
    token = service._createFileAccessToken(relative, "document.docx", "temporary")
    with clientFor(service) as client:
        assert client.get(f"/onlyoffice/files/{token}").status_code == 403


def test_rejects_invalid_scope_signature_storage_and_expired_tokens(service):
    valid = tokenFrom(createPreview(service))
    payload = jwt.decode(valid, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    with clientFor(service) as client:
        for change in ({"scope": "other"}, {"storage": "other"}, {"exp": 1}):
            token = jwt.encode(payload | change, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            assert client.get(f"/onlyoffice/files/{token}").status_code == 403
        token = jwt.encode(payload, "incorrect-secret-" * 3, algorithm=settings.JWT_ALGORITHM)
        assert client.get(f"/onlyoffice/files/{token}").status_code == 403


def test_expired_and_deleted_files_return_404(service):
    preview = createPreview(service)
    file = storedFile(service, preview)
    age(file)
    with clientFor(service) as client:
        assert client.get(f"/onlyoffice/files/{tokenFrom(preview)}").status_code == 404
        file.unlink()
        assert client.get(f"/onlyoffice/files/{tokenFrom(preview)}").status_code == 404


def test_existing_event_uses_original_storage_and_file_response(service):
    file = service.uploadRoot / "pensum" / "saved.xlsx"
    file.parent.mkdir()
    file.write_bytes(b"saved spreadsheet")
    age(file, 86400)
    event = SimpleNamespace(
        createdByUserLogin="tester", pensumPathEvent="uploads/pensum/saved.xlsx",
        pensumOriginalNameEvent="saved.xlsx",
    )
    service.eventRepository = SimpleNamespace(getById=lambda eventId: event)
    with clientFor(service) as client:
        result = client.get("/onlyoffice/pensum/events/42")
        assert result.status_code == 200
        token = result.json()["result"]["config"]["document"]["url"].rsplit("/", 1)[1]
        service._cleanupExpiredTemporaryFiles()
        assert isinstance(getOnlyOfficeFile(token, service), FileResponse)
        assert client.get(f"/onlyoffice/files/{token}").content == b"saved spreadsheet"
    assert file.exists()
    with pytest.raises(PermissionError):
        service.createEventPensumPreview(42, "another-user", [])


def test_cleanup_skips_an_active_read_and_response_survives_later_deletion(service, monkeypatch):
    preview = createPreview(service)
    file = storedFile(service, preview)
    originalRead = Path.read_bytes
    entered = threading.Event()
    release = threading.Event()

    def pausedRead(path):
        if path == file:
            entered.set()
            assert release.wait(5)
        return originalRead(path)

    monkeypatch.setattr(Path, "read_bytes", pausedRead)
    with ThreadPoolExecutor() as executor:
        responseFuture = executor.submit(getOnlyOfficeFile, tokenFrom(preview), service)
        try:
            assert entered.wait(5)
            age(file)
            OnlyOfficeApplication(None)._cleanupExpiredTemporaryFiles()
            assert file.exists()
        finally:
            release.set()
        response = responseFuture.result(timeout=5)
    service._cleanupExpiredTemporaryFiles()
    assert not file.exists()
    assert response.body == b"document contents"


def cleanupInWorker(uploadDirectory, previewDirectory, connection):
    settings.UPLOAD_DIR = uploadDirectory
    settings.ONLYOFFICE_TEMP_DIR = previewDirectory
    try:
        OnlyOfficeApplication(None)._cleanupExpiredTemporaryFiles()
        connection.send("ok")
    finally:
        connection.close()


def test_cleanup_respects_other_process_lock(service):
    file = storedFile(service, createPreview(service))
    age(file)
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    worker = context.Process(
        target=cleanupInWorker,
        args=(str(service.uploadRoot), str(service.previewDirectory), sender),
    )
    with service._temporaryFilesLock():
        worker.start()
        try:
            assert receiver.poll(15)
            assert receiver.recv() == "ok"
            assert file.exists()
        finally:
            worker.join(5)
            if worker.is_alive():
                worker.terminate()
                worker.join(5)
            sender.close()
            receiver.close()
    assert worker.exitcode == 0
    service._cleanupExpiredTemporaryFiles()
    assert not file.exists()


def test_concurrent_cleanup_and_missing_file_race_are_harmless(service, monkeypatch):
    files = [storedFile(service, createPreview(service)) for _ in range(8)]
    for file in files:
        age(file)
    originalUnlink = Path.unlink

    def alreadyRemoved(path, *args, **kwargs):
        originalUnlink(path, *args, **kwargs)
        raise FileNotFoundError(str(path))

    monkeypatch.setattr(Path, "unlink", alreadyRemoved)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda _: service._cleanupExpiredTemporaryFiles(), range(4)))
    assert not any(file.exists() for file in files)


def test_lifespan_cleans_at_start_periodically_without_requests_and_stops(service, monkeypatch):
    expired = storedFile(service, createPreview(service))
    age(expired)
    monkeypatch.setattr(applicationModule, "TEMPORARY_CLEANUP_INTERVAL_SECONDS", 0.02)

    async def run():
        async with temporaryPensumLifespan(FastAPI()):
            assert not expired.exists()
            another = storedFile(service, createPreview(service))
            age(another)
            for _ in range(100):
                if not another.exists():
                    break
                await asyncio.sleep(0.01)
            assert not another.exists()
            tasks = [task for task in asyncio.all_tasks() if task.get_name() == "onlyoffice-temporary-cleanup"]
            assert len(tasks) == 1
        assert tasks[0].done()

    asyncio.run(run())


def test_lifespan_retries_after_cleanup_error(service, monkeypatch):
    expired = storedFile(service, createPreview(service))
    age(expired)
    originalCleanup = OnlyOfficeApplication._cleanupExpiredTemporaryFiles
    calls = []

    def failOnce(instance):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("temporary storage unavailable")
        originalCleanup(instance)

    monkeypatch.setattr(OnlyOfficeApplication, "_cleanupExpiredTemporaryFiles", failOnce)
    monkeypatch.setattr(applicationModule, "TEMPORARY_CLEANUP_INTERVAL_SECONDS", 0.02)

    async def run():
        async with temporaryPensumLifespan(FastAPI()):
            for _ in range(100):
                if not expired.exists():
                    break
                await asyncio.sleep(0.01)
            assert not expired.exists()

    asyncio.run(run())
    assert len(calls) >= 2


def test_private_directory_cannot_be_configured_under_uploads(service, monkeypatch):
    for directory in (service.uploadRoot, service.uploadRoot / "nested"):
        monkeypatch.setattr(settings, "ONLYOFFICE_TEMP_DIR", str(directory))
        with pytest.raises(RuntimeError, match="fuera de uploads"):
            OnlyOfficeApplication(None)


def test_default_directory_is_private_and_stable_across_instances(service, monkeypatch):
    monkeypatch.setattr(settings, "ONLYOFFICE_TEMP_DIR", None)
    first = OnlyOfficeApplication(None)
    second = OnlyOfficeApplication(None)
    assert first.previewDirectory == second.previewDirectory
    assert first.previewDirectory.name.startswith("assistanceapp-onlyoffice-")
    assert first.uploadRoot not in first.previewDirectory.parents


def test_lifespan_shutdown_waits_for_running_cleanup(service, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    completed = threading.Event()
    calls = []

    def slowCleanup(instance):
        calls.append(1)
        if len(calls) > 1:
            entered.set()
            assert release.wait(5)
            completed.set()

    monkeypatch.setattr(OnlyOfficeApplication, "_cleanupExpiredTemporaryFiles", slowCleanup)
    monkeypatch.setattr(applicationModule, "TEMPORARY_CLEANUP_INTERVAL_SECONDS", 0.01)

    async def run():
        lifespan = temporaryPensumLifespan(FastAPI())
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


def test_symlink_is_never_served_or_cleaned(service):
    outside = service.uploadRoot / "keep.docx"
    outside.write_bytes(b"keep")
    age(outside)
    service.previewDirectory.mkdir()
    link = service.previewDirectory / ("preview-" + "c" * 32 + ".docx")
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks is not permitted on this platform")
    token = service._createFileAccessToken(link.name, "document.docx", "temporary")
    with pytest.raises(PermissionError):
        service.resolveFileAccess(token)
    service._cleanupExpiredTemporaryFiles()
    assert link.is_symlink()
    assert outside.exists()
