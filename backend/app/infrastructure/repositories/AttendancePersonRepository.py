from app.domain.interfaces.IAttendancePersonRepository import IAttendancePersonRepository
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

class AttendancePersonRepository(IAttendancePersonRepository):

    def __init__(self, db: Session):
        self.db = db

    def getByDocument(self, documentNumber: str) -> Optional[AttendancePerson]:
        return (self.db.query(AttendancePerson).filter(AttendancePerson.documentNumberAttendancePerson == documentNumber.strip()).first())

    def create(self, data: AttendanceRegisterDto, signaturePath: str | None) -> AttendancePerson:
        try:
            newPerson = AttendancePerson(
                fullNameAttendancePerson=data.fullNameAttendancePerson.strip(),
                documentNumberAttendancePerson=data.documentNumberAttendancePerson.strip(),
                positionAttendancePerson=data.positionAttendancePerson.strip() if data.positionAttendancePerson else None,
                IdSolutionCenter=data.IdSolutionCenter,
                phoneAttendancePerson=data.phoneAttendancePerson.strip() if data.phoneAttendancePerson else None,
                signaturePathAttendancePerson=signaturePath,
                createdAt=datetime.now()
            )

            self.db.add(newPerson)
            self.db.commit()
            self.db.refresh(newPerson)

            return newPerson

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe una persona registrada con esa cédula.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear la persona de asistencia: {str(e)}")

    def update(self, attendancePerson: AttendancePerson, data: AttendanceRegisterDto, signaturePath: str | None) -> AttendancePerson:
        try:
            attendancePerson.fullNameAttendancePerson = data.fullNameAttendancePerson.strip()
            attendancePerson.positionAttendancePerson = data.positionAttendancePerson.strip() if data.positionAttendancePerson else None
            attendancePerson.IdSolutionCenter = data.IdSolutionCenter
            attendancePerson.phoneAttendancePerson = data.phoneAttendancePerson.strip() if data.phoneAttendancePerson else None

            if signaturePath:
                attendancePerson.signaturePathAttendancePerson = signaturePath

            attendancePerson.updatedAt = datetime.now()

            self.db.commit()
            self.db.refresh(attendancePerson)

            return attendancePerson

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar la persona de asistencia: {str(e)}")