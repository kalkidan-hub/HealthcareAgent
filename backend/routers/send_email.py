from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/send_email")
async def send_email(email_data: dict):
    try:
        # Logic to send email goes here
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))