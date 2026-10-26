from app.domain.interfaces.IPersonnelTypeRepository import IPersonnelTypeRepository
from app.domain.entities.PersonnelType import PersonnelType
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

class PersonnelTypeRepository(IPersonnelTypeRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> list[PersonnelType]:
        return (
            self.db.query(PersonnelType)
            .filter(func.lower(func.trim(PersonnelType.namePersonnelType)) != "no aplica")
            .order_by(PersonnelType.namePersonnelType.asc())
            .all()
        )

    def getById(self, IdPersonnelType: int) -> Optional[PersonnelType]:
        return (
            self.db.query(PersonnelType)
            .filter(PersonnelType.IdPersonnelType == IdPersonnelType)
            .first()
        )
