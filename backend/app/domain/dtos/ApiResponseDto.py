from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class apiResponseDto(BaseModel, Generic[T]):
    isSuccess: bool
    Message: str
    result: Optional[T] = None