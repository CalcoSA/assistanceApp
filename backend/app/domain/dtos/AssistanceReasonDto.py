from pydantic import BaseModel

class AssistanceReasonDto(BaseModel):
    IdAssistanceReason: int
    nameAssistanceReason: str