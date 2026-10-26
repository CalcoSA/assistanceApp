"""Exercise the opt-in connection check entirely with fakes; never call GCS."""

import ast
import builtins
import importlib.util
import logging
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
import pytest


BACKEND_PATH = Path(__file__).resolve().parents[1]
TEST_ACCESS = "synthetic-check-access"
TEST_SECRET = "synthetic-check-secret"
TEST_SIGNED_URL = "https://storage.googleapis.com/calco-storage/test?X-Goog-Signature=synthetic-private-signature"
TEST_CONTENT = b"assistanceApp isolated GCS connection test; synthetic content only.\n"
TEST_RELATIVE_PATH = "pensum/_connection-tests/" + "1" * 32 + ".txt"


def loadCheckModule():
    spec = importlib.util.spec_from_file_location(
        "_gcs_connection_check_test_copy",
        BACKEND_PATH / "scripts/check_gcs_connection.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def checkHarness(monkeypatch):
    module = loadCheckModule()
    settings = SimpleNamespace(
        GCS_ENVIRONMENT="development",
        GCS_AUTH_MODE="hmac",
        GCS_PREFIX="assistanceApp_dev/",
        GCS_BUCKET="calco-storage",
        GCS_ENDPOINT="https://storage.googleapis.com",
        GCS_HMAC_ACCESS_KEY=SecretStr(TEST_ACCESS),
        GCS_HMAC_SECRET_KEY=SecretStr(TEST_SECRET),
        GCS_TIMEOUT_SECONDS=30,
    )
    configModule = ModuleType("app.infrastructure.db.config")
    configModule.settings = settings

    class ObjectAlreadyExistsError(RuntimeError):
        pass

    state = SimpleNamespace(present=False)

    def upload(relativePath, content, contentType):
        if state.present:
            raise ObjectAlreadyExistsError("simulated HTTP 412")
        state.present = True
        return 123

    def delete(relativePath, *, expectedGeneration):
        state.present = False
        return True

    storage = Mock()
    storage.upload.side_effect = upload
    storage.exists.side_effect = lambda relativePath: state.present
    storage.delete.side_effect = delete
    storage.generateReadUrl.return_value = TEST_SIGNED_URL
    storageFactory = Mock(return_value=storage)
    storageModule = ModuleType("app.infrastructure.storage.GcsStorage")
    storageModule.GcsStorage = storageFactory
    storageModule.GcsObjectAlreadyExistsError = ObjectAlreadyExistsError
    monkeypatch.setitem(sys.modules, "app.infrastructure.db.config", configModule)
    monkeypatch.setitem(sys.modules, "app.infrastructure.storage.GcsStorage", storageModule)

    anonymous = MagicMock()
    anonymous.__enter__.return_value = anonymous
    anonymous.get.side_effect = [
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=200, content=TEST_CONTENT),
        SimpleNamespace(status_code=400, content=b"<Error><Code>ExpiredToken</Code></Error>"),
    ]
    httpModule = ModuleType("httpx")
    httpModule.Client = Mock(return_value=anonymous)
    monkeypatch.setitem(sys.modules, "httpx", httpModule)
    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)
    monkeypatch.setattr(module, "uuid4", lambda: SimpleNamespace(hex="1" * 32))
    # The standalone script adjusts global logger state and sys.path. Isolate
    # those changes so these tests can also run beside other backend tests.
    monkeypatch.setattr(sys, "path", list(sys.path))
    for name in ("httpx", "httpcore", "urllib3", "google.auth"):
        logger = logging.getLogger(name)
        for attribute in ("disabled", "propagate", "level"):
            monkeypatch.setattr(logger, attribute, getattr(logger, attribute))
        monkeypatch.setattr(logger, "handlers", list(logger.handlers))
    return SimpleNamespace(
        module=module, settings=settings, storage=storage,
        storageFactory=storageFactory, anonymous=anonymous, httpModule=httpModule,
        sleep=sleep, collisionError=ObjectAlreadyExistsError, state=state,
    )


def assertNoSensitiveOutput(capsys, caplog):
    captured = capsys.readouterr()
    output = captured.out + captured.err + caplog.text
    for sensitive in (TEST_ACCESS, TEST_SECRET, TEST_SIGNED_URL, "synthetic-private-signature"):
        assert sensitive not in output
    return output


def test_without_run_flag_never_imports_configuration_or_http(monkeypatch, capsys):
    realImport = builtins.__import__

    def guardedImport(name, *args, **kwargs):
        if name.startswith("app.infrastructure") or name == "httpx":
            pytest.fail("Without --run the connection check must not load settings or HTTP")
        return realImport(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guardedImport)
    module = loadCheckModule()
    monkeypatch.setattr(sys, "argv", ["check_gcs_connection.py"])
    monkeypatch.setattr(module, "run", Mock(side_effect=AssertionError("run must remain opt-in")))
    assert module.main() == 0
    module.run.assert_not_called()
    assert "Sin --run" in capsys.readouterr().out


@pytest.mark.parametrize("name", ["GCS_HMAC_ACCESS_KEY", "GCS_HMAC_SECRET_KEY"])
@pytest.mark.parametrize("value", [None, SecretStr(""), SecretStr(" ")])
def test_missing_credentials_make_no_requests(checkHarness, name, value, capsys, caplog):
    setattr(checkHarness.settings, name, value)
    assert checkHarness.module.run() == 1
    checkHarness.storageFactory.assert_not_called()
    checkHarness.httpModule.Client.assert_not_called()
    assert name in assertNoSensitiveOutput(capsys, caplog)


@pytest.mark.parametrize("name, value", [
    ("GCS_ENVIRONMENT", "qa"),
    ("GCS_AUTH_MODE", "adc"),
    ("GCS_PREFIX", "assistanceApp_qa/"),
    ("GCS_PREFIX", "other-app/"),
    ("GCS_BUCKET", "other-bucket"),
    ("GCS_ENDPOINT", "http://storage.googleapis.com"),
])
def test_check_refuses_non_development_scope(checkHarness, name, value, capsys, caplog):
    setattr(checkHarness.settings, name, value)
    assert checkHarness.module.run() == 1
    checkHarness.storageFactory.assert_not_called()
    checkHarness.httpModule.Client.assert_not_called()
    assertNoSensitiveOutput(capsys, caplog)


@pytest.mark.parametrize("expirationStatus", [400, 403])
def test_happy_path_checks_privacy_expiration_and_deletes_only_created_generation(checkHarness, capsys, caplog, expirationStatus):
    checkHarness.anonymous.get.side_effect = [
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=200, content=TEST_CONTENT),
        SimpleNamespace(status_code=expirationStatus, content=b"<Error><Code>ExpiredToken</Code></Error>"),
    ]
    assert checkHarness.module.run() == 0
    storage = checkHarness.storage
    assert storage.upload.call_count == 2
    assert storage.upload.call_args_list[0].args == (TEST_RELATIVE_PATH, TEST_CONTENT, "text/plain; charset=utf-8")
    assert storage.upload.call_args_list[1].args[0] == TEST_RELATIVE_PATH
    storage.generateReadUrl.assert_called_once_with(TEST_RELATIVE_PATH, expiresInSeconds=8)
    storage.delete.assert_called_once_with(TEST_RELATIVE_PATH, expectedGeneration=123)
    storage.close.assert_called_once()
    checkHarness.sleep.assert_called_once_with(13)
    calls = checkHarness.anonymous.get.call_args_list
    assert len(calls) == 4
    objectName = "assistanceApp_dev/" + TEST_RELATIVE_PATH
    assert calls[0].args == ("https://storage.googleapis.com/calco-storage/" + objectName,)
    assert calls[1].kwargs == {"params": {"prefix": objectName, "max-keys": "1"}}
    assert calls[2].args == calls[3].args == (TEST_SIGNED_URL,)
    assert checkHarness.state.present is False
    assert "Prueba completada" in assertNoSensitiveOutput(capsys, caplog)


def test_initial_collision_never_deletes_preexisting_object(checkHarness, capsys, caplog):
    checkHarness.state.present = True
    assert checkHarness.module.run() == 1
    checkHarness.storage.upload.assert_called_once()
    checkHarness.storage.delete.assert_not_called()
    checkHarness.storage.close.assert_called_once()
    checkHarness.httpModule.Client.assert_not_called()
    assert checkHarness.state.present is True
    assert "No hay generacion confirmada" in assertNoSensitiveOutput(capsys, caplog)


def test_unexpired_signed_url_fails_but_still_cleans_own_generation(checkHarness, capsys, caplog):
    checkHarness.anonymous.get.side_effect = [
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=200, content=TEST_CONTENT),
        SimpleNamespace(status_code=200, content=TEST_CONTENT),
    ]
    assert checkHarness.module.run() == 1
    checkHarness.storage.delete.assert_called_once_with(TEST_RELATIVE_PATH, expectedGeneration=123)
    assert checkHarness.state.present is False
    assert "tras expirar" in assertNoSensitiveOutput(capsys, caplog)


@pytest.mark.parametrize("status, content", [
    (400, b"<Error><Code>InvalidArgument</Code></Error>"),
    (403, b"<Error><Code>AccessDenied</Code></Error>"),
    (400, b"invalid XML"),
    (200, b"<Error><Code>ExpiredToken</Code></Error>"),
])
def test_invalid_expiration_response_fails_and_cleans_own_object(checkHarness, capsys, caplog, status, content):
    checkHarness.anonymous.get.side_effect = [
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=403, content=b""),
        SimpleNamespace(status_code=200, content=TEST_CONTENT),
        SimpleNamespace(status_code=status, content=content),
    ]
    assert checkHarness.module.run() == 1
    checkHarness.storage.delete.assert_called_once_with(TEST_RELATIVE_PATH, expectedGeneration=123)
    assert "tras expirar" in assertNoSensitiveOutput(capsys, caplog)


@pytest.mark.parametrize("failureStage", ["initialize", "upload", "read", "delete", "close"])
def test_failures_never_print_credentials_urls_or_exception_details(checkHarness, failureStage, capsys, caplog):
    sensitiveError = RuntimeError(TEST_ACCESS + " " + TEST_SECRET + " " + TEST_SIGNED_URL)
    if failureStage == "initialize":
        checkHarness.storageFactory.side_effect = sensitiveError
    elif failureStage == "upload":
        checkHarness.storage.upload.side_effect = sensitiveError
    elif failureStage == "read":
        checkHarness.anonymous.get.side_effect = sensitiveError
    elif failureStage == "delete":
        checkHarness.storage.delete.side_effect = sensitiveError
    else:
        checkHarness.storage.close.side_effect = sensitiveError
    assert checkHarness.module.run() == 1
    assertNoSensitiveOutput(capsys, caplog)


def test_settings_validation_error_never_discloses_raw_hmac_inputs(monkeypatch):
    # Compile only the Settings class: importing config would instantiate its
    # global Settings and read .env. Empty os.environ prevents inherited values.
    source = (BACKEND_PATH / "app/infrastructure/db/config.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    settingsClass = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Settings")
    isolated = ast.Module(body=[settingsClass], type_ignores=[])
    namespace = {
        "BaseSettings": BaseSettings, "SettingsConfigDict": SettingsConfigDict,
        "Field": Field, "SecretStr": SecretStr, "__name__": "_isolated_gcs_config_test",
    }
    exec(compile(isolated, "isolated_settings_for_test", "exec"), namespace)
    monkeypatch.setattr(os, "environ", {})
    with pytest.raises(ValidationError) as error:
        namespace["Settings"](
            _env_file=None,
            GCS_HMAC_ACCESS_KEY=TEST_ACCESS,
            GCS_HMAC_SECRET_KEY=TEST_SECRET,
        )
    assert "DB_HOST" in str(error.value)
    assert TEST_ACCESS not in str(error.value)
    assert TEST_SECRET not in str(error.value)
