from app.domain.interfaces.IAttendanceRepository import IAttendanceRepository
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.Attendance import Attendance
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

class AttendanceRepository(IAttendanceRepository):

    def __init__(self, db: Session):
        self.db = db

    def getByEventAndPerson(self, IdEvent: int, IdAttendancePerson: int) -> Optional[Attendance]:
        return (self.db.query(Attendance).filter(Attendance.IdEvent == IdEvent).filter(Attendance.IdAttendancePerson == IdAttendancePerson).first())

    def create(self, IdEvent: int, IdAttendancePerson: int, IdPersonnelType: int, ipAddress: str | None, userAgent: str | None) -> Attendance:
        try:
            newAttendance = Attendance(
                IdEvent=IdEvent,
                IdAttendancePerson=IdAttendancePerson,
                IdPersonnelType=IdPersonnelType,
                ipAddressAttendance=ipAddress,
                createdAt=datetime.now()
            )

            self.db.add(newAttendance)
            self.db.commit()
            self.db.refresh(newAttendance)

            return newAttendance

        except IntegrityError:
            self.db.rollback()
            raise ValueError("La persona ya registró asistencia para este evento.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al registrar asistencia: {str(e)}")

    def countByEvent(self, IdEvent: int) -> int:
        return (self.db.query(Attendance).filter(Attendance.IdEvent == IdEvent).count())