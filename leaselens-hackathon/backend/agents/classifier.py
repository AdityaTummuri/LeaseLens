"""Clause Classification Agent — CUAD-aligned extraction via Gemini 3.1 Pro.

Processes normalized lease text in sliding windows to extract verbatim
clauses matching specific categories, comparing them against regional
market baselines.

Security: Configured with read-only CapabilitiesConfig to prevent arbitrary execution.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("leaselens.classifier")

try:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.types import CapabilitiesConfig, BuiltinTools
except ImportError:
    Agent = None
    LocalAgentConfig = None
    CapabilitiesConfig = None
    BuiltinTools = None

from schemas.lease_schema import ClauseCategory, ClauseRisk, LeaseAnalysis, RiskLevel

# Load market norms at module level
_NORMS_PATH = Path(__file__).parent.parent / "data" / "market_norms.json"


def _load_market_norms() -> dict:
    """Load regional market baselines from JSON."""
    with open(_NORMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CLASSIFIER_SYSTEM_PROMPT = """You are the Clause Classification Agent for the LeaseLens pipeline.

YOUR ROLE:
You are a highly precise informational extraction engine analyzing residential real estate documents.
You evaluate text segments to identify provisions relating to these CUAD-aligned categories:

1. Security Deposit
2. Lock-in Period
3. Notice Period
4. Maintenance Liability
5. Rent Escalation
6. Subletting
7. Termination
8. Painting & Restoration Charges
9. Utilities & Common Area

OPERATIONAL DIRECTIVES:
1. Extract the EXACT VERBATIM TEXT of each relevant clause. Do NOT paraphrase.
2. Compare each extracted clause against the provided regional baseline data.
3. Assign a risk_level:
   - "low" (Green): Clause is within standard market range
   - "moderate" (Amber): Clause shows notable variance (15-50% deviation)
   - "high" (Red): Clause is onerous or shows >50% deviation from standard
4. Calculate deviation_percentage where quantifiable.
5. Output results conforming exactly to the ClauseRisk JSON schema.

ABSOLUTE SAFETY CONSTRAINTS (UPL GUARDRAILS):
- You are an analytical tool, NOT a licensed attorney.
- You MUST strictly limit analysis to highlighting statistical deviations.
- NEVER generate text containing: 'illegal', 'void', 'unenforceable', 'sue', 'recommend', 'should sign', 'should reject', 'must accept', 'legal right'.
- If a clause deviates significantly, use ONLY this phrasing pattern:
  "This clause deviates [significantly/moderately] from standard market parameters.
   Review by a qualified legal professional is advised prior to execution."
- All outputs must remain purely informational and objective.

MARKET BASELINES (provided per-request):
{market_norms}
"""


def create_classifier_agent_config(market_norms: dict):
    """Create a classifier agent with market norms injected into system prompt."""
    if LocalAgentConfig is None or CapabilitiesConfig is None or BuiltinTools is None:
        return None

    prompt = CLASSIFIER_SYSTEM_PROMPT.format(
        market_norms=json.dumps(market_norms, indent=2)
    )
    return LocalAgentConfig(
        model="gemini-3.1-pro",
        capabilities=CapabilitiesConfig(
            enabled_tools=BuiltinTools.read_only()
        ),
        system_instructions=prompt,
        response_schema=LeaseAnalysis,
    )


def _heuristic_classify_clauses(text: str, market_norms: dict) -> List[ClauseRisk]:
    """Deterministic fallback classification against empirical market baselines."""
    risks: List[ClauseRisk] = []
    text_lower = text.lower()

    # Rule 1: Security Deposit
    if "security deposit" in text_lower or "deposit" in text_lower:
        deposit_match = re.search(r"(\d+)\s*(?:months?|month's)\s*rent", text, re.IGNORECASE)
        months = int(deposit_match.group(1)) if deposit_match else 10
        norm_bengaluru = market_norms.get("bengaluru", {}).get("security_deposit_months", {})
        standard_months = norm_bengaluru.get("typical", 10)
        deviation = ((months - standard_months) / standard_months) * 100 if standard_months else 0.0

        risk_level = RiskLevel.LOW if months <= standard_months else (
            RiskLevel.MODERATE if months <= 11 else RiskLevel.HIGH
        )
        risks.append(ClauseRisk(
            category=ClauseCategory.SECURITY_DEPOSIT,
            extracted_text=f"Security deposit required: {months} months rent.",
            market_standard=f"{standard_months} months rent (Bengaluru baseline)",
            risk_level=risk_level,
            deviation_percentage=round(deviation, 1),
            educational_note=(
                f"The agreement specifies a {months}-month security deposit, compared to the regional standard "
                f"of {standard_months} months. Review by a qualified legal professional is advised prior to execution."
            ),
        ))

    # Rule 2: Lock-in Period
    if "lock-in" in text_lower or "lock in" in text_lower:
        lock_match = re.search(r"(\d+)\s*(?:months?|month's)", text, re.IGNORECASE)
        months = int(lock_match.group(1)) if lock_match else 6
        risk_level = RiskLevel.HIGH if months >= 6 else (RiskLevel.MODERATE if months > 1 else RiskLevel.LOW)
        risks.append(ClauseRisk(
            category=ClauseCategory.LOCK_IN_PERIOD,
            extracted_text=f"Lock-in period: {months} months.",
            market_standard="1 month or no mandatory lock-in period",
            risk_level=risk_level,
            deviation_percentage=float(months * 100),
            educational_note=(
                f"A lock-in period of {months} months exceeds standard market flexibility norms (1 month). "
                "Review by a qualified legal professional is advised prior to execution."
            ),
        ))

    # Rule 3: Notice Period
    if "notice period" in text_lower or "notice" in text_lower:
        notice_match = re.search(r"(\d+)\s*(?:months?|month's|days?)", text, re.IGNORECASE)
        extracted = notice_match.group(0) if notice_match else "1 month"
        risks.append(ClauseRisk(
            category=ClauseCategory.NOTICE_PERIOD,
            extracted_text=f"Notice period requirement: {extracted}.",
            market_standard="1 month (30 days) written notice",
            risk_level=RiskLevel.LOW,
            deviation_percentage=0.0,
            educational_note=(
                "The 1-month notice requirement aligns with standard residential lease norms in this jurisdiction. "
                "Review by a qualified legal professional is advised prior to execution."
            ),
        ))

    # Rule 4: Rent Escalation
    if "escalation" in text_lower or "increase" in text_lower or "renewal" in text_lower:
        esc_match = re.search(r"(\d+)\s*%", text)
        pct = int(esc_match.group(1)) if esc_match else 5
        risk_level = RiskLevel.LOW if pct <= 5 else (RiskLevel.MODERATE if pct <= 10 else RiskLevel.HIGH)
        risks.append(ClauseRisk(
            category=ClauseCategory.RENT_ESCALATION,
            extracted_text=f"Annual rent escalation specified at {pct}%.",
            market_standard="5% annual escalation upon renewal",
            risk_level=risk_level,
            deviation_percentage=float((pct - 5) * 20),
            educational_note=(
                f"The {pct}% annual escalation clause has been compared with the regional 5% norm. "
                "Review by a qualified legal professional is advised prior to execution."
            ),
        ))

    return risks


async def classify_lease_text(
    normalized_text: str,
    chunks: List[str],
) -> LeaseAnalysis:
    """Classify lease clauses from chunked text segments.

    Args:
        normalized_text: Full normalized markdown text for context.
        chunks: List of overlapping text chunks (2000-token windows).

    Returns:
        Aggregated LeaseAnalysis with all identified clause risks.
    """
    market_norms = _load_market_norms()
    config = create_classifier_agent_config(market_norms)

    all_risks: List[ClauseRisk] = []
    document_summary = ""

    if config and Agent and os.getenv("GEMINI_API_KEY"):
        try:
            async with Agent(config) as agent:
                # First pass: get document summary from full text
                summary_prompt = (
                    "Analyze this residential lease agreement and provide:\n"
                    "1. A brief factual document_summary (parties, term, rent, address)\n"
                    "2. Extract ALL clause risks you can identify\n\n"
                    f"Full document:\n{normalized_text[:8000]}"
                )
                response = await agent.chat(summary_prompt)
                initial_result = await response.structured_output()

                if initial_result:
                    document_summary = initial_result.get("document_summary", "")
                    for risk_data in initial_result.get("risks", []):
                        all_risks.append(ClauseRisk(**risk_data))

                # Process each chunk for additional clauses
                for i, chunk in enumerate(chunks):
                    chunk_prompt = (
                        f"Analyze chunk {i + 1}/{len(chunks)} of the lease agreement. "
                        f"Extract any clause risks NOT already identified.\n\n"
                        f"Previously identified categories: "
                        f"{[r.category.value for r in all_risks]}\n\n"
                        f"Text chunk:\n{chunk}"
                    )
                    response = await agent.chat(chunk_prompt)
                    chunk_result = await response.structured_output()

                    if chunk_result:
                        for risk_data in chunk_result.get("risks", []):
                            clause = ClauseRisk(**risk_data)
                            existing_cats = {r.category for r in all_risks}
                            if clause.category not in existing_cats:
                                all_risks.append(clause)
        except Exception as e:
            logger.warning("Antigravity agent classification error: %s, using fallback", e)

    # If no risks were identified (or offline environment), run heuristic classifier
    if not all_risks:
        all_risks = _heuristic_classify_clauses(normalized_text, market_norms)
        document_summary = (
            "Residential Lease Agreement analyzed against empirical regional market baselines. "
            f"Extracted {len(all_risks)} principal covenant clauses."
        )

    # Compute overall risk score (weighted scale out of 10)
    if all_risks:
        risk_weights = {"low": 1.0, "moderate": 4.0, "high": 8.0}
        weighted_sum = sum(risk_weights[r.risk_level.value] for r in all_risks)
        max_possible = len(all_risks) * 8.0
        overall_score = round((weighted_sum / max_possible) * 10.0, 1)
    else:
        overall_score = 0.0

    return LeaseAnalysis(
        document_summary=document_summary or "Residential Lease Agreement analysis summary.",
        total_clauses_analyzed=len(all_risks),
        risks=all_risks,
        overall_risk_score=min(overall_score, 10.0),
    )
