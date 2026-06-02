from app.domain.interfaces.ICompetencyRepository import ICompetencyRepository
from app.domain.entities.Competency import Competency
from sqlalchemy.orm import Session
from typing import List

class CompetencyRepository(ICompetencyRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[Competency]:
        return (self.db.query(Competency).order_by(Competency.IdCompetency.asc()).all())