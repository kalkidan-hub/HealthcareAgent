from fastapi import FastAPI
from backend.routers.clinical_notes import router as clinical_notes
from backend.routers.lab_report import router as lab_report
from backend.routers.prescription import router as prescription_router
from backend.routers.talk import router as talk_router

app = FastAPI()

# Include the prescription router
app.include_router(prescription_router, prefix="/api")
app.include_router(lab_report, prefix="/api")
app.include_router(talk_router, prefix="/api")
app.include_router(clinical_notes, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)