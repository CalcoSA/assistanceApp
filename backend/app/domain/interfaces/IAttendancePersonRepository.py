from app.domain.entities.AttendancePerson import AttendancePerson
from app.domain.dtos.AttendanceDto import AttendanceRegisterDto
from abc import ABC, abstractmethod
from typing import Optional

class IAttendancePersonRepository(ABC):

    @abstractmethod
    def getByDocument(self, documentNumber: str) -> Optional[AttendancePerson]:
        pass

    @abstractmethod
    def create(self, data: AttendanceRegisterDto, signaturePath: str | None) -> AttendancePerson:
        pass

    @abstractmethod
    def update(self, attendancePerson: AttendancePerson, data: AttendanceRegisterDto, signaturePath: str | None) -> AttendancePerson:
        pass