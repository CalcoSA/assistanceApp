from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class EventCompetency(Base):
    __tablename__ = "EventCompetency"

    IdEventCompetency = Column(Integer, primary_key=True, autoincrement=True)
    IdEvent = Column(Integer, ForeignKey("Event.IdEvent"), nullable=False)
    IdCompetency = Column(Integer, ForeignKey("Competency.IdCompetency"), nullable=False)

    event = relationship("Event", back_populates="competencies")
    competency = relationship("Competency")

    __table_args__ = (
        UniqueConstraint("IdEvent", "IdCompetency", name="uq_event_competency"),
    )