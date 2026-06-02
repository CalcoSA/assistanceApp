from pydantic import BaseModel

class SpecificTrainingProgramDto(BaseModel):
    IdSpecificTrainingProgram: int
    nameSpecificTrainingProgram: str