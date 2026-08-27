from app.application.interfaces.IOnlyOfficeApplication import IOnlyOfficeApplication
from app.domain.dtos.OnlyOfficeDto import OnlyOfficePreviewResponseDto
from app.domain.interfaces.IEventRepository import IEventRepository
from app.infrastructure.db.config import settings
from datetime import datetime, timedelta, timezone
from fastapi import UploadFile
from pathlib import Path
from urllib.parse import quote
import hashlib
import jwt
import mimetypes
import time
import uuid


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

    def __init__(self, eventRepository: IEventRepository):
        self.eventRepository = eventRepository
        self.uploadRoot = Path(settings.UPLOAD_DIR).resolve()
        self.previewDirectory = self.uploadRoot / "pensum-previews"

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
        self._cleanupExpiredTemporaryFiles()

        fileContent = file.file.read()

        if not fileContent:
            raise ValueError("El archivo seleccionado está vacío.")

        self.previewDirectory.mkdir(parents=True, exist_ok=True)
        temporaryFileName = f"{uuid.uuid4().hex}{extension}"
        temporaryFilePath = self.previewDirectory / temporaryFileName
        temporaryFilePath.write_bytes(fileContent)

        relativePath = temporaryFilePath.relative_to(self.uploadRoot).as_posix()

        return self._buildPreviewResponse(
            relativePath=relativePath,
            originalFileName=originalFileName,
            extension=extension,
            userLogin=userLogin,
        )

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
        storedFilePath = self._resolveStoredPath(relativePath)

        if not storedFilePath.is_file():
            raise ValueError("No se encontró el archivo solicitado.")

        mimeType = mimetypes.guess_type(originalFileName)[0] or "application/octet-stream"

        return str(storedFilePath), originalFileName, mimeType

    def _buildPreviewResponse(
        self,
        relativePath: str,
        originalFileName: str,
        extension: str,
        userLogin: str,
    ) -> OnlyOfficePreviewResponseDto:
        storedFilePath = self._resolveStoredPath(relativePath)
        fileStat = storedFilePath.stat()
        fileAccessToken = self._createFileAccessToken(relativePath, originalFileName)
        storageBaseUrl = settings.ONLYOFFICE_STORAGE_BASE_URL.rstrip("/")
        fileUrl = (
            f"{storageBaseUrl}/onlyoffice/files/"
            f"{quote(fileAccessToken, safe='')}"
        )
        documentKeySource = (
            f"assistance-app:{relativePath}:{fileStat.st_size}:"
            f"{fileStat.st_mtime_ns}"
        )
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

    def _createFileAccessToken(self, relativePath: str, originalFileName: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ONLYOFFICE_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "scope": "onlyoffice_pensum_file",
            "path": relativePath,
            "name": Path(originalFileName).name,
            "exp": expire,
        }

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

    def _cleanupExpiredTemporaryFiles(self) -> None:
        if not self.previewDirectory.exists():
            return

        expirationThreshold = time.time() - (
            settings.ONLYOFFICE_TEMP_FILE_EXPIRE_MINUTES * 60
        )

        for temporaryFile in self.previewDirectory.iterdir():
            if temporaryFile.is_file() and temporaryFile.stat().st_mtime < expirationThreshold:
                temporaryFile.unlink(missing_ok=True)

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

