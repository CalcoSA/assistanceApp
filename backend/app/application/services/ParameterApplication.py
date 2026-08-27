from app.application.interfaces.IParameterApplication import IParameterApplication
from app.domain.interfaces.IParameterRepository import IParameterRepository
from app.domain.dtos.ParameterDto import ParameterCreateDto, ParameterUpdateDto, ParameterResponseDto
from app.domain.constants.ParameterNames import (
    EVENT_NOTIFICATION_RECIPIENTS_PARAMETER,
    SYSTEM_PARAMETER_NAMES,
)
from typing import List
import re


PARAMETER_NAME_PATTERN = re.compile(r"^[A-Z0-9_]+$")
EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
RECIPIENT_SEPARATOR = re.compile(r"[,;\r\n]+")


class ParameterApplication(IParameterApplication):

    def __init__(self, parameterRepository: IParameterRepository):
        self.parameterRepository = parameterRepository

    def getAll(self) -> List[ParameterResponseDto]:
        return self.parameterRepository.getAll()

    def getById(self, IdParameter: int) -> ParameterResponseDto:
        parameterFound = self.parameterRepository.getById(IdParameter)

        if not parameterFound:
            raise ValueError("El parámetro no existe.")

        return parameterFound

    def create(self, parameterData: ParameterCreateDto) -> ParameterResponseDto:
        nameParameter = parameterData.nameParameter.strip().upper()
        valueParameter = parameterData.valueParameter.strip()

        if not nameParameter:
            raise ValueError("El nombre del parámetro es obligatorio.")

        if len(nameParameter) > 150:
            raise ValueError("El nombre del parámetro no puede superar 150 caracteres.")

        if not PARAMETER_NAME_PATTERN.fullmatch(nameParameter):
            raise ValueError(
                "El nombre del parámetro solo puede contener letras, números y guion bajo."
            )

        valueParameter = self._normalizeValue(nameParameter, valueParameter)

        existingParameter = self.parameterRepository.getByNameInsensitive(nameParameter)

        if existingParameter:
            raise ValueError("Ya existe un parámetro con ese nombre.")

        parameterData.nameParameter = nameParameter
        parameterData.valueParameter = valueParameter

        return self.parameterRepository.create(parameterData)

    def update(self, IdParameter: int, parameterData: ParameterUpdateDto) -> ParameterResponseDto:
        parameterFound = self.parameterRepository.getById(IdParameter)

        if not parameterFound:
            raise ValueError("El parámetro no existe.")

        if parameterData.valueParameter is not None:
            valueParameter = parameterData.valueParameter.strip()
            parameterData.valueParameter = self._normalizeValue(
                parameterFound.nameParameter, valueParameter
            )

        parameterUpdated = self.parameterRepository.update(IdParameter, parameterData)

        if not parameterUpdated:
            raise ValueError("El parámetro no existe.")

        return parameterUpdated

    def delete(self, IdParameter: int) -> bool:
        parameterFound = self.parameterRepository.getById(IdParameter)

        if not parameterFound:
            raise ValueError("El parámetro no existe.")

        if parameterFound.nameParameter.strip().upper() in SYSTEM_PARAMETER_NAMES:
            raise ValueError(
                "No se puede eliminar este parámetro porque es requerido por el sistema."
            )

        deleted = self.parameterRepository.delete(IdParameter)

        if not deleted:
            raise ValueError("El parámetro no existe.")

        return deleted

    def _normalizeValue(self, nameParameter: str, valueParameter: str) -> str:
        if not valueParameter:
            raise ValueError("El valor del parámetro es obligatorio.")

        if (
            nameParameter.strip().upper()
            != EVENT_NOTIFICATION_RECIPIENTS_PARAMETER
        ):
            return valueParameter

        recipients = list(
            dict.fromkeys(
                recipient.strip().lower()
                for recipient in RECIPIENT_SEPARATOR.split(valueParameter)
                if recipient.strip()
            )
        )

        if not recipients:
            raise ValueError("Debe configurar al menos un correo destinatario.")

        invalidRecipient = next(
            (
                recipient
                for recipient in recipients
                if not EMAIL_PATTERN.fullmatch(recipient)
            ),
            None,
        )

        if invalidRecipient:
            raise ValueError(
                f'El correo "{invalidRecipient}" no tiene un formato válido.'
            )

        return ", ".join(recipients)
