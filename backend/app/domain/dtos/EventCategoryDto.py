from pydantic import BaseModel

class EventCategoryDto(BaseModel):
    IdEventCategory: int
    nameEventCategory: str