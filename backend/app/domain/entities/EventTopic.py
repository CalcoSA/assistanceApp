from sqlalchemy import Column, ForeignKey, Integer, String
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class EventTopic(Base):
    __tablename__ = "EventTopic"

    IdEventTopic = Column(Integer, primary_key=True, autoincrement=True)
    IdEvent = Column(Integer, ForeignKey("Event.IdEvent"), nullable=False)
    nameEventTopic = Column(String(300), nullable=False)

    event = relationship("Event", back_populates="topics")