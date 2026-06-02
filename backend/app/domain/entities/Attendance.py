from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.infrastructure.db.connection import Base
from sqlalchemy.orm import relationship

class Attendance(Base):
    __tablename__ = "Attendance"

    IdAttendance = Column(Integer, primary_key=True, autoincrement=True)
    IdEvent = Column(Integer, ForeignKey("Event.IdEvent"), nullable=False)
    IdAttendancePerson = Column(Integer, ForeignKey("AttendancePerson.IdAttendancePerson"), nullable=False)
    IdPersonnelType = Column(Integer, ForeignKey("PersonnelType.IdPersonnelType"), nullable=False)
    ipAddressAttendance = Column(String(100), nullable=True)
    createdAt = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="attendances")
    attendancePerson = relationship("AttendancePerson", back_populates="attendances")
    personnelType = relationship("PersonnelType")

    __table_args__ = (
        UniqueConstraint("IdEvent", "IdAttendancePerson", name="uq_attendance_event_person"),
    )