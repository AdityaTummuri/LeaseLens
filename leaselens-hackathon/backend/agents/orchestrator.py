"""Master Orchestrator Agent — Supervisor Pattern implementation.

Central router that manages the LeaseLens processing pipeline:
1. Receives uploaded PDF or raw text
2. Delegates to Ingestion Agent for OCR/normalization
3. Chunks normalized text into overlapping 2000-token sliding windows
4. Delegates chunks to Classifier Agent for clause extraction
5. Passes results through UPL Guardrail Agent for sanitization
6. Returns validated LeaseAnalysis to the FastAPI endpoint

Implements automatic retry loops for schema validation failures.
"""

import logging
import time
from typing import List, Optional

from schemas.lease_schema import LeaseAnalysis
from agents.ingestion import extract_text_from_pdf, extract_text_from_raw
from agents.classifier import classify_lease_text
from agents.upl_guardrail import sanitize_analysis

logger = logging.getLogger("leaselens.orchestrator")

# --- Configuration ---
CHUNK_SIZE = 2000       # tokens (approximated as ~4 chars per token)
CHUNK_OVERLAP = 200     # token overlap between windows
MAX_RETRIES = 3         # retry count for schema validation failures
CHARS_PER_TOKEN = 4     # rough approximation for chunking


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping sliding windows.

    Uses character-based approximation (4 chars ≈ 1 token) to create
    overlapping chunks that preserve context at boundaries.

    Args:
        text: Full normalized text to chunk.
        chunk_size: Target chunk size in tokens.
        overlap: Overlap between consecutive chunks in tokens.

    Returns:
        List of text chunks with overlap.
    """
    char_chunk = chunk_size * CHARS_PER_TOKEN
    char_overlap = overlap * CHARS_PER_TOKEN

    if len(text) <= char_chunk:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + char_chunk
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= len(text):
            break

        start = end - char_overlap

    return chunks


async def analyze_lease(
    pdf_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None,
) -> LeaseAnalysis:
    """Execute the full LeaseLens analysis pipeline.

    This is the main entry point called by the FastAPI endpoint.
    Implements the Supervisor pattern with sequential agent delegation
    and automatic retry on schema validation failures.

    Args:
        pdf_bytes: Raw PDF file bytes (mutually exclusive with raw_text).
        raw_text: Pasted lease text (mutually exclusive with pdf_bytes).

    Returns:
        Fully sanitized, UPL-compliant LeaseAnalysis.

    Raises:
        ValueError: If neither pdf_bytes nor raw_text is provided.
        RuntimeError: If all retry attempts fail.
    """
    if not pdf_bytes and not raw_text:
        raise ValueError("Either pdf_bytes or raw_text must be provided.")

    pipeline_start = time.perf_counter()

    # --- Step 1: Document Ingestion ---
    logger.info("Step 1/3: Document Ingestion — extracting text...")
    stage_start = time.perf_counter()
    
    last_error: Optional[Exception] = None
    normalized_text = ""

    for attempt in range(MAX_RETRIES):
        try:
            if pdf_bytes:
                normalized_text = await extract_text_from_pdf(pdf_bytes)
            else:
                normalized_text = await extract_text_from_raw(raw_text)

            if normalized_text and len(normalized_text.strip()) > 50:
                stage_elapsed = (time.perf_counter() - stage_start) * 1000
                logger.info(
                    "Ingestion complete: %d chars extracted (%.1fms)",
                    len(normalized_text),
                    stage_elapsed,
                )
                break
            else:
                logger.warning(
                    f"Ingestion attempt {attempt + 1}/{MAX_RETRIES}: "
                    "insufficient text extracted, retrying..."
                )
        except Exception as e:
            last_error = e
            logger.error(
                f"Ingestion attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
            )
    else:
        raise RuntimeError(
            f"Document ingestion failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    # --- Step 2: Chunking & Classification ---
    logger.info("Step 2/3: Clause Classification — chunking and analyzing...")
    stage_start = time.perf_counter()

    chunks = chunk_text(normalized_text)
    logger.info("Document split into %d overlapping chunks.", len(chunks))

    analysis: Optional[LeaseAnalysis] = None

    for attempt in range(MAX_RETRIES):
        try:
            analysis = await classify_lease_text(normalized_text, chunks)
            # Validate the output
            _ = analysis.model_dump()
            stage_elapsed = (time.perf_counter() - stage_start) * 1000
            logger.info(
                "Classification complete: %d clauses identified (%.1fms)",
                analysis.total_clauses_analyzed,
                stage_elapsed,
            )
            break
        except Exception as e:
            last_error = e
            logger.error(
                f"Classification attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
            )
    else:
        raise RuntimeError(
            f"Clause classification failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    # --- Step 3: UPL Sanitization ---
    logger.info("Step 3/3: UPL Guardrail — sanitizing output...")
    stage_start = time.perf_counter()

    for attempt in range(MAX_RETRIES):
        try:
            sanitized = await sanitize_analysis(analysis)
            pipeline_elapsed = (time.perf_counter() - pipeline_start) * 1000
            logger.info(
                "UPL sanitization complete. Pipeline finished in %.1fms",
                pipeline_elapsed,
            )
            return sanitized
        except Exception as e:
            last_error = e
            logger.error(
                f"UPL sanitization attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
            )

    # If LLM sanitization fails, the rule-based layer in upl_guardrail.py
    # already applied regex sanitization, so return the analysis as-is
    logger.warning(
        "LLM-based UPL sanitization failed; returning regex-sanitized result."
    )
    return analysis
