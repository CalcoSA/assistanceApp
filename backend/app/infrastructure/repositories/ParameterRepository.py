from app.domain.dtos.ParameterDto import ParameterCreateDto, ParameterUpdateDto
from app.domain.interfaces.IParameterRepository import IParameterRepository
from app.domain.entities.Parameter import Parameter
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional


class ParameterRepository(IParameterRepository):

    def __init__(self, db: Session):
        self.db = db

    def getAll(self) -> List[Parameter]:
        return self.db.query(Parameter).order_by(Parameter.IdParameter.asc()).all()

    def getById(self, IdParameter: int) -> Optional[Parameter]:
        return (
            self.db.query(Parameter)
            .filter(Parameter.IdParameter == IdParameter)
            .first()
        )

    def getByNameInsensitive(self, nameParameter: str) -> Optional[Parameter]:
        return (
            self.db.query(Parameter)
            .filter(func.lower(Parameter.nameParameter) == nameParameter.strip().lower())
            .first()
        )

    def create(self, parameterData: ParameterCreateDto) -> Parameter:
        try:
            newParameter = Parameter(
                nameParameter=parameterData.nameParameter.strip().upper(),
                valueParameter=parameterData.valueParameter.strip()
            )

            self.db.add(newParameter)
            self.db.commit()
            self.db.refresh(newParameter)

            return newParameter

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un parámetro con ese nombre.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al crear el parámetro: {str(e)}")

    def update(self, IdParameter: int, parameterData: ParameterUpdateDto) -> Optional[Parameter]:
        try:
            parameterFound = self.getById(IdParameter)

            if not parameterFound:
                return None

            if parameterData.valueParameter is not None:
                parameterFound.valueParameter = parameterData.valueParameter.strip()

            self.db.commit()
            self.db.refresh(parameterFound)

            return parameterFound

        except IntegrityError:
            self.db.rollback()
            raise ValueError("Ya existe un parámetro con ese nombre.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al actualizar el parámetro: {str(e)}")

    def delete(self, IdParameter: int) -> bool:
        try:
            parameterFound = self.getById(IdParameter)

            if not parameterFound:
                return False

            self.db.delete(parameterFound)
            self.db.commit()

            return True

        except IntegrityError:
            self.db.rollback()
            raise ValueError("No se puede eliminar el parámetro porque está relacionado con otros registros.")

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error al eliminar el parámetro: {str(e)}")
