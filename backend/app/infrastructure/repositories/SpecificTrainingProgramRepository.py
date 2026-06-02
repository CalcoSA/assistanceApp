from app.domain.interfaces.ISpecificTrainingProgramRepository import ISpecificTrainingProgramRepository
from app.domain.entities.SpecificTrainingProgram import SpecificTrainingProgram
from sqlalchemy.orm import Session
from typing import List

class SpecificTrainingProgramRepository(ISpecificTrainingProgramRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[SpecificTrainingProgram]:
        return (self.db.query(SpecificTrainingProgram).order_by(SpecificTrainingProgram.IdSpecificTrainingProgram.asc()).all())