from urllib.parse import urlsplit

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.db.connection import Base


class TrainingParameter(Base):
    __tablename__ = "trainingparameter"

    IdTrainingParameter = Column(Integer, primary_key=True, autoincrement=True)
    nameTrainingParameter = Column(String(200), nullable=False, unique=True)
    pensumPathTrainingParameter = Column(String(500), nullable=True)
    pensumOriginalNameTrainingParameter = Column(String(255), nullable=True)
    pensumMimeTypeTrainingParameter = Column(String(150), nullable=True)
    pensumSizeTrainingParameter = Column(Integer, nullable=True)
    isActive = Column(Boolean, nullable=False, default=False)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=True)

    topics = relationship(
        "ParameterTopic", back_populates="trainingParameter",
        cascade="all, delete-orphan", order_by="ParameterTopic.sortOrder",
    )

    def validateReady(self, topicNames: list[str] | None = None) -> None:
        names = topicNames if topicNames is not None else [
            topic.nameParameterTopic for topic in self.topics
        ]
        if not names:
            raise ValueError("El parámetro debe tener al menos un tema.")
        reference = self.pensumPathTrainingParameter or ""
        parsed = urlsplit(reference)
        expectedPath = f"/pensum/parameters/{self.IdTrainingParameter}/"
        if (
            len(reference) > 500 or parsed.scheme != "gs" or not parsed.netloc
            or parsed.query or parsed.fragment or expectedPath not in parsed.path
            or not self.pensumOriginalNameTrainingParameter
            or len(self.pensumOriginalNameTrainingParameter) > 255
            or not self.pensumMimeTypeTrainingParameter
            or len(self.pensumMimeTypeTrainingParameter) > 150
            or not self.pensumSizeTrainingParameter
            or not 0 < self.pensumSizeTrainingParameter <= 2147483647
        ):
            raise ValueError("El parámetro requiere un PÉNSUM oficial válido.")
