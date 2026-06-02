from app.domain.dtos.SolutionCenterDto import SolutionCenterCreateDto, SolutionCenterUpdateDto
from app.domain.interfaces.ISolutionCenterRepository import ISolutionCenterRepository
from app.domain.entities.SolutionCenter import SolutionCenter
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

class SolutionCenterRepository(ISolutionCenterRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[SolutionCenter]:
        return (self.db.query(SolutionCenter).order_by(SolutionCenter.IdSolutionCenter.asc()).all())

    def getById(self, IdSolutionCenter: int) -> Optional[SolutionCenter]:
        return (self.db.query(SolutionCenter).filter(SolutionCenter.IdSolutionCenter == IdSolutionCenter).first())
    
    def getByCodeInsensitive(self, codeSolutionCenter: str) -> Optional[SolutionCenter]:
        return (self.db.query(SolutionCenter).filter(func.lower(SolutionCenter.codeSolutionCenter) == codeSolutionCenter.strip().lower()).first())

    def create(self, solutionCenterData: SolutionCenterCreateDto) -> SolutionCenter:
        try:
            newSolutionCenter = SolutionCenter(
                codeSolutionCenter=solutionCenterData.codeSolutionCenter.strip(),
                nameSolutionCenter=solutionCenterData.nameSolutionCenter.strip(),
                statusSolutionCenter=1 if solutionCenterData.statusSolutionCenter else 0
            )

            self.db.add(newSolutionCenter)
            self.db.commit()
            self.db.refresh(newSolutionCenter)

            return newSolutionCenter

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un centro de soluciones con ese código.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear el centro de soluciones: {str(e)}")

    def update(self, IdSolutionCenter: int, solutionCenterData: SolutionCenterUpdateDto) -> Optional[SolutionCenter]:
        try:
            solutionCenterFound = self.getById(IdSolutionCenter)

            if not solutionCenterFound:
                return None

            if solutionCenterData.codeSolutionCenter is not None:
                solutionCenterFound.codeSolutionCenter = solutionCenterData.codeSolutionCenter.strip()

            if solutionCenterData.nameSolutionCenter is not None:
                solutionCenterFound.nameSolutionCenter = solutionCenterData.nameSolutionCenter.strip()

            if solutionCenterData.statusSolutionCenter is not None:
                solutionCenterFound.statusSolutionCenter = 1 if solutionCenterData.statusSolutionCenter else 0

            self.db.commit()
            self.db.refresh(solutionCenterFound)

            return solutionCenterFound

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un centro de soluciones con ese código.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el centro de soluciones: {str(e)}")

    def delete(self, IdSolutionCenter: int) -> bool:
        try:
            solutionCenterFound = self.getById(IdSolutionCenter)

            if not solutionCenterFound:
                return False

            self.db.delete(solutionCenterFound)
            self.db.commit()

            return True

        except IntegrityError:
            self.db.rollback()
            raise ValueError("No se puede eliminar el centro de soluciones porque está relacionado con otros registros.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar el centro de soluciones: {str(e)}")