from pydantic import BaseModel
from typing import Any, Dict


class OnlyOfficePreviewResponseDto(BaseModel):
    documentServerUrl: str
    config: Dict[str, Any]

