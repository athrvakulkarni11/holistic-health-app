"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    age: int = Field(..., ge=1, le=120, description="Patient age in years")
    gender: str = Field(..., pattern="^(male|female|Male|Female|M|F|m|f)$", description="Patient gender")
    height: Optional[float] = Field(None, ge=50, le=300, description="Height in cm")
    weight: Optional[float] = Field(None, ge=20, le=500, description="Weight in kg")


class BiomarkerData(BaseModel):
    hemoglobin: Optional[float] = Field(None, ge=0, le=25, description="Hemoglobin in g/dL")
    rbc_count: Optional[float] = Field(None, ge=0, le=10, description="RBC count in million cells/mcL")
    ferritin: Optional[float] = Field(None, ge=0, le=5000, description="Ferritin in ng/mL")
    vitamin_b12: Optional[float] = Field(None, ge=0, le=5000, description="Vitamin B12 in pg/mL")
    vitamin_d: Optional[float] = Field(None, ge=0, le=200, description="Vitamin D (25-OH) in ng/mL")
    fasting_glucose: Optional[float] = Field(None, ge=0, le=600, description="Fasting Glucose in mg/dL")
    hba1c: Optional[float] = Field(None, ge=0, le=20, description="HbA1c in %")
    total_cholesterol: Optional[float] = Field(None, ge=0, le=600, description="Total Cholesterol in mg/dL")
    ldl: Optional[float] = Field(None, ge=0, le=500, description="LDL in mg/dL")
    hdl: Optional[float] = Field(None, ge=0, le=200, description="HDL in mg/dL")
    triglycerides: Optional[float] = Field(None, ge=0, le=1000, description="Triglycerides in mg/dL")
    hs_crp: Optional[float] = Field(None, ge=0, le=50, description="hs-CRP in mg/L")
    tsh: Optional[float] = Field(None, ge=0, le=100, description="TSH in mIU/L")
    sgpt_alt: Optional[float] = Field(None, ge=0, le=2000, description="SGPT / ALT in U/L")


class AnalysisRequest(BaseModel):
    profile: UserProfile
    biomarkers: BiomarkerData


class AnalysisResponse(BaseModel):
    user_profile: dict
    classifications: list[dict]
    risk_score: dict
    analysis: dict


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000, description="User's chat message")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    error: bool = False
    sources_used: bool = False


class FileUploadResponse(BaseModel):
    success: bool
    filename: str = ""
    raw_text: str = ""
    extracted_data: dict = {}
    error: str = ""
