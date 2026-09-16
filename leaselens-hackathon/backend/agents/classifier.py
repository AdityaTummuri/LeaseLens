"""Clause Classification Agent — CUAD-aligned extraction via Gemini 3.1 Pro.

Processes normalized lease text in sliding windows to extract verbatim
clauses matching specific categories, comparing them against regional
market baselines.
"""

import json
from pathlib import Path
from typing import List

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import CapabilitiesConfig, BuiltinTools

from schemas.lease_schema import ClauseRisk, LeaseAnalysis

# Load market norms at module level
_NORMS_PATH = Path(__file__).parent.parent / "data" / "market_norms.json"


def _load_market_norms() -> dict:
    """Load regional market baselines from JSON."""
    with open(_NORMS_PATH, "r") as f:
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


def create_classifier_agent_config(market_norms: dict) -> LocalAgentConfig:
    """Create a classifier agent with market norms injected into system prompt."""
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

    async with Agent(config) as agent:
        # First pass: get document summary from full text (truncated if needed)
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

        # Process each chunk for clauses that may have been missed
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
                    # Deduplicate by category
                    existing_cats = {r.category for r in all_risks}
                    if clause.category not in existing_cats:
                        all_risks.append(clause)

    # Compute overall risk score
    if all_risks:
        risk_weights = {"low": 1.0, "moderate": 4.0, "high": 8.0}
        weighted_sum = sum(risk_weights[r.risk_level.value] for r in all_risks)
        max_possible = len(all_risks) * 8.0
        overall_score = round((weighted_sum / max_possible) * 10.0, 1)
    else:
        overall_score = 0.0

    return LeaseAnalysis(
        document_summary=document_summary or "Unable to extract document summary.",
        total_clauses_analyzed=len(all_risks),
        risks=all_risks,
        overall_risk_score=min(overall_score, 10.0),
    )
