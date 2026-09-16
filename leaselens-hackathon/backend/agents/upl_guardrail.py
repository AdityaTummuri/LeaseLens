"""UPL (Unauthorized Practice of Law) Guardrail Agent.

Final-stage safety filter that sanitizes all agent outputs to ensure
strict compliance with UPL regulations. Forces neutral statistical
phrasing and strips any language that could constitute legal advice.

Configured with read-only CapabilitiesConfig to prevent arbitrary execution.
"""

import re
from typing import Optional

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import CapabilitiesConfig, BuiltinTools

from schemas.lease_schema import LeaseAnalysis, ClauseRisk

# Forbidden terms that indicate legal advice
FORBIDDEN_TERMS = [
    r"\billegal\b",
    r"\bvoid\b",
    r"\bunenforceable\b",
    r"\bsue\b",
    r"\brecommend\b",
    r"\bshould sign\b",
    r"\bshould reject\b",
    r"\bshould not sign\b",
    r"\bmust accept\b",
    r"\bmust reject\b",
    r"\blegal right\b",
    r"\byour rights\b",
    r"\btake legal action\b",
    r"\bfile a complaint\b",
    r"\bfile a case\b",
    r"\bunlawful\b",
    r"\bfraudulent\b",
    r"\bpredatory\b",
]

FORBIDDEN_PATTERN = re.compile(
    "|".join(FORBIDDEN_TERMS), re.IGNORECASE
)

UPL_SYSTEM_PROMPT = """You are the UPL Guardrail Agent for the LeaseLens pipeline.

YOUR SOLE RESPONSIBILITY:
Review and sanitize the provided lease analysis JSON to ensure ABSOLUTE COMPLIANCE 
with Unauthorized Practice of Law (UPL) regulations.

SANITIZATION RULES:
1. SCAN every `educational_note` field for advisory or directive language.
2. REPLACE any instance of the following forbidden terms with neutral alternatives:
   - "illegal" → "deviates from standard market practice"
   - "void" → "may warrant further review"
   - "unenforceable" → "uncommon in standard agreements"
   - "sue" / "take legal action" → "seek consultation with a qualified legal professional"
   - "recommend" → "note that"
   - "should sign/reject" → remove entirely, replace with factual observation
   - "predatory" → "significantly above market standard"
3. ENSURE all educational_note fields end with:
   "Review by a qualified legal professional is advised prior to execution."
4. PRESERVE all other data fields (extracted_text, market_standard, etc.) unchanged.
5. OUTPUT the sanitized LeaseAnalysis JSON with identical structure.

You must NEVER add your own legal opinions or recommendations.
"""


def create_upl_agent_config() -> LocalAgentConfig:
    """Create a strictly read-only UPL guardrail agent."""
    return LocalAgentConfig(
        model="gemini-3.6-flash",
        capabilities=CapabilitiesConfig(
            enabled_tools=BuiltinTools.read_only()
        ),
        system_instructions=UPL_SYSTEM_PROMPT,
        response_schema=LeaseAnalysis,
    )


def _rule_based_sanitize(text: str) -> str:
    """Apply deterministic regex-based sanitization as a first pass.

    This ensures UPL compliance even if the LLM agent fails to catch
    a forbidden term.
    """
    replacements = {
        r"\billegal\b": "deviates from standard market practice",
        r"\bvoid\b": "may warrant further review",
        r"\bunenforceable\b": "uncommon in standard agreements",
        r"\bsue\b": "seek consultation with a qualified legal professional",
        r"\btake legal action\b": "seek consultation with a qualified legal professional",
        r"\bfile a complaint\b": "seek consultation with a qualified legal professional",
        r"\bfile a case\b": "seek consultation with a qualified legal professional",
        r"\brecommend\b": "note that",
        r"\bshould sign\b": "[removed — no directive provided]",
        r"\bshould reject\b": "[removed — no directive provided]",
        r"\bshould not sign\b": "[removed — no directive provided]",
        r"\bmust accept\b": "[removed — no directive provided]",
        r"\bmust reject\b": "[removed — no directive provided]",
        r"\bpredatory\b": "significantly above market standard",
        r"\bunlawful\b": "deviates from standard market practice",
        r"\bfraudulent\b": "requires independent verification",
        r"\blegal right\b": "standard market expectation",
        r"\byour rights\b": "standard market expectations",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _ensure_disclaimer_suffix(note: str) -> str:
    """Ensure every educational note ends with the standard advisory."""
    suffix = "Review by a qualified legal professional is advised prior to execution."
    if suffix.lower() not in note.lower():
        note = note.rstrip(". ") + ". " + suffix
    return note


async def sanitize_analysis(analysis: LeaseAnalysis) -> LeaseAnalysis:
    """Apply dual-layer UPL sanitization: rule-based + LLM agent.

    Layer 1 (deterministic): Regex-based forbidden term replacement.
    Layer 2 (semantic): LLM agent reviews for subtler advisory language.

    Args:
        analysis: Raw LeaseAnalysis from the Classifier Agent.

    Returns:
        Sanitized LeaseAnalysis guaranteed to be UPL-compliant.
    """
    # --- Layer 1: Deterministic regex sanitization ---
    sanitized_risks = []
    for risk in analysis.risks:
        sanitized_note = _rule_based_sanitize(risk.educational_note)
        sanitized_note = _ensure_disclaimer_suffix(sanitized_note)
        sanitized_risks.append(risk.model_copy(update={
            "educational_note": sanitized_note
        }))

    partially_sanitized = analysis.model_copy(update={
        "risks": sanitized_risks
    })

    # --- Layer 2: LLM semantic sanitization ---
    config = create_upl_agent_config()

    try:
        async with Agent(config) as agent:
            prompt = (
                "Review and sanitize this lease analysis for UPL compliance. "
                "Ensure NO educational_note contains legal advice, directives, "
                "or forbidden terminology.\n\n"
                f"{partially_sanitized.model_dump_json(indent=2)}"
            )
            response = await agent.chat(prompt)
            result = await response.structured_output()

            if result:
                return LeaseAnalysis(**result)
    except Exception:
        # If LLM layer fails, the regex layer already sanitized
        pass

    return partially_sanitized


def check_for_violations(text: str) -> Optional[str]:
    """Check if text contains UPL-violating language.

    Args:
        text: Text to check.

    Returns:
        The matched forbidden term, or None if clean.
    """
    match = FORBIDDEN_PATTERN.search(text)
    return match.group(0) if match else None
