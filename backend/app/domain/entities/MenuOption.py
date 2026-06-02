from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class MenuOption(Base):
    __tablename__ = "MenuOption"

    IdMenuOption = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nameMenuOption = Column(String(100), nullable=False)
    pathMenuOption = Column(String(200), nullable=True)
    iconMenuOption = Column(String(100), nullable=True)
    parentMenuOption = Column(Integer, ForeignKey("MenuOption.IdMenuOption"), nullable=True)
    orderMenuOption = Column(Integer, nullable=False, default=0)
    statusMenuOption = Column(Boolean, nullable=False, default=True)

    parent = relationship("MenuOption", remote_side=[IdMenuOption])
    roles = relationship("RoleMenuOption", back_populates="menuOption", cascade="all, delete-orphan")