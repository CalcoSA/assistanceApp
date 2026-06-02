from app.application.interfaces.IAssistanceReasonApplication import IAssistanceReasonApplication
from app.domain.interfaces.IAssistanceReasonRepository import IAssistanceReasonRepository
from app.domain.dtos.AssistanceReasonDto import AssistanceReasonDto
from typing import List

class AssistanceReasonApplication(IAssistanceReasonApplication):

    def __init__(self, assistanceReasonRepository: IAssistanceReasonRepository):
        self.assistanceReasonRepository = assistanceReasonRepository

    def getAll(self) -> List[AssistanceReasonDto]:
        return self.assistanceReasonRepository.getAll()