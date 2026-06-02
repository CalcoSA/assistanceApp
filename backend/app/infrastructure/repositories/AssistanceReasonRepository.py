from app.domain.interfaces.IAssistanceReasonRepository import IAssistanceReasonRepository
from app.domain.entities.AssistanceReason import AssistanceReason
from sqlalchemy.orm import Session
from typing import List

class AssistanceReasonRepository(IAssistanceReasonRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[AssistanceReason]:
        return (self.db.query(AssistanceReason).order_by(AssistanceReason.IdAssistanceReason.asc()).all())