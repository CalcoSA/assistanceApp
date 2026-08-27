from app.infrastructure.db.connection import Base
from sqlalchemy import Column, Integer, String, Text


class Parameter(Base):
    __tablename__ = "Parameter"

    IdParameter = Column(Integer, primary_key=True, autoincrement=True)
    nameParameter = Column(String(150), nullable=False, unique=True)
    valueParameter = Column(Text, nullable=False)
