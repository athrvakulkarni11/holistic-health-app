"""
Configuration settings for the Healthcare Analytics Platform.

Includes security-relevant settings: CORS origins, rate limits,
file upload constraints, and environment-aware toggles.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── AI / LLM ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# SerpAPI (Google Search)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# ─── Knowledge Base ────────────────────────────────────────
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")

# ─── File Uploads (Security) ───────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "csv", "txt", "docx"}

# ─── Server ────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8050"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# ─── CORS (Security) ───────────────────────────────────────
# In production, restrict to your actual domains
# In development, allow localhost variants
_cors_env = os.getenv("CORS_ORIGINS", "")
if _cors_env:
    CORS_ORIGINS = [origin.strip() for origin in _cors_env.split(",")]
elif ENVIRONMENT.lower() == "development":
    CORS_ORIGINS = [
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:3000",
    ]
else:
    # Production: only allow same-origin (requests from the served frontend)
    CORS_ORIGINS = ["*"]  # FastAPI serves the frontend, so same-origin is fine

# ─── Rate Limiting ─────────────────────────────────────────
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# ─── Content Limits ────────────────────────────────────────
MAX_CHAT_MESSAGE_LENGTH = 5000
MAX_FILE_TEXT_FOR_CONTEXT = 50000
