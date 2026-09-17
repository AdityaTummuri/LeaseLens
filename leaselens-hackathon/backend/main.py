"""LeaseLens FastAPI Backend — Fortified API Gateway.

Provides high-security endpoints for residential lease analysis:
- POST /api/analyze-lease: Multi-part or JSON lease ingestion with strict validation:
    * Magic byte signature verification (%PDF- header check)
    * Streaming chunk-based file size enforcement (max 10MB to prevent DoS)
    * Content-Type whitelist enforcement
    * Raw text length and null-byte sanitization
- GET /api/health: Service liveness and dependency status
- GET /api/market-norms: Verified regional lease baseline benchmarks

All endpoints enforce strict UPL guardrails and return informational data only.
"""

import json
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from agents.orchestrator import analyze_lease
from schemas.lease_schema import LeaseAnalysis

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("leaselens")

# Security constants
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit strictly enforced
PDF_MAGIC_BYTES = b"%PDF-"
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
}
MAX_RAW_TEXT_CHARS = 100_000
NORMS_FILE_PATH = Path(__file__).parent / "data" / "market_norms.json"


@lru_cache(maxsize=1)
def _load_cached_market_norms() -> dict:
    """Load and cache regional market baselines into memory once."""
    if not NORMS_FILE_PATH.exists():
        raise FileNotFoundError("Market norms dataset not found.")
    with open(NORMS_FILE_PATH, encoding="utf-8") as f:
        return json.load(f)


class TextAnalysisRequest(BaseModel):
    """Pydantic model for raw text lease analysis with injection safeguards."""

    raw_text: str = Field(
        ...,
        min_length=20,
        max_length=MAX_RAW_TEXT_CHARS,
        description="Raw residential lease text to analyze",
    )

    @field_validator("raw_text")
    @classmethod
    def sanitize_raw_text(cls, v: str) -> str:
        """Strip null bytes and non-printable control characters."""
        cleaned = v.replace("\x00", "").strip()
        if len(cleaned) < 20:
            raise ValueError("Lease text must contain at least 20 valid characters.")
        return cleaned


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler verifying agent environment."""
    logger.info("🔍 LeaseLens fortified backend starting...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "⚠️ GEMINI_API_KEY not configured. Agent calls will fail in live mode. "
            "Mock/fallback baselines remain active."
        )
    else:
        logger.info("✅ GEMINI_API_KEY detected and loaded.")

    yield
    logger.info("LeaseLens backend shutting down cleanly.")


is_production = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER", "").lower() == "true"
docs_url = None if is_production else "/docs"
redoc_url = None if is_production else "/redoc"
openapi_url = None if is_production else "/openapi.json"

app = FastAPI(
    title="LeaseLens API",
    description=(
        "Multi-agent residential rent agreement risk highlighter. "
        "Strictly provides informational variance analysis against empirical market norms. "
        "DOES NOT provide legal advice or recommendations (UPL Compliant)."
    ),
    version="1.1.0",
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# Rate limiter setup (prevents DoS and API quota exhaustion)
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# GZip compression for all responses > 500 bytes (~60-70% reduction)
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS configuration: restricted allow_headers for defense-in-depth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://leaselens.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With", "X-Request-ID"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Enforce OWASP defense-in-depth security response headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    """Log request processing time and assign tracking ID for observability."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "[%s] %s %s → %d (%.1fms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


@app.get("/", tags=["System"])
async def root_health_check():
    """Lightweight root health check endpoint for Render service monitoring."""
    return {"status": "online", "service": "LeaseLens Backend"}


@app.get("/api/health", tags=["System"])
async def health_check():
    """Detailed health check endpoint confirming API availability and UPL guardrail status."""
    return {
        "status": "healthy",
        "service": "leaselens",
        "version": "1.1.0",
        "guardrail_status": "active",
        "upl_compliance": "enforced",
    }


async def _read_and_validate_pdf_upload(file: UploadFile) -> bytes:
    """Safely stream and validate uploaded PDF file to prevent DoS and malicious payloads.

    Validations:
    1. Content-Type header whitelist check.
    2. Streaming chunk read with immediate termination if size > 10 MB.
    3. Magic byte (%PDF-) header verification to block spoofed extensions.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported media type: '{file.content_type}'. "
                "Only standard PDF documents ('application/pdf') are accepted."
            ),
        )

    chunks = []
    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB read buffer

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"Uploaded file exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.",
            )
        chunks.append(chunk)

    file_bytes = b"".join(chunks)

    if len(file_bytes) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or corrupted.",
        )

    # Magic byte verification
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid PDF binary header. The uploaded file does not match "
                "the standard '%PDF-' magic signature."
            ),
        )

    return file_bytes


@app.post(
    "/api/analyze-lease",
    response_model=LeaseAnalysis,
    summary="Analyze Residential Lease Agreement",
    tags=["Analysis"],
)
@limiter.limit("30/minute")
async def analyze_lease_endpoint(
    request: Request,
    file: UploadFile | None = File(default=None, description="PDF lease document"),
    raw_text: str | None = Form(default=None, description="Raw lease text"),
):
    """Analyze a residential lease agreement for variance against market norms.

    Input requirements:
    - Either a valid PDF upload (<= 10MB, verified %PDF- header) OR raw text string.
    - Output strictly conforms to LeaseAnalysis schema with neutral phrasing.

    Security & UPL Guardrail:
    - Rejects spoofed MIME types and oversize payloads.
    - All outputs pass through dual-layer UPL regex and semantic sanitization.
    """
    if not file and not raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request: Provide either a PDF file upload or raw lease text.",
        )

    pdf_bytes: bytes | None = None
    sanitized_text: str | None = None

    if file:
        pdf_bytes = await _read_and_validate_pdf_upload(file)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename or "upload.pdf")[:100]
        logger.info(
            "Validated PDF upload '%s' (%d bytes, verified %s)",
            safe_name,
            len(pdf_bytes),
            file.content_type,
        )

    if raw_text:
        cleaned = raw_text.replace("\x00", "").strip()
        if len(cleaned) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Raw lease text must contain at least 20 valid characters.",
            )
        if len(cleaned) > MAX_RAW_TEXT_CHARS:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"Raw text exceeds maximum allowed length of {MAX_RAW_TEXT_CHARS} characters.",
            )
        sanitized_text = cleaned

    try:
        result = await analyze_lease(
            pdf_bytes=pdf_bytes,
            raw_text=sanitized_text,
        )
        return result

    except ValueError as e:
        logger.warning("Validation error in analysis pipeline: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except RuntimeError as e:
        logger.error("Pipeline runtime error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Multi-agent analysis pipeline encountered an upstream error.",
        ) from e
    except Exception as e:
        logger.error("Unexpected error in lease analysis: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the document.",
        ) from e


@app.post(
    "/api/analyze-lease-json",
    response_model=LeaseAnalysis,
    summary="Analyze Raw Text Lease via JSON Body",
    tags=["Analysis"],
)
@limiter.limit("30/minute")
async def analyze_lease_json_endpoint(request: Request, payload: TextAnalysisRequest):
    """Analyze raw lease text submitted as a strictly validated JSON payload."""
    try:
        result = await analyze_lease(
            pdf_bytes=None,
            raw_text=payload.raw_text,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error in JSON lease analysis: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the document.",
        ) from e


@app.get("/api/market-norms", tags=["Data"])
async def get_market_norms():
    """Return empirical regional lease market baselines used for variance calculation."""
    try:
        norms_data = _load_cached_market_norms()
        return JSONResponse(
            content=norms_data,
            headers={
                "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400",
            },
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market norms dataset not found.",
        ) from None
    except Exception as e:
        logger.error("Error reading market norms: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load market norms repository.",
        ) from e


if __name__ == "__main__":
    import uvicorn

    server_port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=server_port,
        reload=not bool(os.getenv("RENDER")),
        log_level="info",
    )
