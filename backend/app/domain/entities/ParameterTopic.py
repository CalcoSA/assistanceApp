from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.infrastructure.db.connection import Base


class ParameterTopic(Base):
    __tablename__ = "parametertopic"
    __table_args__ = (UniqueConstraint("IdTrainingParameter", "nameParameterTopic"),)

    IdParameterTopic = Column(Integer, primary_key=True, autoincrement=True)
    IdTrainingParameter = Column(
        Integer, ForeignKey("trainingparameter.IdTrainingParameter", ondelete="RESTRICT"),
        nullable=False,
    )
    nameParameterTopic = Column(String(300), nullable=False)
    sortOrder = Column(Integer, nullable=False, default=0)

    trainingParameter = relationship("TrainingParameter", back_populates="topics")
