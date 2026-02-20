"""
Main FastAPI application entry point.
Serves the API endpoints and the static frontend.

v2: Added security hardening — restrictive CORS, security headers middleware,
    request size limits, and error sanitization.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api import router as api_router
from app.config import HOST, PORT, CORS_ORIGINS
import uvicorn
import os
import time


app = FastAPI(
    title="Holistic Health AI Platform",
    description="AI-powered biomarker analytics and health suggestions.",
    version="1.0.0",
    docs_url=None if os.getenv("ENVIRONMENT", "production") == "production" else "/docs",
    redoc_url=None if os.getenv("ENVIRONMENT", "production") == "production" else "/redoc",
)


# ─── SECURITY HEADERS MIDDLEWARE ─────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy — restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        )
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' https://ui-avatars.com data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


app.add_middleware(SecurityHeadersMiddleware)


# ─── REQUEST SIZE LIMIT MIDDLEWARE ───────────────────────────

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent abuse."""

    MAX_BODY_SIZE = 15 * 1024 * 1024  # 15 MB (slightly above file upload limit)

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Maximum allowed size is 15 MB."},
            )
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)


# ─── CORS CONFIGURATION ─────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ─── GLOBAL EXCEPTION HANDLER ───────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent leaking internal error details.
    In production, only return a generic message.
    """
    is_production = os.getenv("ENVIRONMENT", "production") == "production"

    if is_production:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred. Please try again later.",
                "error": True,
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "error": True,
            },
        )


# Include API router (must be BEFORE static mount)
app.include_router(api_router, prefix="/api")

# Serve static files (Frontend) — mounted last so /api routes take priority
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    # Only use reload in local development, never in production
    is_dev = os.getenv("ENVIRONMENT", "production").lower() == "development"
    uvicorn.run("main:app", host=HOST, port=PORT, reload=is_dev)
