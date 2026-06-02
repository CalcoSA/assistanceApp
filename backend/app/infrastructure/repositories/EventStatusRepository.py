from app.domain.interfaces.IEventStatusRepository import IEventStatusRepository
from app.domain.entities.EventStatus import EventStatus
from sqlalchemy.orm import Session
from typing import List

class EventStatusRepository(IEventStatusRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[EventStatus]:
        return (self.db.query(EventStatus).order_by(EventStatus.IdEventStatus.asc()).all())