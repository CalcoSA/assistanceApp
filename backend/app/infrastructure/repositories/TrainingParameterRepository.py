import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.domain.entities.ParameterTopic import ParameterTopic
from app.domain.entities.TrainingParameter import TrainingParameter
from app.domain.entities.TrainingParameterVersion import TrainingParameterVersion
from app.domain.interfaces.ITrainingParameterRepository import ITrainingParameterRepository

logger = logging.getLogger(__name__)


class TrainingParameterRepository(ITrainingParameterRepository):
    def __init__(self, db: Session):
        self.db = db

    def appendVersion(self, parameter, userLogin):
        # Current locking read, not MAX under a potentially stale REPEATABLE READ snapshot.
        last = self.db.query(TrainingParameterVersion).filter(
            TrainingParameterVersion.IdTrainingParameter == parameter.IdTrainingParameter,
        ).order_by(TrainingParameterVersion.versionNumber.desc()).with_for_update().first()
        version = TrainingParameterVersion(
            IdTrainingParameter=parameter.IdTrainingParameter,
            versionNumber=last.versionNumber + 1 if last else 1,
            pensumPathTrainingParameterVersion=parameter.pensumPathTrainingParameter,
            pensumOriginalNameTrainingParameterVersion=parameter.pensumOriginalNameTrainingParameter,
            pensumMimeTypeTrainingParameterVersion=parameter.pensumMimeTypeTrainingParameter,
            pensumSizeTrainingParameterVersion=parameter.pensumSizeTrainingParameter,
            createdAt=parameter.updatedAt, createdByUserLogin=userLogin, isBaseline=False,
        )
        self.db.add(version)
        try:
            self.db.flush()
        except IntegrityError as error:
            raise FileExistsError("Conflicto al publicar la versión. Consulte el documento vigente antes de reintentar.") from error
        return version

    def getVersions(self, IdTrainingParameter):
        return self.db.query(TrainingParameterVersion).filter(
            TrainingParameterVersion.IdTrainingParameter == IdTrainingParameter,
        ).order_by(TrainingParameterVersion.versionNumber.desc()).all()

    def getVersion(self, IdTrainingParameter, versionId):
        return self.db.query(TrainingParameterVersion).filter(
            TrainingParameterVersion.IdTrainingParameter == IdTrainingParameter,
            TrainingParameterVersion.IdTrainingParameterVersion == versionId,
        ).first()

    def getAll(self, isActive=None):
        query = self.db.query(TrainingParameter).options(selectinload(TrainingParameter.topics))
        if isActive is not None:
            query = query.filter(TrainingParameter.isActive == isActive)
        return query.order_by(TrainingParameter.nameTrainingParameter).all()

    def getById(self, IdTrainingParameter, *, forUpdate=False):
        query = self.db.query(TrainingParameter).filter(
            TrainingParameter.IdTrainingParameter == IdTrainingParameter,
        )
        if not forUpdate:
            return query.options(selectinload(TrainingParameter.topics)).first()
        parameter = query.populate_existing().with_for_update().first()
        if parameter:
            # Locking reads see current committed data even with MySQL REPEATABLE READ.
            # All catalog mutations and event snapshots first lock the parent.
            topics = (
                self.db.query(ParameterTopic)
                .filter(ParameterTopic.IdTrainingParameter == IdTrainingParameter)
                .order_by(ParameterTopic.sortOrder, ParameterTopic.IdParameterTopic)
                .populate_existing().with_for_update().all()
            )
            set_committed_value(parameter, "topics", topics)
        return parameter

    def getByName(self, name):
        return self.db.query(TrainingParameter).filter(
            func.lower(TrainingParameter.nameTrainingParameter) == name.lower(),
        ).first()

    def create(self, parameter):
        try:
            self.db.add(parameter)
            self.db.commit()
            self.db.refresh(parameter)
            return self.getById(parameter.IdTrainingParameter)
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un parámetro o tema con ese nombre.") from None
        except Exception:
            self.db.rollback()
            raise

    def createComplete(self, parameter, prepare):
        try:
            self.db.add(parameter)
            # Obtain the ID and enforce unique constraints before uploading, without committing.
            self.db.flush()
            prepare(parameter)
            self.db.flush()
            self.db.commit()
            self.db.refresh(parameter)
            return self.getById(parameter.IdTrainingParameter)
        except Exception as error:
            try:
                self.db.rollback()
            except Exception:
                logger.exception("No fue posible revertir la creación completa del parámetro")
            if isinstance(error, IntegrityError):
                raise ValueError("Ya existe un parámetro o tema con ese nombre.") from error
            raise

    def update(self, IdTrainingParameter, applyChanges, topics=None):
        try:
            parameter = self.getById(IdTrainingParameter, forUpdate=True)
            if not parameter:
                raise LookupError("El parámetro de capacitación no existe.")
            applyChanges(parameter)
            if topics is not None:
                # These are catalog rows only. EventTopic snapshots are never touched.
                # Flush removals before inserts to allow reordering identical names.
                parameter.topics.clear()
                self.db.flush()
                parameter.topics = [
                    ParameterTopic(nameParameterTopic=name, sortOrder=order)
                    for order, name in enumerate(topics)
                ]
            self.db.commit()
            self.db.refresh(parameter)
            return self.getById(IdTrainingParameter)
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un parámetro o tema con ese nombre.") from None
        except Exception:
            self.db.rollback()
            raise
