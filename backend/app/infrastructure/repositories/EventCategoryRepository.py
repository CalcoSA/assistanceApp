from app.domain.interfaces.IEventCategoryRepository import IEventCategoryRepository
from app.domain.entities.EventCategory import EventCategory
from sqlalchemy.orm import Session
from typing import List

class EventCategoryRepository(IEventCategoryRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[EventCategory]:
        return (self.db.query(EventCategory).order_by(EventCategory.IdEventCategory.asc()).all())