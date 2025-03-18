from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.talk import TalkRequest, TalkResponse

router = APIRouter()

@router.post("/talk", response_model=TalkResponse)
async def talk(request: TalkRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Implement your logic here
    response_message = f"Echo: {request.message}"
    
    return TalkResponse(response=response_message)