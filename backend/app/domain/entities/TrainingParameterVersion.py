from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.infrastructure.db.connection import Base


class TrainingParameterVersion(Base):
    __tablename__ = "trainingparameterversion"
    __table_args__ = (UniqueConstraint("IdTrainingParameter", "versionNumber"),)

    IdTrainingParameterVersion = Column(Integer, primary_key=True, autoincrement=True)
    IdTrainingParameter = Column(Integer, ForeignKey("trainingparameter.IdTrainingParameter", ondelete="RESTRICT"), nullable=False)
    versionNumber = Column(Integer, nullable=False)
    pensumPathTrainingParameterVersion = Column(String(500), nullable=False)
    pensumOriginalNameTrainingParameterVersion = Column(String(255), nullable=False)
    pensumMimeTypeTrainingParameterVersion = Column(String(150), nullable=False)
    pensumSizeTrainingParameterVersion = Column(Integer, nullable=False)
    createdAt = Column(DateTime, nullable=False)
    createdByUserLogin = Column(String(100), nullable=True)
    isBaseline = Column(Boolean, nullable=False, default=False)
