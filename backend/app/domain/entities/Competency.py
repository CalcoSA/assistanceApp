from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class Competency(Base):
    __tablename__ = "Competency"

    IdCompetency = Column(Integer, primary_key=True, autoincrement=True)
    nameCompetency = Column(String(200), nullable=False)