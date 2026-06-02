from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class SpecificTrainingProgram(Base):
    __tablename__ = "SpecificTrainingProgram"

    IdSpecificTrainingProgram = Column(Integer, primary_key=True, autoincrement=True)
    nameSpecificTrainingProgram = Column(String(250), nullable=False)