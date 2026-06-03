from pydantic import BaseModel


class TalkRequest(BaseModel):
    message: str

class TalkResponse(BaseModel):
    response: str