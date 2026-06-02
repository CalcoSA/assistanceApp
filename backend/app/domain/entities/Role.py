from sqlalchemy import Column, Integer, String, Boolean
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class Role(Base):
    __tablename__ = "Role"

    IdRole = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nameRole = Column(String(100), nullable=False, unique=True)
    statusRole = Column(Boolean, nullable=False, default=True)

    menuOptions = relationship("RoleMenuOption", back_populates="role", cascade="all, delete-orphan")
    applicationUsers = relationship("ApplicationUserRole", back_populates="role", cascade="all, delete-orphan")