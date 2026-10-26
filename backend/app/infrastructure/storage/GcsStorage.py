"""Private GCS storage shared by application file flows.

HMAC signing follows Google's V4 specification using only hashlib/hmac:
https://cloud.google.com/storage/docs/authentication/signatures
https://cloud.google.com/storage/docs/authentication/canonical-requests
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
from urllib.parse import quote, urlsplit

import httpx

from app.domain.interfaces.IObjectStorage import IObjectStorage
from app.infrastructure.db.config import settings


class GcsConfigurationError(ValueError):
    pass


class GcsStorageError(RuntimeError):
    pass


class GcsObjectAlreadyExistsError(GcsStorageError):
    pass


def _utcNow() -> datetime:
    return datetime.now(timezone.utc)


class GcsStorage(IObjectStorage):
    """Synchronous adapter: use a FastAPI sync dependency/route or a threadpool.

    Only relative names under pensum/ and signatures/ are accepted. Callers own
    naming (prefer UUIDs); the server-side generation precondition prevents races.
    Signed URLs are bearer credentials: never log them or attach them to errors.
    """

    _ENVIRONMENTS = {
        "development": ("assistanceApp_dev/", "hmac"),
        "qa": ("assistanceApp_qa/", "adc"),
    }
    _ALGORITHM = "GOOG4-HMAC-SHA256"

    def __init__(self, configuration=settings, *, httpClient: httpx.Client | None = None):
        self._validateConfiguration(configuration)
        self._bucket = configuration.GCS_BUCKET
        self._prefix = configuration.GCS_PREFIX
        self._mode = configuration.GCS_AUTH_MODE
        self._endpoint = configuration.GCS_ENDPOINT.rstrip("/")
        self._timeout = configuration.GCS_TIMEOUT_SECONDS
        self._project = configuration.GCS_PROJECT_ID
        self._signingEmail = configuration.GCS_SIGNING_SERVICE_ACCOUNT_EMAIL or None
        self._httpClient = None
        self._ownsHttpClient = False
        self._adcClient = None
        self._adcCredentials = None
        if self._mode == "hmac":
            # Credentials come exclusively from backend Settings (SecretStr).
            self._accessKey = configuration.GCS_HMAC_ACCESS_KEY.get_secret_value()
            self._secretKey = configuration.GCS_HMAC_SECRET_KEY.get_secret_value()
            self._httpClient = httpClient if httpClient is not None else httpx.Client(
                timeout=self._timeout, follow_redirects=False, trust_env=False,
            )
            self._ownsHttpClient = httpClient is None
        else:
            self._initializeAdc()

    @staticmethod
    def _validateConfiguration(configuration) -> None:
        expected = GcsStorage._ENVIRONMENTS.get(configuration.GCS_ENVIRONMENT)
        if expected is None:
            raise GcsConfigurationError("Configure GCS_ENVIRONMENT como development o qa.")
        if configuration.GCS_PREFIX != expected[0]:
            raise GcsConfigurationError("GCS_PREFIX no corresponde al entorno GCS_ENVIRONMENT.")
        if configuration.GCS_AUTH_MODE != expected[1]:
            raise GcsConfigurationError("Development requiere GCS_AUTH_MODE=hmac; QA requiere adc.")
        if not configuration.GCS_BUCKET or not re.fullmatch(
            r"[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]", configuration.GCS_BUCKET,
        ):
            raise GcsConfigurationError("Configure un GCS_BUCKET válido.")
        if not configuration.GCS_PROJECT_ID or not re.fullmatch(
            r"[a-z][a-z0-9-]{4,61}[a-z0-9]", configuration.GCS_PROJECT_ID,
        ):
            raise GcsConfigurationError("Configure un GCS_PROJECT_ID válido.")
        if configuration.GCS_ENDPOINT.rstrip("/") != "https://storage.googleapis.com":
            raise GcsConfigurationError("GCS_ENDPOINT debe ser https://storage.googleapis.com.")
        if not 0 < configuration.GCS_TIMEOUT_SECONDS <= 120:
            raise GcsConfigurationError("GCS_TIMEOUT_SECONDS debe estar entre 0 y 120 segundos.")
        if configuration.GCS_SIGNING_SERVICE_ACCOUNT_EMAIL and not re.fullmatch(
            r"[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.gserviceaccount\.com",
            configuration.GCS_SIGNING_SERVICE_ACCOUNT_EMAIL,
        ):
            raise GcsConfigurationError("GCS_SIGNING_SERVICE_ACCOUNT_EMAIL no es válido.")
        if configuration.GCS_AUTH_MODE == "hmac":
            for name in ("GCS_HMAC_ACCESS_KEY", "GCS_HMAC_SECRET_KEY"):
                secret = getattr(configuration, name, None)
                if secret is None or not secret.get_secret_value().strip():
                    raise GcsConfigurationError(f"Falta {name} en el entorno privado del backend.")
                # Reject line breaks/whitespace without including the value in an error.
                if not re.fullmatch(r"[A-Za-z0-9+/=_-]+", secret.get_secret_value()):
                    raise GcsConfigurationError(f"El formato de {name} no es válido.")

    def _initializeAdc(self) -> None:
        try:
            import google.auth
            from google.cloud import storage

            self._adcCredentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            self._adcClient = storage.Client(
                project=self._project, credentials=self._adcCredentials,
                client_options={"api_endpoint": self._endpoint},
            )
        except ImportError:
            raise GcsConfigurationError("Instale google-cloud-storage para usar GCS_AUTH_MODE=adc.") from None
        except Exception:
            raise GcsConfigurationError("No fue posible obtener ADC. Revise la identidad de la VM.") from None

    def _objectName(self, relativePath: str) -> str:
        if not isinstance(relativePath, str) or len(relativePath) > 900:
            raise ValueError("La ruta relativa del objeto no es válida.")
        parts = relativePath.split("/")
        if len(parts) < 2 or parts[0] not in ("pensum", "signatures") or any(
            not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]{0,127}", part)
            for part in parts
        ):
            raise ValueError("Use una ruta relativa segura dentro de pensum/ o signatures/.")
        return self._prefix + relativePath

    def _objectUrl(self, objectName: str) -> str:
        return f"{self._endpoint}/{self._bucket}/{quote(objectName, safe='/~')}"

    def objectReference(self, relativePath: str) -> str:
        """Permanent reference for persistence; never contains credentials."""
        return f"gs://{self._bucket}/{self._objectName(relativePath)}"

    def relativePathFromReference(self, reference: str) -> str:
        root = f"gs://{self._bucket}/{self._prefix}"
        if not isinstance(reference, str) or not reference.startswith(root):
            raise ValueError("La referencia GCS no pertenece al bucket y entorno configurados.")
        relativePath = reference[len(root):]
        self._objectName(relativePath)
        return relativePath

    @staticmethod
    def _canonicalQuery(parameters: dict[str, str]) -> str:
        return "&".join(
            f"{quote(key, safe='~')}={quote(value, safe='~')}"
            for key, value in sorted(parameters.items())
        )

    def _signature(self, canonicalRequest: str, timestamp: str) -> str:
        date = timestamp[:8]
        scope = f"{date}/auto/storage/goog4_request"
        stringToSign = "\n".join((
            self._ALGORITHM, timestamp, scope,
            hashlib.sha256(canonicalRequest.encode("utf-8")).hexdigest(),
        ))
        key = ("GOOG4" + self._secretKey).encode("utf-8")
        for part in (date, "auto", "storage", "goog4_request"):
            key = hmac.new(key, part.encode("utf-8"), hashlib.sha256).digest()
        return hmac.new(key, stringToSign.encode("utf-8"), hashlib.sha256).hexdigest()

    def _hmacRequest(
        self, method: str, objectName: str, *, content: bytes = b"",
        extraHeaders: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = self._objectUrl(objectName)
        timestamp = _utcNow().strftime("%Y%m%dT%H%M%SZ")
        payloadHash = hashlib.sha256(content).hexdigest()
        headers = {
            "host": urlsplit(self._endpoint).netloc,
            "x-goog-date": timestamp,
            "x-goog-content-sha256": payloadHash,
            **(extraHeaders or {}),
        }
        canonicalHeaders = "".join(f"{key}:{' '.join(headers[key].split())}\n" for key in sorted(headers))
        signedHeaders = ";".join(sorted(headers))
        canonicalRequest = "\n".join((
            method, urlsplit(url).path, "", canonicalHeaders, signedHeaders, payloadHash,
        ))
        scope = f"{timestamp[:8]}/auto/storage/goog4_request"
        headers["authorization"] = (
            f"{self._ALGORITHM} Credential={self._accessKey}/{scope}, "
            f"SignedHeaders={signedHeaders}, Signature={self._signature(canonicalRequest, timestamp)}"
        )
        try:
            # Redirects could forward credentials outside the configured GCS endpoint.
            return self._httpClient.request(
                method, url, content=content, headers=headers,
                timeout=self._timeout, follow_redirects=False,
            )
        except httpx.HTTPError:
            raise GcsStorageError("No fue posible comunicarse con GCS.") from None

    @staticmethod
    def _checkResponse(response: httpx.Response, *, uploading: bool = False) -> None:
        if response.status_code == 412 and uploading:
            raise GcsObjectAlreadyExistsError("El objeto ya existe; no se permite sobrescribirlo.")
        if not 200 <= response.status_code < 300:
            # Never propagate response text, Authorization or full request exceptions.
            raise GcsStorageError(f"GCS rechazó la operación (HTTP {response.status_code}).")

    @staticmethod
    def _adcError(error: Exception, *, uploading: bool = False) -> None:
        if uploading and getattr(error, "code", None) == 412:
            raise GcsObjectAlreadyExistsError("El objeto ya existe; no se permite sobrescribirlo.") from None
        raise GcsStorageError("GCS no pudo completar la operación ADC; revise permisos y conectividad.") from None

    def upload(self, relativePath: str, content: bytes, contentType: str) -> int:
        objectName = self._objectName(relativePath)
        if not isinstance(content, bytes):
            raise ValueError("El contenido del objeto debe ser bytes.")
        if not isinstance(contentType, str) or not re.fullmatch(
            r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+(?:;[ \x21-\x7e]*)?", contentType,
        ):
            raise ValueError("Content-Type no es válido.")
        if self._mode == "hmac":
            response = self._hmacRequest("PUT", objectName, content=content, extraHeaders={
                "content-type": contentType,
                "cache-control": "private, no-store",
                "x-goog-if-generation-match": "0",
            })
            self._checkResponse(response, uploading=True)
            generation = response.headers.get("x-goog-generation")
        else:
            try:
                blob = self._adcClient.bucket(self._bucket).blob(objectName)
                blob.cache_control = "private, no-store"
                blob.upload_from_string(
                    content, content_type=contentType, if_generation_match=0,
                    timeout=self._timeout, retry=None,
                )
                generation = blob.generation
            except Exception as error:
                self._adcError(error, uploading=True)
        try:
            result = int(generation)
            if result <= 0:
                raise ValueError
            return result
        except (TypeError, ValueError):
            raise GcsStorageError("GCS no devolvió una generación válida para el objeto subido.") from None

    def exists(self, relativePath: str) -> bool:
        objectName = self._objectName(relativePath)
        if self._mode == "hmac":
            response = self._hmacRequest("HEAD", objectName)
            if response.status_code == 404:
                return False
            self._checkResponse(response)
            return True
        try:
            return self._adcClient.bucket(self._bucket).blob(objectName).exists(
                timeout=self._timeout, retry=None,
            )
        except Exception as error:
            self._adcError(error)

    def download(self, relativePath: str) -> bytes:
        objectName = self._objectName(relativePath)
        if self._mode == "hmac":
            response = self._hmacRequest("GET", objectName)
            if response.status_code == 404:
                raise FileNotFoundError("No se encontró el objeto solicitado.")
            self._checkResponse(response)
            return response.content
        try:
            return self._adcClient.bucket(self._bucket).blob(objectName).download_as_bytes(
                timeout=self._timeout, retry=None,
            )
        except Exception as error:
            if getattr(error, "code", None) == 404:
                raise FileNotFoundError("No se encontró el objeto solicitado.") from None
            self._adcError(error)

    def generateReadUrl(
        self, relativePath: str, expiresInSeconds: int = 300,
        *, fileName: str | None = None, download: bool = False,
    ) -> str:
        objectName = self._objectName(relativePath)
        # A deliberately short application policy, within Google's V4 7-day maximum.
        if type(expiresInSeconds) is not int or not 1 <= expiresInSeconds <= 3600:
            raise ValueError("La URL de lectura debe expirar entre 1 y 3600 segundos.")
        disposition = None
        if fileName:
            safeName = fileName.replace("\\", "/").rsplit("/", 1)[-1]
            disposition = (
                f"{'attachment' if download else 'inline'}; "
                f"filename*=UTF-8''{quote(safeName, safe='')}"
            )
        if self._mode == "hmac":
            url = self._objectUrl(objectName)
            timestamp = _utcNow().strftime("%Y%m%dT%H%M%SZ")
            scope = f"{timestamp[:8]}/auto/storage/goog4_request"
            parameters = {
                "X-Goog-Algorithm": self._ALGORITHM,
                "X-Goog-Credential": f"{self._accessKey}/{scope}",
                "X-Goog-Date": timestamp,
                "X-Goog-Expires": str(expiresInSeconds),
                "X-Goog-SignedHeaders": "host",
            }
            if disposition:
                parameters["response-content-disposition"] = disposition
            query = self._canonicalQuery(parameters)
            canonicalRequest = "\n".join((
                "GET", urlsplit(url).path, query,
                f"host:{urlsplit(self._endpoint).netloc}\n", "host", "UNSIGNED-PAYLOAD",
            ))
            return f"{url}?{query}&X-Goog-Signature={self._signature(canonicalRequest, timestamp)}"
        try:
            from google.auth.transport.requests import Request

            if not self._adcCredentials.valid:
                self._adcCredentials.refresh(Request())
            email = self._signingEmail or getattr(self._adcCredentials, "service_account_email", None)
            if not email or email == "default":
                raise GcsConfigurationError("ADC requiere el email de la cuenta de servicio firmante.")
            options = {} if disposition is None else {"response_disposition": disposition}
            return self._adcClient.bucket(self._bucket).blob(objectName).generate_signed_url(
                version="v4", expiration=timedelta(seconds=expiresInSeconds), method="GET",
                service_account_email=email, access_token=self._adcCredentials.token,
                api_access_endpoint=self._endpoint,
                **options,
            )
        except GcsConfigurationError:
            raise
        except Exception:
            raise GcsStorageError(
                "No fue posible firmar con ADC. Revise IAM Credentials API y iam.serviceAccounts.signBlob."
            ) from None

    def delete(self, relativePath: str, *, expectedGeneration: int | None = None) -> bool:
        objectName = self._objectName(relativePath)
        if expectedGeneration is not None and (
            type(expectedGeneration) is not int or expectedGeneration <= 0
        ):
            raise ValueError("La generación esperada debe ser un entero positivo.")
        if self._mode == "hmac":
            headers = {} if expectedGeneration is None else {
                "x-goog-if-generation-match": str(expectedGeneration)
            }
            response = self._hmacRequest("DELETE", objectName, extraHeaders=headers)
            if response.status_code == 404:
                return False
            self._checkResponse(response)
            return True
        try:
            options = {} if expectedGeneration is None else {"if_generation_match": expectedGeneration}
            self._adcClient.bucket(self._bucket).blob(objectName).delete(
                timeout=self._timeout, retry=None, **options,
            )
            return True
        except Exception as error:
            if getattr(error, "code", None) == 404:
                return False
            self._adcError(error)

    def close(self) -> None:
        if self._ownsHttpClient:
            self._httpClient.close()
        if self._adcClient is not None:
            self._adcClient.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
