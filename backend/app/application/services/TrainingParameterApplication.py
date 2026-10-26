from datetime import datetime
import logging
import uuid
from types import SimpleNamespace
from app.domain.dtos.PensumHistoryDto import TrainingParameterVersionResponseDto

from app.application.interfaces.ITrainingParameterApplication import ITrainingParameterApplication
from app.application.services.PensumFile import readPensumUpload
from app.domain.dtos.TrainingParameterDto import (
    TrainingParameterCompleteCreateDto, TrainingParameterCreateDto, TrainingParameterUpdateDto,
)
from app.domain.entities.ParameterTopic import ParameterTopic
from app.domain.entities.TrainingParameter import TrainingParameter
from app.domain.interfaces.ITrainingParameterRepository import ITrainingParameterRepository
from app.infrastructure.db.config import APP_TIMEZONE_INFO
from app.infrastructure.storage.GcsStorage import GcsStorage

logger = logging.getLogger(__name__)


class TrainingParameterApplication(ITrainingParameterApplication):
    def __init__(self, repository: ITrainingParameterRepository):
        self.repository = repository

    @staticmethod
    def _now():
        return datetime.now(APP_TIMEZONE_INFO).replace(tzinfo=None)

    def getAll(self, isActive=None):
        return self.repository.getAll(isActive)

    def getById(self, IdTrainingParameter):
        parameter = self.repository.getById(IdTrainingParameter)
        if not parameter:
            raise LookupError("El parámetro de capacitación no existe.")
        return parameter

    def _checkName(self, name, IdTrainingParameter=None):
        existing = self.repository.getByName(name)
        if existing and existing.IdTrainingParameter != IdTrainingParameter:
            raise ValueError("Ya existe un parámetro con ese nombre.")

    def create(self, data: TrainingParameterCreateDto):
        if data.isActive:
            raise ValueError("Cree el parámetro inactivo y adjunte su PÉNSUM antes de activarlo.")
        self._checkName(data.nameTrainingParameter)
        return self.repository.create(TrainingParameter(
            nameTrainingParameter=data.nameTrainingParameter, isActive=False,
            createdAt=self._now(),
            topics=[
                ParameterTopic(nameParameterTopic=name, sortOrder=order)
                for order, name in enumerate(data.topics)
            ],
        ))

    def createComplete(self, data: TrainingParameterCompleteCreateDto, file, userLogin=None):
        document = self._readOfficialPensum(file)
        self._checkName(data.nameTrainingParameter)
        parameter = TrainingParameter(
            nameTrainingParameter=data.nameTrainingParameter, isActive=False,
            createdAt=self._now(),
            topics=[
                ParameterTopic(nameParameterTopic=name, sortOrder=order)
                for order, name in enumerate(data.topics)
            ],
        )
        uploadAttempt = {}

        def prepare(pendingParameter):
            self._attachOfficialPensum(pendingParameter, document, uploadAttempt)
            pendingParameter.validateReady()
            pendingParameter.isActive = True
            self.repository.appendVersion(pendingParameter, userLogin)

        try:
            return self.repository.createComplete(parameter, prepare)
        except Exception:
            if uploadAttempt:
                # Neither a failed upload nor rollback proves that the remote operation failed.
                # Conservatively retain this UUID object, including after commit/refresh errors.
                logger.warning(
                    "Creación completa sin confirmación; conservar PÉNSUM para revisión | "
                    "IdTrainingParameter=%s reference=%s generation=%s",
                    uploadAttempt["id"], uploadAttempt["reference"], uploadAttempt.get("generation"),
                    exc_info=True,
                )
            raise

    def update(self, IdTrainingParameter, data: TrainingParameterUpdateDto):
        def applyChanges(parameter):
            if data.nameTrainingParameter is not None:
                self._checkName(data.nameTrainingParameter, IdTrainingParameter)
                parameter.nameTrainingParameter = data.nameTrainingParameter
            if data.isActive is not None:
                parameter.isActive = data.isActive
            if parameter.isActive:
                parameter.validateReady(data.topics)
                if data.isActive is True:
                    # Activation also confirms the object still exists in this environment.
                    with GcsStorage() as storage:
                        path = self._documentPath(parameter, storage)
                        if not storage.exists(path):
                            raise ValueError("No se encontró el PÉNSUM oficial en GCS.")
            parameter.updatedAt = self._now()
        return self.repository.update(IdTrainingParameter, applyChanges, data.topics)

    @staticmethod
    def _documentPath(parameter, storage):
        reference = parameter.pensumPathTrainingParameter
        if not reference:
            raise ValueError("El parámetro no tiene un PÉNSUM oficial.")
        path = storage.relativePathFromReference(reference)
        prefix = f"pensum/parameters/{parameter.IdTrainingParameter}/"
        if not path.startswith(prefix) or "/" in path[len(prefix):]:
            raise ValueError("La referencia no corresponde al PÉNSUM de este parámetro.")
        return path

    @staticmethod
    def _readOfficialPensum(file):
        name, extension, content, mime = readPensumUpload(file)
        if len(content) > 2147483647:
            raise ValueError("El tamaño del archivo supera el límite permitido.")
        return name, extension, content, mime

    def _attachOfficialPensum(self, parameter, document, uploadAttempt=None):
        name, extension, content, mime = document
        path = f"pensum/parameters/{parameter.IdTrainingParameter}/{uuid.uuid4().hex}{extension}"
        with GcsStorage() as storage:
            reference = storage.objectReference(path)
            if len(reference) > 500:
                raise ValueError("La referencia del PÉNSUM supera 500 caracteres.")
            if uploadAttempt is not None:
                uploadAttempt.update(id=parameter.IdTrainingParameter, reference=reference)
            generation = storage.upload(path, content, mime)
            if uploadAttempt is not None:
                uploadAttempt["generation"] = generation
        parameter.pensumPathTrainingParameter = reference
        parameter.pensumOriginalNameTrainingParameter = name
        parameter.pensumMimeTypeTrainingParameter = mime
        parameter.pensumSizeTrainingParameter = len(content)
        parameter.updatedAt = self._now()

    def uploadPensum(self, IdTrainingParameter, file, userLogin=None):
        parameter = self.getById(IdTrainingParameter)
        if parameter.pensumPathTrainingParameter:
            raise FileExistsError("El PÉNSUM oficial ya existe; no se permite reemplazarlo.")
        document = self._readOfficialPensum(file)

        def attach(lockedParameter):
            if lockedParameter.pensumPathTrainingParameter:
                raise FileExistsError("El PÉNSUM oficial ya existe; no se permite reemplazarlo.")
            # Serialize competing initial uploads with the same parent lock used by events.
            self._attachOfficialPensum(lockedParameter, document)
            self.repository.appendVersion(lockedParameter, userLogin)

        try:
            return self.repository.update(IdTrainingParameter, attach)
        except (ValueError, LookupError, FileExistsError):
            raise
        except Exception:
            # Upload/commit/refresh failure can have an uncertain outcome. Never delete.
            logger.warning(
                "Carga oficial sin confirmación; se conservan objetos para revisión | IdTrainingParameter=%s",
                IdTrainingParameter,
            )
            raise

    def updatePensum(self, IdTrainingParameter, file, userLogin=None):
        parameter = self.getById(IdTrainingParameter)
        # Capture a scalar: the locking read refreshes this same ORM instance.
        previousReference = parameter.pensumPathTrainingParameter
        if not previousReference:
            raise ValueError("El parámetro no tiene PÉNSUM oficial. Utilice la carga inicial.")
        document = self._readOfficialPensum(file)
        uploadAttempt = {}

        def replace(lockedParameter):
            if lockedParameter.pensumPathTrainingParameter != previousReference:
                raise FileExistsError(
                    "Otro administrador actualizó el PÉNSUM. Consulte el parámetro antes de reintentar."
                )
            # Keep the existing parent lock through upload and commit. Event snapshots use it too.
            self._attachOfficialPensum(lockedParameter, document, uploadAttempt)
            if lockedParameter.isActive:
                lockedParameter.validateReady()
            self.repository.appendVersion(lockedParameter, userLogin)

        try:
            return self.repository.update(IdTrainingParameter, replace)
        except Exception:
            # A failed commit/refresh can still mean the new reference was persisted.
            # Never delete either object, even when the upload outcome is unknown.
            logger.warning(
                "Actualización de PÉNSUM sin confirmación; conservar objetos para revisión | "
                "IdTrainingParameter=%s previousReference=%s newReference=%s generation=%s",
                IdTrainingParameter, previousReference,
                uploadAttempt.get("reference"), uploadAttempt.get("generation"),
                exc_info=True,
            )
            raise

    def getVersions(self, IdTrainingParameter):
        parameter = self.getById(IdTrainingParameter)
        return [TrainingParameterVersionResponseDto.model_validate(version).model_copy(update={
            "isCurrent": version.pensumPathTrainingParameterVersion == parameter.pensumPathTrainingParameter,
            "parameterName": parameter.nameTrainingParameter,
        }) for version in self.repository.getVersions(IdTrainingParameter)]

    def getVersionReadUrl(self, IdTrainingParameter, versionId, download=False):
        version = self.repository.getVersion(IdTrainingParameter, versionId)
        if not version:
            raise LookupError("La versión no pertenece al parámetro o no existe.")
        with GcsStorage() as storage:
            path = self._documentPath(SimpleNamespace(
                IdTrainingParameter=IdTrainingParameter,
                pensumPathTrainingParameter=version.pensumPathTrainingParameterVersion,
            ), storage)
            if not storage.exists(path):
                raise LookupError("No se encontró el documento de esta versión.")
            return storage.generateReadUrl(path, fileName=version.pensumOriginalNameTrainingParameterVersion, download=download)

    def getPensumReadUrl(self, IdTrainingParameter, download=False):
        parameter = self.getById(IdTrainingParameter)
        with GcsStorage() as storage:
            path = self._documentPath(parameter, storage)
            if not storage.exists(path):
                raise LookupError("No se encontró el PÉNSUM oficial.")
            return storage.generateReadUrl(
                path, fileName=parameter.pensumOriginalNameTrainingParameter, download=download,
            )
