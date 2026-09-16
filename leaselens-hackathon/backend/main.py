"""LeaseLens FastAPI Backend — API Gateway.

Provides the /api/analyze-lease endpoint that accepts PDF uploads
or raw text and returns a UPL-compliant LeaseAnalysis JSON response.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🔍 LeaseLens backend starting...")
    
    # Verify API key is configured
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "⚠️  GEMINI_API_KEY not set. Agent calls will fail. "
            "Set it in .env or as an environment variable."
        )
    else:
        logger.info("✅ GEMINI_API_KEY configured.")

    yield
    logger.info("LeaseLens backend shutting down.")


app = FastAPI(
    title="LeaseLens API",
    description=(
        "Multi-agent residential rent agreement risk highlighter. "
        "Analyzes lease agreements and highlights clauses that deviate "
        "from regional market standards. For informational purposes only."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "leaselens"}


@app.post("/api/analyze-lease", response_model=LeaseAnalysis)
async def analyze_lease_endpoint(
    file: Optional[UploadFile] = File(default=None, description="PDF lease document"),
    raw_text: Optional[str] = Form(default=None, description="Raw lease text"),
):
    """Analyze a residential lease agreement for clause risks.

    Accepts either a PDF file upload or raw text. Returns a structured
    LeaseAnalysis with clause-level risk assessments and educational notes.

    ⚠️ DISCLAIMER: This analysis is for informational and educational
    purposes only. It does not constitute legal advice.
    """
    # Validate input
    if not file and not raw_text:
        raise HTTPException(
            status_code=400,
            detail="Provide either a PDF file upload or raw lease text.",
        )

    try:
        pdf_bytes = None
        if file:
            # Validate file type
            if file.content_type not in [
                "application/pdf",
                "application/x-pdf",
                "image/png",
                "image/jpeg",
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type: {file.content_type}. "
                        "Please upload a PDF or image file."
                    ),
                )

            # Read file bytes (limit to 20MB)
            pdf_bytes = await file.read()
            if len(pdf_bytes) > 20 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum upload size is 20MB.",
                )

            logger.info(
                f"Received file: {file.filename} "
                f"({len(pdf_bytes)} bytes, {file.content_type})"
            )

        # Run the analysis pipeline
        result = await analyze_lease(
            pdf_bytes=pdf_bytes,
            raw_text=raw_text,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(
            status_code=502,
            detail=(
                "Analysis pipeline encountered an error. "
                "Please try again or contact support."
            ),
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis.",
        )


@app.get("/api/market-norms")
async def get_market_norms():
    """Return the static market baselines used for comparison."""
    import json
    from pathlib import Path

    norms_path = Path(__file__).parent / "data" / "market_norms.json"
    try:
        with open(norms_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Market norms data not found.",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
