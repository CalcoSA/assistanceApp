from sqlalchemy import Column, Integer, String, Boolean, BigInteger, UniqueConstraint
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class ApplicationUser(Base):
    __tablename__ = "ApplicationUser"

    IdApplicationUser = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wordpressUserId = Column(BigInteger, nullable=False)
    wordpressUserLogin = Column(String(60), nullable=False)
    statusApplicationUser = Column(Boolean, nullable=False, default=True)

    roles = relationship("ApplicationUserRole", back_populates="applicationUser", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("wordpressUserId", name="uq_application_user_wordpress_id"),
        UniqueConstraint("wordpressUserLogin", name="uq_application_user_wordpress_login"),
    )