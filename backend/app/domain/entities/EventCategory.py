from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class EventCategory(Base):
    __tablename__ = "EventCategory"

    IdEventCategory = Column(Integer, primary_key=True, autoincrement=True)
    nameEventCategory = Column(String(150), nullable=False)