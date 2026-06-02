from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String

class PersonnelType(Base):
    __tablename__ = "PersonnelType"

    IdPersonnelType = Column(Integer, primary_key=True, autoincrement=True)
    namePersonnelType = Column(String(100), nullable=False, unique=True)