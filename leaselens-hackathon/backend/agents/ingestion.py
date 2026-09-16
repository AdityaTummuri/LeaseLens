"""Document Ingestion Agent — OCR and text extraction via Gemini 3.6 Flash.

Processes uploaded PDFs and images using Gemini's native multimodal
capabilities. Outputs clean, normalized markdown text stripped of
irrelevant headers, footers, and formatting artifacts.
"""

import base64

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import CapabilitiesConfig, BuiltinTools

INGESTION_SYSTEM_PROMPT = """You are the Document Ingestion Agent for the LeaseLens pipeline.

YOUR SOLE RESPONSIBILITY:
Convert the provided document (PDF pages or images) into clean, well-structured markdown text.

OPERATIONAL DIRECTIVES:
1. Perform OCR on all pages, preserving paragraph structure and clause numbering.
2. Strip out irrelevant content: page numbers, headers, footers, watermarks, logos.
3. Preserve the EXACT wording of all legal clauses — do NOT paraphrase or summarize.
4. Use markdown formatting:
   - ## for major section headings
   - ### for sub-section headings
   - Numbered lists for enumerated clauses
   - > blockquotes for important defined terms
5. If text is illegible or ambiguous, mark it as [ILLEGIBLE] rather than guessing.
6. Output ONLY the extracted text. No commentary, analysis, or opinions.
"""


def create_ingestion_agent_config() -> LocalAgentConfig:
    """Create a read-only configured ingestion agent."""
    return LocalAgentConfig(
        model="gemini-3.6-flash",
        capabilities=CapabilitiesConfig(
            enabled_tools=BuiltinTools.read_only()
        ),
        system_instructions=INGESTION_SYSTEM_PROMPT,
    )


async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract and normalize text from a PDF document.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Clean markdown text of the lease agreement.
    """
    config = create_ingestion_agent_config()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    prompt = (
        "Extract all text from the following residential lease agreement PDF. "
        "Preserve exact clause wording and structure."
    )

    async with Agent(config) as agent:
        response = await agent.chat(
            prompt,
            attachments=[{
                "mime_type": "application/pdf",
                "data": pdf_b64,
            }],
        )
        return await response.text()


async def extract_text_from_raw(raw_text: str) -> str:
    """Normalize raw pasted text into structured markdown.

    Args:
        raw_text: Raw text pasted by the user.

    Returns:
        Cleaned and structured markdown text.
    """
    config = create_ingestion_agent_config()

    prompt = (
        "The following is raw text from a residential lease agreement. "
        "Clean it up into well-structured markdown, preserving exact "
        "clause wording. Remove any formatting artifacts.\n\n"
        f"{raw_text}"
    )

    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        return await response.text()
