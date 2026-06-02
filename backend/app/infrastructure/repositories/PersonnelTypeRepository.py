from app.domain.interfaces.IPersonnelTypeRepository import IPersonnelTypeRepository
from app.domain.entities.PersonnelType import PersonnelType
from sqlalchemy.orm import Session
from typing import Optional

class PersonnelTypeRepository(IPersonnelTypeRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> list[PersonnelType]:
        return (
            self.db.query(PersonnelType)
            .order_by(PersonnelType.namePersonnelType.asc())
            .all()
        )

    def getById(self, IdPersonnelType: int) -> Optional[PersonnelType]:
        return (
            self.db.query(PersonnelType)
            .filter(PersonnelType.IdPersonnelType == IdPersonnelType)
            .first()
        )