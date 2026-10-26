from app.domain.interfaces.IEventRepository import IEventRepository
from app.domain.entities.EventCompetency import EventCompetency
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.domain.entities.EventStatus import EventStatus
from app.domain.entities.Attendance import Attendance
from app.domain.entities.EventTopic import EventTopic
from sqlalchemy.orm import Session, joinedload
from app.domain.entities.Event import Event
from app.domain.dtos.TrainingParameterDto import normalizeTopics
from app.infrastructure.repositories.TrainingParameterRepository import TrainingParameterRepository
from typing import List, Optional
from datetime import date, datetime
from typing import Callable
from sqlalchemy import func, or_
import math

class EventRepository(IEventRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[Event]:
        return (self.db.query(Event)
                    .options(joinedload(Event.topics),
                             joinedload(Event.competencies),
                             joinedload(Event.eventStatus),
                             joinedload(Event.solutionCenter)
                            ).order_by(Event.IdEvent.desc()).all())

    def getByCreatedBy(self, createdByUserLogin: str) -> List[Event]:
        return (self.db.query(Event)
                    .options(joinedload(Event.topics),
                             joinedload(Event.competencies),
                             joinedload(Event.eventStatus),
                             joinedload(Event.solutionCenter)
                            ).filter(Event.createdByUserLogin == createdByUserLogin).order_by(Event.IdEvent.desc()).all())

    def getById(self, IdEvent: int) -> Optional[Event]:
        return (self.db.query(Event)
                    .options(joinedload(Event.topics),
                             joinedload(Event.competencies),
                             joinedload(Event.eventStatus),
                             joinedload(Event.solutionCenter)
                            ).filter(Event.IdEvent == IdEvent).first())

    def getByToken(self, tokenEvent: str) -> Optional[Event]:
        return (self.db.query(Event)
                    .options(joinedload(Event.topics),
                             joinedload(Event.competencies),
                             joinedload(Event.eventStatus),
                             joinedload(Event.solutionCenter)
                            ).filter(Event.tokenEvent == tokenEvent).first())
    
    def getAttendancesByEvent(self, IdEvent: int) -> List[Attendance]:
        return (self.db.query(Attendance).options(joinedload(Attendance.attendancePerson)).filter(Attendance.IdEvent == IdEvent).order_by(Attendance.createdAt.desc()).all())

    def getAttendanceByEvent(self, IdEvent: int, IdAttendance: int) -> Optional[Attendance]:
        return (
            self.db.query(Attendance).options(joinedload(Attendance.attendancePerson))
            .filter(Attendance.IdEvent == IdEvent, Attendance.IdAttendance == IdAttendance)
            .populate_existing().first()
        )
    
    def getPaginated(self, page: int, pageSize: int, status: Optional[str], createdByUserLogin: Optional[str],):
        page = max(page, 1)
        pageSize = max(min(pageSize, 100), 1)
        query = (
            self.db.query(Event)
            .outerjoin(EventStatus, Event.IdEventStatus == EventStatus.IdEventStatus).options(
                joinedload(Event.topics),
                joinedload(Event.competencies),
                joinedload(Event.eventStatus),
                joinedload(Event.solutionCenter),
            )
        )

        if createdByUserLogin:
            query = query.filter(Event.createdByUserLogin == createdByUserLogin)

        if status and status.strip():
            query = query.filter(func.lower(EventStatus.nameEventStatus) == status.strip().lower())

        total = query.count()

        items = (
            query
            .order_by(Event.IdEvent.desc())
            .offset((page - 1) * pageSize)
            .limit(pageSize)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": math.ceil(total / pageSize) if total > 0 else 0,
        }

    def create(self, eventData: Event, topics: Optional[List[str]], competencies: List[int]) -> Event:
        try:
            if eventData.IdTrainingParameter is not None:
                parameter = TrainingParameterRepository(self.db).getById(
                    eventData.IdTrainingParameter, forUpdate=True,
                )
                if not parameter:
                    raise ValueError("El parámetro de capacitación no existe.")
                if not parameter.isActive:
                    raise ValueError("El parámetro de capacitación no está activo.")
                parameter.validateReady()
                topics = normalizeTopics(
                    [topic.nameParameterTopic for topic in parameter.topics]
                    if topics is None else topics
                )
                if not topics:
                    raise ValueError("El evento parametrizado debe tener al menos un tema.")
                for field in ("Path", "OriginalName", "MimeType", "Size"):
                    setattr(
                        eventData, f"pensum{field}Event",
                        getattr(parameter, f"pensum{field}TrainingParameter"),
                    )
            self.db.add(eventData)
            self.db.flush()
            self._replaceTopics(eventData.IdEvent, topics)
            self._replaceCompetencies(eventData.IdEvent, competencies)
            self.db.commit()
            self.db.refresh(eventData)
            return self.getById(eventData.IdEvent)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("No se pudo crear el evento por una restricción de datos.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear el evento: {str(e)}")

        except Exception:
            self.db.rollback()
            raise

    def update(self, IdEvent: int, updateData: dict, topics, competencies) -> Optional[Event]:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return None

            if "IdTrainingParameter" in updateData:
                raise ValueError("IdTrainingParameter no se puede cambiar ni retirar.")
            if eventFound.IdTrainingParameter is not None and any(
                key.startswith("pensum") for key in updateData
            ):
                raise ValueError("No se permite reemplazar el PÉNSUM de un evento parametrizado.")

            for key, value in updateData.items():
                setattr(eventFound, key, value)

            if topics is not None:
                self._replaceTopics(IdEvent, topics)

            if competencies is not None:
                self._replaceCompetencies(IdEvent, competencies)

            self.db.commit()
            self.db.refresh(eventFound)

            return self.getById(IdEvent)

        except IntegrityError:
            self.db.rollback()
            raise ValueError("No se pudo actualizar el evento por una restricción de datos.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el evento: {str(e)}")

        except Exception:
            self.db.rollback()
            raise
        
    def updatePensum(self, IdEvent: int, pensumOriginalNameEvent: str, pensumPathEvent: str, pensumMimeTypeEvent: str, pensumSizeEvent: int, updatedByUserLogin: str) -> Optional[Event]:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return None

            if eventFound.IdTrainingParameter is not None:
                raise ValueError("No se permite reemplazar el PÉNSUM de un evento parametrizado.")

            eventFound.pensumOriginalNameEvent = pensumOriginalNameEvent
            eventFound.pensumPathEvent = pensumPathEvent
            eventFound.pensumMimeTypeEvent = pensumMimeTypeEvent
            eventFound.pensumSizeEvent = pensumSizeEvent
            eventFound.updatedByUserLogin = updatedByUserLogin
            eventFound.updatedAt = datetime.now()

            self.db.commit()
            self.db.refresh(eventFound)

            return self.getById(IdEvent)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el pensum del evento: {str(e)}")

        except Exception:
            self.db.rollback()
            raise

    def cancel(self, IdEvent: int, observationsEvent: str) -> Optional[Event]:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return None

            eventFound.IdEventStatus = 3
            eventFound.observationsEvent = observationsEvent

            self.db.commit()
            self.db.refresh(eventFound)

            return self.getById(IdEvent)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al cancelar el evento: {str(e)}")

    def getQrCleanupCandidates(self, throughDate: date, afterId: int, limit: int = 100) -> list[int]:
        # Coarse date filter only: the application rechecks the exact attendance
        # deadline under the row lock, including the existing grace period.
        return [row.IdEvent for row in (
            self.db.query(Event.IdEvent)
            .filter(Event.IdEvent > afterId, Event.qrPathEvent.isnot(None), Event.qrPathEvent != "")
            .filter(or_(Event.IdEventStatus == 3, Event.dateEvent <= throughDate))
            .order_by(Event.IdEvent).limit(limit).all()
        )]

    def cleanupQr(self, IdEvent: int, removeIfExpired: Callable[[Event], bool]) -> None:
        try:
            event = (
                self.db.query(Event).filter(Event.IdEvent == IdEvent)
                .populate_existing().with_for_update().first()
            )
            if event and event.qrPathEvent and removeIfExpired(event):
                event.qrPathEvent = None
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def delete(self, IdEvent: int) -> bool:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return False

            self.db.delete(eventFound)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar el evento: {str(e)}")

    def setStatus(self, IdEvent: int, IdEventStatus: int) -> Optional[Event]:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return None

            eventFound.IdEventStatus = IdEventStatus

            self.db.commit()
            self.db.refresh(eventFound)

            return self.getById(IdEvent)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el estado del evento: {str(e)}")

    def countAttendances(self, IdEvent: int) -> int:
        return (self.db.query(Attendance).filter(Attendance.IdEvent == IdEvent).count())

    def setAttendedPeopleNumber(self, IdEvent: int, attendedPeopleNumber: int) -> Optional[Event]:
        try:
            eventFound = self.getById(IdEvent)

            if not eventFound:
                return None

            eventFound.attendedPeopleNumber = attendedPeopleNumber

            self.db.commit()
            self.db.refresh(eventFound)

            return self.getById(IdEvent)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el número de asistentes: {str(e)}")

    def _replaceTopics(self, IdEvent: int, topics: List[str]) -> None:
        self.db.query(EventTopic).filter(EventTopic.IdEvent == IdEvent).delete()

        for topicName in topics:
            cleanTopic = topicName.strip()

            if cleanTopic:
                self.db.add(
                    EventTopic(
                        IdEvent=IdEvent,
                        nameEventTopic=cleanTopic
                    )
                )

    def _replaceCompetencies(self, IdEvent: int, competencies: List[int]) -> None:
        competencies = list(dict.fromkeys(competencies))

        self.db.query(EventCompetency).filter(EventCompetency.IdEvent == IdEvent).delete()

        for IdCompetency in competencies:
            self.db.add(
                EventCompetency(
                    IdEvent=IdEvent,
                    IdCompetency=IdCompetency
                )
            )
