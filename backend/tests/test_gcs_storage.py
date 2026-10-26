"""Isolated GCS contract tests: no real settings, credentials, files, or network."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import importlib.util
from pathlib import Path
import sys
import traceback
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import httpx
from pydantic import SecretStr
import pytest


TEST_ACCESS_KEY = "unit-test-access"
TEST_SECRET_KEY = "unit-test-secret"
FIXED_TIME = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def configuration():
    return SimpleNamespace(
        GCS_ENVIRONMENT="development",
        GCS_AUTH_MODE="hmac",
        GCS_BUCKET="calco-storage",
        GCS_PREFIX="assistanceApp_dev/",
        GCS_PROJECT_ID="calco-sa-508817",
        GCS_ENDPOINT="https://storage.googleapis.com",
        GCS_HMAC_ACCESS_KEY=SecretStr(TEST_ACCESS_KEY),
        GCS_HMAC_SECRET_KEY=SecretStr(TEST_SECRET_KEY),
        GCS_SIGNING_SERVICE_ACCOUNT_EMAIL=None,
        GCS_TIMEOUT_SECONDS=30,
    )


@pytest.fixture
def storageModule(configuration, monkeypatch):
    # Import a private copy with stubbed configuration so Settings() never reads
    # a developer's .env; restoration also avoids affecting unrelated tests.
    configStub = ModuleType("app.infrastructure.db.config")
    configStub.settings = configuration
    monkeypatch.setitem(sys.modules, "app.infrastructure.db.config", configStub)
    modulePath = (
        Path(__file__).resolve().parents[1]
        / "app/infrastructure/storage/GcsStorage.py"
    )
    spec = importlib.util.spec_from_file_location("_gcs_storage_test_copy", modulePath)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_utcNow", lambda: FIXED_TIME)
    return module


@pytest.fixture
def buildStorage(storageModule, configuration):
    clients = []

    def build(handler=None):
        if handler is None:
            def handler(request):
                pytest.fail("This operation must not perform an HTTP request")
        client = httpx.Client(transport=httpx.MockTransport(handler))
        clients.append(client)
        return storageModule.GcsStorage(configuration, httpClient=client)

    yield build
    for client in clients:
        client.close()


def assertSignedRequest(request):
    """Verify the transmitted request using Google's documented V4 algorithm."""
    authorization = request.headers["authorization"]
    assert authorization.startswith("GOOG4-HMAC-SHA256 ")
    components = dict(
        part.strip().split("=", 1)
        for part in authorization.removeprefix("GOOG4-HMAC-SHA256 ").split(",")
    )
    credential = components["Credential"]
    assert credential == TEST_ACCESS_KEY + "/20261009/auto/storage/goog4_request"
    signedHeaders = components["SignedHeaders"]
    headerNames = signedHeaders.split(";")
    assert headerNames == sorted(headerNames)
    assert "host" in headerNames
    assert "x-goog-date" in headerNames
    canonicalHeaders = "".join(
        name + ":" + " ".join(request.headers[name].split()) + "\n"
        for name in headerNames
    )
    payloadHash = hashlib.sha256(request.content).hexdigest()
    assert request.headers["x-goog-content-sha256"] == payloadHash
    canonicalRequest = "\n".join([
        request.method,
        request.url.path,
        request.url.query.decode("ascii"),
        canonicalHeaders,
        signedHeaders,
        payloadHash,
    ])
    scope = credential.split("/", 1)[1]
    stringToSign = "\n".join([
        "GOOG4-HMAC-SHA256",
        "20261009T120000Z",
        scope,
        hashlib.sha256(canonicalRequest.encode()).hexdigest(),
    ])
    signingKey = ("GOOG4" + TEST_SECRET_KEY).encode()
    for value in scope.split("/"):
        signingKey = hmac.new(signingKey, value.encode(), hashlib.sha256).digest()
    expected = hmac.new(signingKey, stringToSign.encode(), hashlib.sha256).hexdigest()
    assert hmac.compare_digest(components["Signature"], expected)


def test_upload_signs_content_type_and_prevents_overwrite(buildStorage):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, headers={"x-goog-generation": "123"})

    storage = buildStorage(handler)
    generation = storage.upload("pensum/event-1/document.docx", b"test document", "application/octet-stream")
    assert generation == 123
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "PUT"
    assert str(request.url) == "https://storage.googleapis.com/calco-storage/assistanceApp_dev/pensum/event-1/document.docx"
    assert request.content == b"test document"
    assert request.headers["content-type"] == "application/octet-stream"
    assert request.headers["x-goog-if-generation-match"] == "0"
    assert "content-type" in request.headers["authorization"]
    assert "x-goog-if-generation-match" in request.headers["authorization"]
    assertSignedRequest(request)


def test_upload_collision_is_not_retried_or_overwritten(buildStorage, storageModule):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(412, text="sensitive provider detail")

    with pytest.raises(storageModule.GcsObjectAlreadyExistsError):
        buildStorage(handler).upload("signatures/test.png", b"test", "image/png")
    assert len(requests) == 1
    assert requests[0].headers["x-goog-if-generation-match"] == "0"


@pytest.mark.parametrize("contentType", ["", "text", "text/plain\r\nAuthorization: injected", "text/\u00e1", None])
def test_upload_rejects_invalid_content_type_before_http(buildStorage, contentType):
    with pytest.raises(ValueError):
        buildStorage().upload("pensum/test.txt", b"test", contentType)


@pytest.mark.parametrize("generation", [None, "", "not-a-generation", "0", "-1"])
def test_upload_requires_a_usable_generation_for_safe_cleanup(buildStorage, storageModule, generation):
    headers = {} if generation is None else {"x-goog-generation": generation}
    with pytest.raises(storageModule.GcsStorageError):
        buildStorage(lambda request: httpx.Response(200, headers=headers)).upload(
            "pensum/test.txt", b"test", "text/plain"
        )


@pytest.mark.parametrize("status, expected", [(200, True), (404, False)])
def test_exists_uses_signed_head(buildStorage, status, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status)

    assert buildStorage(handler).exists("pensum/test.xlsx") is expected
    assert len(requests) == 1
    assert requests[0].method == "HEAD"
    assertSignedRequest(requests[0])


@pytest.mark.parametrize("status, expected", [(204, True), (404, False)])
def test_delete_uses_signed_delete_and_generation_precondition(buildStorage, status, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status)

    assert buildStorage(handler).delete("signatures/test.png", expectedGeneration=123) is expected
    assert len(requests) == 1
    assert requests[0].method == "DELETE"
    assert requests[0].headers["x-goog-if-generation-match"] == "123"
    assertSignedRequest(requests[0])


def test_delete_generation_mismatch_does_not_retry(buildStorage, storageModule):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(412)

    with pytest.raises(storageModule.GcsStorageError):
        buildStorage(handler).delete("pensum/test.txt", expectedGeneration=123)
    assert len(requests) == 1


@pytest.mark.parametrize("generation", [0, -1, True, 1.5, "123"])
def test_delete_rejects_invalid_generation_before_http(buildStorage, generation):
    with pytest.raises(ValueError):
        buildStorage().delete("pensum/test.txt", expectedGeneration=generation)


def test_signed_read_url_matches_fixed_v4_vector_without_http(buildStorage, caplog):
    signedUrl = buildStorage().generateReadUrl("pensum/smoke.txt", expiresInSeconds=60)
    parsed = urlsplit(signedUrl)
    assert parsed.scheme == "https"
    assert parsed.netloc == "storage.googleapis.com"
    assert parsed.path == "/calco-storage/assistanceApp_dev/pensum/smoke.txt"
    assert parse_qs(parsed.query) == {
        "X-Goog-Algorithm": ["GOOG4-HMAC-SHA256"],
        "X-Goog-Credential": [TEST_ACCESS_KEY + "/20261009/auto/storage/goog4_request"],
        "X-Goog-Date": ["20261009T120000Z"],
        "X-Goog-Expires": ["60"],
        "X-Goog-SignedHeaders": ["host"],
        "X-Goog-Signature": ["1ae332faa10a5db2cc3f62b12c3ccb10bbb8cbc1534596b592aa2e6050785cbd"],
    }
    assert TEST_SECRET_KEY not in signedUrl
    assert signedUrl not in caplog.text
    assert TEST_ACCESS_KEY not in caplog.text
    assert TEST_SECRET_KEY not in caplog.text


@pytest.mark.parametrize("duration", [0, -1, 3601, 604800, True, 1.5, "60", None])
def test_signed_url_rejects_invalid_expiration(buildStorage, duration):
    with pytest.raises(ValueError):
        buildStorage().generateReadUrl("pensum/test.txt", expiresInSeconds=duration)


@pytest.mark.parametrize("duration", [1, 3600])
def test_signed_url_accepts_expiration_boundaries(buildStorage, duration):
    query = parse_qs(urlsplit(buildStorage().generateReadUrl("pensum/test.txt", duration)).query)
    assert query["X-Goog-Expires"] == [str(duration)]


@pytest.mark.parametrize("relativePath", [
    "", "pensum", "pensum/", "../secret", "pensum/../secret", "pensum/./test",
    "/pensum/test", "pensum//test", "pensum\\test", "pensum/%2e%2e/test",
    "pensum/a?query", "pensum/a#fragment", "pensum/has space", "pensum/\u00e1.docx",
    "pensum/\nfile", "pensum/.hidden", "pensum/" + "a" * 129,
    "pensum/" + "/".join(["a" * 127] * 8),
    "assistanceApp_qa/pensum/test", "assistanceApp_dev/pensum/test",
    "other-app/test", "uploads/test", "gs://calco-storage/pensum/test", None,
])
@pytest.mark.parametrize("operation", ["upload", "exists", "generateReadUrl", "delete"])
def test_all_operations_reject_unsafe_or_unscoped_paths(buildStorage, relativePath, operation):
    storage = buildStorage()
    args = (relativePath, b"test", "text/plain") if operation == "upload" else (relativePath,)
    with pytest.raises(ValueError):
        getattr(storage, operation)(*args)


@pytest.mark.parametrize("changes", [
    {"GCS_PREFIX": "assistanceApp_qa/"},
    {"GCS_PREFIX": "other-app/"},
    {"GCS_PREFIX": "assistanceApp_dev/pensum/"},
    {"GCS_PREFIX": "assistanceApp_dev/../assistanceApp_qa/"},
    {"GCS_ENVIRONMENT": "production"},
    {"GCS_AUTH_MODE": "adc"},
    {"GCS_AUTH_MODE": "automatic"},
    {"GCS_ENVIRONMENT": "qa", "GCS_PREFIX": "assistanceApp_qa/"},
    {"GCS_ENDPOINT": "http://storage.googleapis.com"},
    {"GCS_ENDPOINT": "https://storage.googleapis.com.attacker.test"},
    {"GCS_BUCKET": "calco-storage/other-app"},
])
def test_constructor_rejects_mixed_environments_and_unsafe_configuration(storageModule, configuration, changes):
    for key, value in changes.items():
        setattr(configuration, key, value)
    with pytest.raises(storageModule.GcsConfigurationError):
        storageModule.GcsStorage(configuration)


@pytest.mark.parametrize("key", ["GCS_HMAC_ACCESS_KEY", "GCS_HMAC_SECRET_KEY"])
@pytest.mark.parametrize("value", [None, SecretStr("")])
def test_development_requires_explicit_hmac_credentials_without_fallback(storageModule, configuration, monkeypatch, key, value):
    setattr(configuration, key, value)
    adc = Mock(side_effect=AssertionError("ADC fallback is forbidden"))
    monkeypatch.setattr(storageModule.GcsStorage, "_initializeAdc", adc)
    with pytest.raises(storageModule.GcsConfigurationError) as error:
        storageModule.GcsStorage(configuration)
    assert "HMAC" in str(error.value)
    assert TEST_SECRET_KEY not in str(error.value)
    adc.assert_not_called()


@pytest.mark.parametrize("operation", ["upload", "exists", "delete"])
@pytest.mark.parametrize("status", [301, 403, 500])
def test_provider_failures_are_sanitized_and_never_follow_redirects(buildStorage, storageModule, operation, status, caplog):
    requests = []
    sensitive = TEST_SECRET_KEY + " https://example.test/?X-Goog-Signature=secret-signature"

    def handler(request):
        requests.append(request)
        return httpx.Response(status, text=sensitive, headers={"Location": "https://example.test/"})

    storage = buildStorage(handler)
    args = ("pensum/test.txt", b"test", "text/plain") if operation == "upload" else ("pensum/test.txt",)
    with pytest.raises(storageModule.GcsStorageError) as error:
        getattr(storage, operation)(*args)
    output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert sensitive not in output
    assert TEST_SECRET_KEY not in output
    assert "secret-signature" not in output
    assert len(requests) == 1


def test_transport_errors_do_not_expose_request_credentials(buildStorage, storageModule, caplog):
    def handler(request):
        raise httpx.ConnectError(TEST_SECRET_KEY + " signed-url=private", request=request)

    with pytest.raises(storageModule.GcsStorageError) as error:
        buildStorage(handler).exists("pensum/test.txt")
    output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert TEST_SECRET_KEY not in output
    assert "signed-url=private" not in output


@pytest.fixture
def adcStorage(storageModule, configuration, monkeypatch):
    configuration.GCS_ENVIRONMENT = "qa"
    configuration.GCS_AUTH_MODE = "adc"
    configuration.GCS_PREFIX = "assistanceApp_qa/"
    configuration.GCS_HMAC_ACCESS_KEY = None
    configuration.GCS_HMAC_SECRET_KEY = None
    configuration.GCS_SIGNING_SERVICE_ACCOUNT_EMAIL = "qa-storage@calco-sa-508817.iam.gserviceaccount.com"
    credentials = SimpleNamespace(valid=True, token="adc-test-token", service_account_email=configuration.GCS_SIGNING_SERVICE_ACCOUNT_EMAIL)
    blob = Mock()
    blob.generation = "321"
    blob.exists.return_value = True
    blob.generate_signed_url.return_value = "https://storage.googleapis.com/test?X-Goog-Signature=test"
    client = Mock()
    client.bucket.return_value.blob.return_value = blob

    def initialize(instance):
        instance._adcClient = client
        instance._adcCredentials = credentials

    monkeypatch.setattr(storageModule.GcsStorage, "_initializeAdc", initialize)
    return SimpleNamespace(storage=storageModule.GcsStorage(configuration), client=client, blob=blob, credentials=credentials)


def test_signature_download_hmac_uses_authenticated_request(buildStorage):
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/calco-storage/assistanceApp_dev/signatures/7/test.png"
        assertSignedRequest(request)
        return httpx.Response(200, content=b"synthetic image")
    assert buildStorage(handler).download("signatures/7/test.png") == b"synthetic image"


@pytest.mark.parametrize("statusCode", [404, 403, 500])
def test_signature_download_hmac_sanitizes_errors(buildStorage, storageModule, statusCode):
    storage = buildStorage(lambda request: httpx.Response(statusCode, text="private details"))
    errorType = FileNotFoundError if statusCode == 404 else storageModule.GcsStorageError
    with pytest.raises(errorType) as error:
        storage.download("signatures/7/test.png")
    assert "private details" not in str(error.value)


def test_signature_download_adc_uses_private_qa_prefix(adcStorage):
    adcStorage.blob.download_as_bytes.return_value = b"synthetic image"
    assert adcStorage.storage.download("signatures/7/test.png") == b"synthetic image"
    adcStorage.client.bucket.return_value.blob.assert_called_once_with("assistanceApp_qa/signatures/7/test.png")
    adcStorage.blob.download_as_bytes.assert_called_once_with(timeout=30, retry=None)


@pytest.mark.parametrize("code", [404, 403])
def test_signature_download_adc_sanitizes_errors(adcStorage, storageModule, code):
    error = RuntimeError("private details")
    error.code = code
    adcStorage.blob.download_as_bytes.side_effect = error
    with pytest.raises(FileNotFoundError if code == 404 else storageModule.GcsStorageError) as result:
        adcStorage.storage.download("signatures/7/test.png")
    assert "private details" not in str(result.value)


def test_signature_download_rejects_unsafe_path_before_network(buildStorage):
    with pytest.raises(ValueError):
        buildStorage().download("signatures/7/../../../private.png")


def test_qa_adc_upload_uses_qa_prefix_and_generation_precondition(adcStorage):
    generation = adcStorage.storage.upload("pensum/test.xlsx", b"test spreadsheet", "application/octet-stream")
    assert generation == 321
    adcStorage.client.bucket.assert_called_with("calco-storage")
    adcStorage.client.bucket.return_value.blob.assert_called_with("assistanceApp_qa/pensum/test.xlsx")
    adcStorage.blob.upload_from_string.assert_called_once_with(b"test spreadsheet", content_type="application/octet-stream", if_generation_match=0, timeout=30, retry=None)


def test_qa_adc_exists_and_conditional_delete(adcStorage):
    assert adcStorage.storage.exists("signatures/test.png") is True
    adcStorage.blob.exists.assert_called_once_with(timeout=30, retry=None)
    assert adcStorage.storage.delete("signatures/test.png", expectedGeneration=321) is True
    adcStorage.blob.delete.assert_called_once_with(if_generation_match=321, timeout=30, retry=None)


def test_qa_adc_signed_url_uses_vm_token_for_iam_signing(adcStorage, caplog):
    signedUrl = adcStorage.storage.generateReadUrl("pensum/test.xlsx", expiresInSeconds=60)
    assert signedUrl == adcStorage.blob.generate_signed_url.return_value
    kwargs = adcStorage.blob.generate_signed_url.call_args.kwargs
    assert kwargs["version"] == "v4"
    assert kwargs["method"] == "GET"
    assert kwargs["expiration"] == timedelta(seconds=60)
    assert kwargs["service_account_email"] == adcStorage.credentials.service_account_email
    assert kwargs["access_token"] == adcStorage.credentials.token
    assert signedUrl not in caplog.text
    assert adcStorage.credentials.token not in caplog.text


def test_qa_adc_refreshes_expired_vm_token_before_signing(adcStorage):
    adcStorage.credentials.valid = False

    def refresh(request):
        adcStorage.credentials.token = "refreshed-adc-test-token"
        adcStorage.credentials.valid = True

    adcStorage.credentials.refresh = Mock(side_effect=refresh)
    adcStorage.storage.generateReadUrl("pensum/test.xlsx")
    adcStorage.credentials.refresh.assert_called_once()
    kwargs = adcStorage.blob.generate_signed_url.call_args.kwargs
    assert kwargs["access_token"] == "refreshed-adc-test-token"


def test_qa_adc_without_resolved_signer_fails_clearly(adcStorage, storageModule):
    adcStorage.storage._signingEmail = None
    adcStorage.credentials.service_account_email = "default"
    with pytest.raises(storageModule.GcsConfigurationError):
        adcStorage.storage.generateReadUrl("pensum/test.xlsx")
    adcStorage.blob.generate_signed_url.assert_not_called()


def test_qa_adc_errors_do_not_fallback_or_expose_tokens(adcStorage, storageModule, caplog):
    adcStorage.blob.exists.side_effect = RuntimeError("private adc-test-token detail")
    with pytest.raises(storageModule.GcsStorageError) as error:
        adcStorage.storage.exists("pensum/test.txt")
    output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert "adc-test-token" not in output
    adcStorage.blob.exists.assert_called_once()


def test_qa_adc_maps_not_found_and_precondition_failures(adcStorage, storageModule):
    from google.api_core.exceptions import NotFound, PreconditionFailed

    adcStorage.blob.delete.side_effect = NotFound("sensitive missing detail")
    assert adcStorage.storage.delete("pensum/test.txt", expectedGeneration=321) is False
    adcStorage.blob.upload_from_string.side_effect = PreconditionFailed("sensitive collision detail")
    with pytest.raises(storageModule.GcsObjectAlreadyExistsError):
        adcStorage.storage.upload("pensum/test.txt", b"test", "text/plain")


def test_adc_initialization_uses_google_identity_scope_and_configured_endpoint(storageModule, configuration, monkeypatch):
    import google.auth
    from google.cloud import storage

    configuration.GCS_ENVIRONMENT = "qa"
    configuration.GCS_AUTH_MODE = "adc"
    configuration.GCS_PREFIX = "assistanceApp_qa/"
    configuration.GCS_HMAC_ACCESS_KEY = None
    configuration.GCS_HMAC_SECRET_KEY = None
    credentials = object()
    discoverCredentials = Mock(return_value=(credentials, "identity-project"))
    createClient = Mock()
    monkeypatch.setattr(google.auth, "default", discoverCredentials)
    monkeypatch.setattr(storage, "Client", createClient)
    service = storageModule.GcsStorage(configuration)
    discoverCredentials.assert_called_once_with(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    createClient.assert_called_once_with(
        project="calco-sa-508817", credentials=credentials,
        client_options={"api_endpoint": "https://storage.googleapis.com"},
    )
    service.close()
    createClient.return_value.close.assert_called_once()


def test_adc_initialization_failure_never_falls_back_to_available_hmac_credentials(storageModule, configuration, monkeypatch, caplog):
    import google.auth
    from google.cloud import storage

    configuration.GCS_ENVIRONMENT = "qa"
    configuration.GCS_AUTH_MODE = "adc"
    configuration.GCS_PREFIX = "assistanceApp_qa/"
    # Leave synthetic HMAC values present: explicit ADC must still fail.
    discoverCredentials = Mock(side_effect=RuntimeError(TEST_SECRET_KEY + " sensitive ADC detail"))
    createClient = Mock()
    hmacClient = Mock(side_effect=AssertionError("HMAC fallback is forbidden"))
    monkeypatch.setattr(google.auth, "default", discoverCredentials)
    monkeypatch.setattr(storage, "Client", createClient)
    monkeypatch.setattr(storageModule.httpx, "Client", hmacClient)
    with pytest.raises(storageModule.GcsConfigurationError) as error:
        storageModule.GcsStorage(configuration)
    createClient.assert_not_called()
    hmacClient.assert_not_called()
    assert "ADC" in str(error.value)
    output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert TEST_SECRET_KEY not in output
    assert "sensitive ADC detail" not in output
