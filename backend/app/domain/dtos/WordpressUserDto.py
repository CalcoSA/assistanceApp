from pydantic import BaseModel

class WordpressUserResponseDto(BaseModel):
    wordpressUserId: int
    wordpressUserLogin: str
    wordpressUserEmail: str
    wordpressDisplayName: str