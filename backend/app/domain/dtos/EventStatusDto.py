from pydantic import BaseModel, ConfigDict

class EventStatusDto(BaseModel):
    IdEventStatus: int
    nameEventStatus: str

    model_config = ConfigDict(from_attributes=True)