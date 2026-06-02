from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class AttendancePerson(Base):
    __tablename__ = "AttendancePerson"

    IdAttendancePerson = Column(Integer, primary_key=True, autoincrement=True)
    fullNameAttendancePerson = Column(String(200), nullable=False)
    documentNumberAttendancePerson = Column(String(50), nullable=False, unique=True)
    positionAttendancePerson = Column(String(150), nullable=True)
    IdSolutionCenter = Column(Integer, ForeignKey("SolutionCenter.IdSolutionCenter"), nullable=True)
    phoneAttendancePerson = Column(String(50), nullable=True)
    signaturePathAttendancePerson = Column(String(500), nullable=True)
    createdAt = Column(DateTime, nullable=True)
    updatedAt = Column(DateTime, nullable=True)

    solutionCenter = relationship("SolutionCenter")
    attendances = relationship("Attendance", back_populates="attendancePerson")