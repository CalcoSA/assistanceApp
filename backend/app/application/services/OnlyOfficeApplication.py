from app.application.interfaces.IOnlyOfficeApplication import IOnlyOfficeApplication
from app.domain.dtos.OnlyOfficeDto import OnlyOfficePreviewResponseDto
from app.domain.interfaces.IEventRepository import IEventRepository
from app.infrastructure.db.config import settings
from app.infrastructure.storage.GcsStorage import GcsStorage
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager, contextmanager
from fastapi import UploadFile
from pathlib import Path
from urllib.parse import quote
import hashlib
import asyncio
import errno
import jwt
import logging
import mimetypes
import os
import re
import tempfile
import time
import uuid


logger = logging.getLogger(__name__)
TEMPORARY_CLEANUP_INTERVAL_SECONDS = 300


@asynccontextmanager
async def temporaryPensumLifespan(app):
    service = OnlyOfficeApplication(None)
    stop = asyncio.Event()

    async def cleanup():
        try:
            await asyncio.to_thread(service._cleanupExpiredTemporaryFiles)
        except OSError:
            logger.exception("No fue posible limpiar los temporales de OnlyOffice")

    async def periodicallyCleanup():
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), TEMPORARY_CLEANUP_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                await cleanup()

    await cleanup()
    task = asyncio.create_task(periodicallyCleanup(), name="onlyoffice-temporary-cleanup")
    try:
        yield
    finally:
        stop.set()
        await task


class OnlyOfficeApplication(IOnlyOfficeApplication):

    VIEW_ALL_ROLES = {"administrador"}
    WORD_EXTENSIONS = {
        ".doc", ".docm", ".docx", ".odt", ".rtf", ".txt",
    }
    CELL_EXTENSIONS = {
        ".csv", ".ods", ".xls", ".xlsb", ".xlsm", ".xlsx",
    }
    SLIDE_EXTENSIONS = {
        ".odp", ".ppt", ".pptm", ".pptx",
    }
    SUPPORTED_EXTENSIONS = WORD_EXTENSIONS | CELL_EXTENSIONS | SLIDE_EXTENSIONS

    def __init__(self, eventRepository: IEventRepository | None):
        self.eventRepository = eventRepository
        self.uploadRoot = Path(settings.UPLOAD_DIR).resolve()
        backendDirectory = Path(__file__).resolve().parents[3]
        installationId = hashlib.sha256(str(backendDirectory).encode()).hexdigest()[:16]
        previewDirectory = Path(settings.ONLYOFFICE_TEMP_DIR) if settings.ONLYOFFICE_TEMP_DIR else (
            Path(tempfile.gettempdir()) / f"assistanceapp-onlyoffice-{installationId}"
        )
        self.previewDirectory = previewDirectory.resolve()
        for publicDirectory in (self.uploadRoot, (backendDirectory / "uploads").resolve()):
            if self.previewDirectory == publicDirectory or publicDirectory in self.previewDirectory.parents:
                raise RuntimeError("ONLYOFFICE_TEMP_DIR debe estar fuera de uploads.")

    def createTemporaryPensumPreview(
        self,
        file: UploadFile,
        userLogin: str,
    ) -> OnlyOfficePreviewResponseDto:
        self._validateConfiguration()

        if not file or not file.filename:
            raise ValueError("Debe adjuntar un archivo para previsualizar.")

        originalFileName = Path(file.filename).name
        extension = Path(originalFileName).suffix.lower()
        self._validateExtension(extension)

        fileContent = file.file.read()

        if not fileContent:
            raise ValueError("El archivo seleccionado está vacío.")

        with self._temporaryFilesLock():
            temporaryFileName = f"preview-{uuid.uuid4().hex}{extension}"
            temporaryFilePath = self.previewDirectory / temporaryFileName
            descriptor = os.open(temporaryFilePath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(descriptor, "wb") as temporaryFile:
                    temporaryFile.write(fileContent)
                return self._buildPreviewResponse(
                    relativePath=temporaryFileName,
                    originalFileName=originalFileName,
                    extension=extension,
                    userLogin=userLogin,
                    storage="temporary",
                )
            except Exception:
                temporaryFilePath.unlink(missing_ok=True)
                raise

    def createEventPensumPreview(
        self,
        IdEvent: int,
        userLogin: str,
        roles: list[str],
    ) -> OnlyOfficePreviewResponseDto:
        self._validateConfiguration()
        eventFound = self.eventRepository.getById(IdEvent)

        if not eventFound:
            raise ValueError("El evento no existe.")

        if not self._userCanAccessEvent(eventFound.createdByUserLogin, userLogin, roles):
            raise PermissionError("No tiene permisos para consultar este PENSUM.")

        if not eventFound.pensumPathEvent:
            raise ValueError("El evento no tiene un PENSUM adjunto.")

        originalFileName = (
            eventFound.pensumOriginalNameEvent
            or Path(eventFound.pensumPathEvent).name
        )
        extension = Path(originalFileName).suffix.lower()
        self._validateExtension(extension)
        if eventFound.pensumPathEvent.startswith("gs://"):
            return self._buildPreviewResponse(
                relativePath=eventFound.pensumPathEvent,
                originalFileName=originalFileName,
                extension=extension,
                userLogin=userLogin,
                storage="gcs",
            )
        storedFilePath = self._resolveStoredPath(eventFound.pensumPathEvent)

        if not storedFilePath.is_file():
            raise ValueError("No se encontró el archivo PENSUM en el servidor.")

        relativePath = storedFilePath.relative_to(self.uploadRoot).as_posix()

        return self._buildPreviewResponse(
            relativePath=relativePath,
            originalFileName=originalFileName,
            extension=extension,
            userLogin=userLogin,
        )

    def resolveFileAccess(self, accessToken: str) -> tuple[str, str, str]:
        try:
            payload = jwt.decode(
                accessToken,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError as error:
            raise PermissionError("El enlace de previsualización expiró.") from error
        except jwt.InvalidTokenError as error:
            raise PermissionError("El enlace de previsualización no es válido.") from error

        if payload.get("scope") != "onlyoffice_pensum_file":
            raise PermissionError("El enlace de previsualización no es válido.")

        relativePath = str(payload.get("path") or "")
        originalFileName = Path(str(payload.get("name") or "documento")).name
        storedFilePath = self._resolveFilePath(relativePath, payload.get("storage", "uploads"))

        if not storedFilePath.is_file():
            raise ValueError("No se encontró el archivo solicitado.")

        mimeType = mimetypes.guess_type(originalFileName)[0] or "application/octet-stream"

        return str(storedFilePath), originalFileName, mimeType

    def readTemporaryFile(self, filePath: str) -> bytes:
        # Copy under the cross-process lock before handing the response to ASGI.
        # Cleanup can then remove the disk file without interrupting the download.
        with self._temporaryFilesLock():
            storedFilePath = self._resolveTemporaryPath(Path(filePath).name)
            if storedFilePath != Path(filePath):
                raise PermissionError("La ruta del archivo no es válida.")
            try:
                return storedFilePath.read_bytes()
            except FileNotFoundError as error:
                raise ValueError("No se encontró el archivo solicitado.") from error

    def _buildPreviewResponse(
        self,
        relativePath: str,
        originalFileName: str,
        extension: str,
        userLogin: str,
        storage: str = "uploads",
    ) -> OnlyOfficePreviewResponseDto:
        if storage == "gcs":
            with GcsStorage() as objectStorage:
                objectPath = objectStorage.relativePathFromReference(relativePath)
                if not objectPath.startswith("pensum/"):
                    raise ValueError("La referencia no corresponde a un PENSUM.")
                if not objectStorage.exists(objectPath):
                    raise ValueError("No se encontró el archivo PENSUM en GCS.")
                fileUrl = objectStorage.generateReadUrl(
                    objectPath,
                    expiresInSeconds=min(3600, max(1, settings.ONLYOFFICE_TOKEN_EXPIRE_MINUTES * 60)),
                )
            # Object names are unique and never overwritten, so the permanent
            # reference is a stable document key independent of URL expiration.
            documentKeySource = f"assistance-app:{relativePath}"
        else:
            storedFilePath = self._resolveFilePath(relativePath, storage)
            fileStat = storedFilePath.stat()
            fileAccessToken = self._createFileAccessToken(relativePath, originalFileName, storage)
            storageBaseUrl = settings.ONLYOFFICE_STORAGE_BASE_URL.rstrip("/")
            fileUrl = (
                f"{storageBaseUrl}/onlyoffice/files/"
                f"{quote(fileAccessToken, safe='')}"
            )
            documentKeySource = (
                f"assistance-app:{relativePath}:{fileStat.st_size}:"
                f"{fileStat.st_mtime_ns}"
            )
        if storage == "temporary":
            documentKeySource = f"temporary:{documentKeySource}"
        documentKey = hashlib.sha256(documentKeySource.encode("utf-8")).hexdigest()
        config = {
            "documentType": self._getDocumentType(extension),
            "type": "desktop",
            "height": "100%",
            "width": "100%",
            "document": {
                "fileType": extension.lstrip("."),
                "key": documentKey,
                "title": originalFileName[:128],
                "url": fileUrl,
                "permissions": {
                    "chat": False,
                    "comment": False,
                    "copy": True,
                    "download": True,
                    "edit": False,
                    "fillForms": False,
                    "print": True,
                    "protect": False,
                    "review": False,
                },
            },
            "editorConfig": {
                "coEditing": {
                    "mode": "strict",
                    "change": False,
                },
                "lang": "es",
                "mode": "view",
                "region": "es-CO",
                "user": {
                    "id": hashlib.sha256(userLogin.encode("utf-8")).hexdigest()[:32],
                    "name": userLogin,
                },
            },
        }
        tokenPayload = config.copy()
        tokenPayload["exp"] = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ONLYOFFICE_TOKEN_EXPIRE_MINUTES
        )
        config["token"] = jwt.encode(
            tokenPayload,
            settings.ONLYOFFICE_JWT_SECRET,
            algorithm="HS256",
        )

        return OnlyOfficePreviewResponseDto(
            documentServerUrl=settings.ONLYOFFICE_PUBLIC_URL.rstrip("/"),
            config=config,
        )

    def _createFileAccessToken(
        self, relativePath: str, originalFileName: str, storage: str = "uploads",
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ONLYOFFICE_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "scope": "onlyoffice_pensum_file",
            "path": relativePath,
            "name": Path(originalFileName).name,
            "exp": expire,
        }
        if storage == "temporary":
            payload["storage"] = storage

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def _resolveStoredPath(self, storedPath: str) -> Path:
        normalizedPath = storedPath.replace("\\", "/").lstrip("/")

        if normalizedPath.startswith("uploads/"):
            normalizedPath = normalizedPath[len("uploads/"):]

        resolvedPath = (self.uploadRoot / normalizedPath).resolve()

        if resolvedPath != self.uploadRoot and self.uploadRoot not in resolvedPath.parents:
            raise PermissionError("La ruta del archivo no es válida.")

        return resolvedPath

    def _resolveFilePath(self, storedPath: str, storage: str) -> Path:
        if storage == "temporary":
            return self._resolveTemporaryPath(storedPath)
        if storage == "uploads":
            return self._resolveStoredPath(storedPath)
        raise PermissionError("El almacenamiento del archivo no es válido.")

    def _isManagedTemporaryName(self, name: str) -> bool:
        return bool(re.fullmatch(r"preview-[0-9a-f]{32}\.[a-z0-9]+", name)) and (
            Path(name).suffix in self.SUPPORTED_EXTENSIONS
        )

    def _resolveTemporaryPath(self, name: str) -> Path:
        if not self._isManagedTemporaryName(name):
            raise PermissionError("La ruta temporal no es válida.")
        candidate = self.previewDirectory / name
        if candidate.is_symlink() or candidate.resolve().parent != self.previewDirectory:
            raise PermissionError("La ruta temporal no es válida.")
        try:
            if self._isExpired(candidate.stat().st_mtime):
                raise ValueError("El archivo temporal expiró.")
        except FileNotFoundError as error:
            raise ValueError("No se encontró el archivo solicitado.") from error
        return candidate

    def _isExpired(self, modifiedAt: float) -> bool:
        return modifiedAt <= time.time() - settings.ONLYOFFICE_TEMP_FILE_EXPIRE_MINUTES * 60

    @contextmanager
    def _temporaryFilesLock(self, blocking: bool = True):
        # One stable lock file coordinates all requests and backend workers.
        # Never delete it: replacing its inode would break mutual exclusion.
        self.previewDirectory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != "nt":
            self.previewDirectory.chmod(0o700)
        descriptor = os.open(self.previewDirectory / ".cleanup.lock", os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(descriptor, "r+b") as lockFile:
            if os.name == "nt":
                import msvcrt

                def acquire():
                    lockFile.seek(0)
                    msvcrt.locking(lockFile.fileno(), msvcrt.LK_NBLCK, 1)

                def release():
                    lockFile.seek(0)
                    msvcrt.locking(lockFile.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                def acquire():
                    fcntl.flock(lockFile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                def release():
                    fcntl.flock(lockFile.fileno(), fcntl.LOCK_UN)

            while True:
                try:
                    acquire()
                    break
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                        raise
                    if not blocking:
                        yield False
                        return
                    time.sleep(0.01)
            try:
                yield True
            finally:
                release()

    def _cleanupExpiredTemporaryFiles(self) -> None:
        with self._temporaryFilesLock(blocking=False) as acquired:
            if not acquired:
                return
            for temporaryFile in self.previewDirectory.iterdir():
                if not self._isManagedTemporaryName(temporaryFile.name) or temporaryFile.is_symlink():
                    continue
                try:
                    if temporaryFile.is_file() and self._isExpired(temporaryFile.stat().st_mtime):
                        temporaryFile.unlink(missing_ok=True)
                except FileNotFoundError:
                    pass
                except OSError:
                    logger.exception("No fue posible eliminar el temporal %s", temporaryFile.name)

    def _validateConfiguration(self) -> None:
        if not settings.ONLYOFFICE_JWT_SECRET:
            raise RuntimeError("ONLYOFFICE_JWT_SECRET no está configurado en el backend.")

        if not settings.ONLYOFFICE_PUBLIC_URL:
            raise RuntimeError("ONLYOFFICE_PUBLIC_URL no está configurado en el backend.")

        if not settings.ONLYOFFICE_STORAGE_BASE_URL:
            raise RuntimeError("ONLYOFFICE_STORAGE_BASE_URL no está configurado en el backend.")

    def _validateExtension(self, extension: str) -> None:
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "OnlyOffice permite previsualizar archivos Word, Excel, "
                "PowerPoint, OpenDocument, RTF, CSV o TXT."
            )

    def _getDocumentType(self, extension: str) -> str:
        if extension in self.WORD_EXTENSIONS:
            return "word"

        if extension in self.CELL_EXTENSIONS:
            return "cell"

        if extension in self.SLIDE_EXTENSIONS:
            return "slide"

        raise ValueError("El formato del documento no es compatible con OnlyOffice.")

    def _userCanAccessEvent(
        self,
        createdByUserLogin: str,
        userLogin: str,
        roles: list[str],
    ) -> bool:
        normalizedRoles = {
            str(role).strip().lower()
            for role in roles
            if str(role).strip()
        }

        return (
            bool(normalizedRoles & self.VIEW_ALL_ROLES)
            or createdByUserLogin == userLogin
        )
