from pydantic import BaseModel, ConfigDict


class CompetencyCreateDto(BaseModel):
    nameCompetency: str


class CompetencyUpdateDto(BaseModel):
    nameCompetency: str


class CompetencyResponseDto(BaseModel):
    IdCompetency: int
    nameCompetency: str

    model_config = ConfigDict(from_attributes=True)


# Se conserva el nombre anterior para no romper los consumidores existentes.
CompetencyDto = CompetencyResponseDto
