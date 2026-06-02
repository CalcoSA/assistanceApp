from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class AssistanceReason(Base):
    __tablename__ = "AssistanceReason"

    IdAssistanceReason = Column(Integer, primary_key=True, autoincrement=True)
    nameAssistanceReason = Column(String(150), nullable=False)