from app.domain.dtos.CompetencyDto import CompetencyCreateDto, CompetencyUpdateDto
from app.domain.interfaces.ICompetencyRepository import ICompetencyRepository
from app.domain.entities.EventCompetency import EventCompetency
from app.domain.entities.Competency import Competency
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

class CompetencyRepository(ICompetencyRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[Competency]:
        return (
            self.db.query(Competency)
            .order_by(Competency.IdCompetency.asc())
            .all()
        )

    def getById(self, IdCompetency: int) -> Optional[Competency]:
        return (
            self.db.query(Competency)
            .filter(Competency.IdCompetency == IdCompetency)
            .first()
        )

    def getByNameInsensitive(self, nameCompetency: str) -> Optional[Competency]:
        return (
            self.db.query(Competency)
            .filter(
                func.lower(Competency.nameCompetency)
                == nameCompetency.strip().lower()
            )
            .first()
        )

    def isInUse(self, IdCompetency: int) -> bool:
        return (
            self.db.query(EventCompetency.IdEventCompetency)
            .filter(EventCompetency.IdCompetency == IdCompetency)
            .first()
            is not None
        )

    def create(self, competencyData: CompetencyCreateDto) -> Competency:
        try:
            newCompetency = Competency(
                nameCompetency=competencyData.nameCompetency.strip().upper()
            )

            self.db.add(newCompetency)
            self.db.commit()
            self.db.refresh(newCompetency)

            return newCompetency

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe una competencia con ese nombre.")

        except SQLAlchemyError as error:
            self.db.rollback()
            raise Exception(f"Error al crear la competencia: {str(error)}")

    def update(
        self,
        IdCompetency: int,
        competencyData: CompetencyUpdateDto,
    ) -> Optional[Competency]:
        try:
            competencyFound = self.getById(IdCompetency)

            if not competencyFound:
                return None

            competencyFound.nameCompetency = (
                competencyData.nameCompetency.strip().upper()
            )

            self.db.commit()
            self.db.refresh(competencyFound)

            return competencyFound

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe una competencia con ese nombre.")

        except SQLAlchemyError as error:
            self.db.rollback()
            raise Exception(f"Error al actualizar la competencia: {str(error)}")

    def delete(self, IdCompetency: int) -> bool:
        try:
            competencyFound = self.getById(IdCompetency)

            if not competencyFound:
                return False

            self.db.delete(competencyFound)
            self.db.commit()

            return True

        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "No se puede eliminar la competencia porque está relacionada "
                "con uno o más eventos."
            )

        except SQLAlchemyError as error:
            self.db.rollback()
            raise Exception(f"Error al eliminar la competencia: {str(error)}")
