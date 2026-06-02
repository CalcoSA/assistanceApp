from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class SolutionCenter(Base):
    __tablename__ = "SolutionCenter"

    IdSolutionCenter = Column(Integer, primary_key=True, autoincrement=True)
    codeSolutionCenter = Column(String(50), nullable=False, unique=True)
    nameSolutionCenter = Column(String(200), nullable=False)
    statusSolutionCenter = Column(Integer, nullable=False, default=1)