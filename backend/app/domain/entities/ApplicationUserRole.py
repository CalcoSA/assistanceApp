from sqlalchemy import Column, Integer, ForeignKey, Boolean, UniqueConstraint
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class ApplicationUserRole(Base):
    __tablename__ = "ApplicationUserRole"

    IdApplicationUserRole = Column(Integer, primary_key=True, index=True, autoincrement=True)
    IdApplicationUser = Column(Integer, ForeignKey("ApplicationUser.IdApplicationUser"), nullable=False)
    IdRole = Column(Integer, ForeignKey("Role.IdRole"), nullable=False)
    statusApplicationUserRole = Column(Boolean, nullable=False, default=True)

    applicationUser = relationship("ApplicationUser", back_populates="roles")
    role = relationship("Role", back_populates="applicationUsers")

    __table_args__ = (UniqueConstraint("IdApplicationUser", "IdRole", name="uq_application_user_role"),)