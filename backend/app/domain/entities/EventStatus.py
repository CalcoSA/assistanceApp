from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class EventStatus(Base):
    __tablename__ = "EventStatus"

    IdEventStatus = Column(Integer, primary_key=True, autoincrement=True)
    nameEventStatus = Column(String(100), nullable=False)