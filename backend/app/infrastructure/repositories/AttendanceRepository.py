from app.domain.interfaces.IAttendanceRepository import IAttendanceRepository, AttendancePersistenceError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.domain.entities.Attendance import Attendance
from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto
from app.domain.entities.Event import Event
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from typing import Callable

class AttendanceRepository(IAttendanceRepository):

    def __init__(self, db: Session):
        self.db = db

    def registerWithSignature(
        self, IdEvent: int, data: AttendanceRegisterDto,
        ipAddress: str | None, userAgent: str | None,
        saveSignature: Callable[[int], str],
    ) -> tuple[int, int, int, str | None]:
        for attempt in range(3):
            commitStarted = False
            signatureStarted = False
            try:
                event = (
                    self.db.query(Event).filter(Event.IdEvent == IdEvent)
                    .populate_existing().with_for_update().first()
                )
                if event is None:
                    raise ValueError("El evento no existe.")
                person = (
                    self.db.query(AttendancePerson)
                    .filter(AttendancePerson.documentNumberAttendancePerson == data.documentNumberAttendancePerson.strip())
                    .populate_existing().with_for_update().first()
                )
                if person is None:
                    person = AttendancePerson(
                        documentNumberAttendancePerson=data.documentNumberAttendancePerson.strip(),
                        fullNameAttendancePerson=data.fullNameAttendancePerson.strip(),
                        createdAt=datetime.now(),
                    )
                    self.db.add(person)
                    # Obtain the internal ID without committing a partial person.
                    self.db.flush()

                # Locking reads see committed changes even when the initial public
                # lookup started a REPEATABLE READ snapshot before another request.
                attendees = (
                    self.db.query(Attendance.IdAttendancePerson)
                    .filter(Attendance.IdEvent == IdEvent).with_for_update().all()
                )
                if any(row.IdAttendancePerson == person.IdAttendancePerson for row in attendees):
                    raise ValueError("Esta persona ya registró asistencia para este evento.")

                previousSignature = person.signaturePathAttendancePerson
                signatureStarted = True
                signature = saveSignature(person.IdAttendancePerson)
                person.fullNameAttendancePerson = data.fullNameAttendancePerson.strip()
                person.positionAttendancePerson = data.positionAttendancePerson.strip() if data.positionAttendancePerson else None
                person.IdSolutionCenter = data.IdSolutionCenter
                person.phoneAttendancePerson = data.phoneAttendancePerson.strip() if data.phoneAttendancePerson else None
                person.signaturePathAttendancePerson = signature
                person.updatedAt = datetime.now()
                attendance = Attendance(
                    IdEvent=IdEvent, IdAttendancePerson=person.IdAttendancePerson,
                    IdPersonnelType=data.IdPersonnelType, ipAddressAttendance=ipAddress,
                    createdAt=datetime.now(),
                )
                self.db.add(attendance)
                count = len(attendees) + 1
                event.attendedPeopleNumber = count
                self.db.flush()
                # Capture scalar results before commit expires ORM objects. Do not
                # turn a post-commit refresh failure into a failed registration.
                result = (attendance.IdAttendance, person.IdAttendancePerson, count, previousSignature)
                commitStarted = True
                self.db.commit()
                return result
            except Exception as error:
                try:
                    self.db.rollback()
                except Exception:
                    raise AttendancePersistenceError(commitUncertain=True) from None
                if commitStarted:
                    raise AttendancePersistenceError(commitUncertain=True) from None
                if isinstance(error, SQLAlchemyError):
                    code = (getattr(getattr(error, "orig", None), "args", ()) or (None,))[0]
                    # Another request can insert a previously unknown person or
                    # win an InnoDB gap-lock race. Retry only BEFORE uploading.
                    if not signatureStarted and not commitStarted and code in (1062, 1205, 1213) and attempt < 2:
                        continue
                    raise AttendancePersistenceError(commitUncertain=commitStarted) from None
                raise

    def getLatestByPerson(self, IdAttendancePerson: int) -> Optional[Attendance]:
        return (
            self.db.query(Attendance)
            .filter(Attendance.IdAttendancePerson == IdAttendancePerson)
            .order_by(Attendance.createdAt.desc(), Attendance.IdAttendance.desc())
            .first()
        )

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

    def createAndCount(self, IdEvent: int, IdAttendancePerson: int, IdPersonnelType: int, ipAddress: str | None, userAgent: str | None) -> tuple[Attendance, int]:
        try:
            eventFound = (
                self.db.query(Event)
                .filter(Event.IdEvent == IdEvent)
                .with_for_update()
                .first()
            )

            if not eventFound:
                raise ValueError("El evento no existe.")

            attendanceCount = self.countByEvent(IdEvent)

            existingAttendance = self.getByEventAndPerson(
                IdEvent,
                IdAttendancePerson,
            )

            if existingAttendance:
                raise ValueError(
                    "Esta persona ya registró asistencia para este evento."
                )

            newAttendance = Attendance(
                IdEvent=IdEvent,
                IdAttendancePerson=IdAttendancePerson,
                IdPersonnelType=IdPersonnelType,
                ipAddressAttendance=ipAddress,
                createdAt=datetime.now(),
            )
            newAttendanceCount = attendanceCount + 1
            eventFound.attendedPeopleNumber = newAttendanceCount

            self.db.add(newAttendance)
            self.db.commit()
            self.db.refresh(newAttendance)

            return newAttendance, newAttendanceCount

        except ValueError:
            self.db.rollback()
            raise

        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "Esta persona ya registró asistencia para este evento."
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al registrar asistencia: {str(e)}")
