from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.brain_tumor.model import BrainTumorModel
from models.diabetic_retinopathy.model import DiabeticRetinopathyModel
from models.skin_disease.model import SkinDiseaseModel
from models.xray_samples.model import XRaySamplesModel
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
brain_tumor_model = BrainTumorModel()
diabetic_retinopathy_model = DiabeticRetinopathyModel()
skin_disease_model = SkinDiseaseModel()
xray_samples_model = XRaySamplesModel()

# Print all routes for debugging
@app.on_event("startup")
async def startup_event():
    logger.info("Available routes:")
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}")

# Register routes
app.include_router(
    brain_tumor_model.router,
    prefix="/api/brain_tumor",
    tags=["brain_tumor"]
)

app.include_router(
    diabetic_retinopathy_model.router,
    prefix="/api/diabetic_retinopathy",
    tags=["diabetic_retinopathy"]
)

app.include_router(
    skin_disease_model.router,
    prefix="/api/skin_disease",
    tags=["skin_disease"]
)

app.include_router(
    xray_samples_model.router,
    prefix="/api/xray_samples",
    tags=["xray_samples"]
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": ["brain_tumor", "diabetic_retinopathy", "skin_disease", "xray_samples"]}

@app.get("/")
async def root():
    return {"message": "Brain Tumor Detection API"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")