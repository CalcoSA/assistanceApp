from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class RoleMenuOption(Base):
    __tablename__ = "RoleMenuOption"

    IdRoleMenuOption = Column(Integer, primary_key=True, index=True, autoincrement=True)
    IdRole = Column(Integer, ForeignKey("Role.IdRole"), nullable=False)
    IdMenuOption = Column(Integer, ForeignKey("MenuOption.IdMenuOption"), nullable=False)

    role = relationship("Role", back_populates="menuOptions")
    menuOption = relationship("MenuOption", back_populates="roles")

    __table_args__ = (UniqueConstraint("IdRole", "IdMenuOption", name="uq_role_menu_option"),)