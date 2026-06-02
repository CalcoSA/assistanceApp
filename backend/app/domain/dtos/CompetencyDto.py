from pydantic import BaseModel

class CompetencyDto(BaseModel):
    IdCompetency: int
    nameCompetency: str