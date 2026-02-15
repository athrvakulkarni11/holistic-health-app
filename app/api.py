"""
API Router configuration — All endpoints for the Healthcare AI Platform.
Supports:
  1. Biomarker form analysis (/api/analyze)
  2. Direct chat interface (/api/chat)
  3. File upload & processing (/api/upload)
  4. Chat with file attachment (/api/chat/upload)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.models import (
    AnalysisRequest, AnalysisResponse,
    ChatRequest, ChatResponse,
    FileUploadResponse,
)
from app.analytics_engine import BiomarkerAnalyticsEngine
from app.chat_engine import ChatEngine
from app.file_processor import FileProcessorService
from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from typing import Optional
import os

router = APIRouter()
engine = BiomarkerAnalyticsEngine()
chat_engine = ChatEngine()
file_processor = FileProcessorService()


# ─── 1. BIOMARKER FORM ANALYSIS ─────────────────────────────
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_biomarkers(request: AnalysisRequest):
    """
    Analyze user biomarkers and profile to provide health suggestions.
    Used by the form-based input mechanism.
    """
    try:
        profile_dict = request.profile.model_dump()
        biomarkers_dict = request.biomarkers.model_dump()
        result = engine.analyze(profile_dict, biomarkers_dict)
        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── 2. DIRECT CHAT INTERFACE ───────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Direct chat endpoint — user sends a message, AI responds with
    health advice using knowledge base and web search.
    """
    try:
        result = chat_engine.chat(
            session_id=request.session_id,
            user_message=request.message,
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a specific session."""
    return chat_engine.get_session_history(session_id)


@router.delete("/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session."""
    return chat_engine.clear_session(session_id)


# ─── 3. FILE UPLOAD & PROCESSING ────────────────────────────
def _validate_file(file: UploadFile):
    """Validate file extension and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a lab report file (PDF, CSV, TXT, DOCX, image).
    Extracts text and identifies biomarker values using AI.
    """
    _validate_file(file)

    try:
        content = await file.read()

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_UPLOAD_SIZE_MB} MB."
            )

        result = file_processor.process_uploaded_file(file.filename, content)
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Upload a file, extract biomarkers, and run full analysis automatically.
    Returns both extracted data and complete health analysis.
    """
    _validate_file(file)

    try:
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_UPLOAD_SIZE_MB} MB."
            )

        # Step 1: Extract data
        upload_result = file_processor.process_uploaded_file(file.filename, content)
        if not upload_result.get("success"):
            return upload_result

        extracted = upload_result.get("extracted_data", {})
        profile = extracted.get("profile", {})
        biomarkers = extracted.get("biomarkers", {})

        # Step 2: Run analysis if we have enough data
        # Clean nulls from biomarkers
        clean_biomarkers = {k: v for k, v in biomarkers.items() if v is not None}

        if not clean_biomarkers:
            return {
                "success": True,
                "upload_result": upload_result,
                "analysis": None,
                "message": "Biomarkers were extracted but no numerical values were found. Please verify the file content.",
            }

        # Ensure profile has required fields
        if not profile.get("age") or not profile.get("gender"):
            return {
                "success": True,
                "upload_result": upload_result,
                "analysis": None,
                "message": "Biomarkers extracted successfully, but age and gender are required for full analysis. Please provide them manually.",
                "needs_profile": True,
            }

        analysis = engine.analyze(profile, clean_biomarkers)

        return {
            "success": True,
            "upload_result": upload_result,
            "analysis": analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload+Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── 4. CHAT WITH FILE ATTACHMENT ───────────────────────────
@router.post("/chat/upload", response_model=ChatResponse)
async def chat_with_file(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    file: UploadFile = File(None),
):
    """
    Chat endpoint with optional file attachment.
    The file is processed and its content is injected into the conversation context.
    """
    file_text = None

    if file and file.filename:
        _validate_file(file)
        try:
            content = await file.read()
            size_mb = len(content) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_UPLOAD_SIZE_MB} MB."
                )

            # Extract text from file
            filepath = file_processor.save_file(file.filename, content)
            file_text = file_processor.extract_text(filepath)
        except HTTPException:
            raise
        except Exception as e:
            file_text = f"Error processing attached file: {str(e)}"

    try:
        result = chat_engine.chat(
            session_id=session_id,
            user_message=message,
            file_text=file_text,
        )
        return result
    except Exception as e:
        print(f"Chat+File error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── UTILITY ENDPOINTS ──────────────────────────────────────
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Holistic Health AI Platform"}


@router.get("/biomarkers")
async def list_supported_biomarkers():
    """List all supported biomarkers with their reference ranges."""
    from app.analytics_engine import BIOMARKER_RANGES, BIOMARKER_DISPLAY_NAMES
    result = []
    for key, ranges in BIOMARKER_RANGES.items():
        result.append({
            "key": key,
            "name": BIOMARKER_DISPLAY_NAMES.get(key, key),
            "unit": ranges["unit"],
            "male_range": f"{ranges['male'][0]} - {ranges['male'][1]}",
            "female_range": f"{ranges['female'][0]} - {ranges['female'][1]}",
        })
    return result
