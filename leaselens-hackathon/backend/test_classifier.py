"""Clause Classifier Agent Test Suite for LeaseLens.

Validates:
1. Heuristic classifier extraction accuracy for all clause types.
2. Risk level assignment against market norms thresholds.
3. Edge cases: no recognizable clauses, all clauses present, unusual values.
4. Market norms loading and caching.

Run with:
    pytest test_classifier.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from agents.classifier import _heuristic_classify_clauses, _load_market_norms
from schemas.lease_schema import ClauseCategory, RiskLevel


# =====================================================================
# 1. Market Norms Loading
# =====================================================================


class TestMarketNormsLoading:
    """Verify market norms data file loads correctly."""

    def test_market_norms_file_exists(self):
        """market_norms.json must exist in data/ directory."""
        norms_path = Path(__file__).parent / "data" / "market_norms.json"
        assert norms_path.exists(), f"Missing: {norms_path}"

    def test_market_norms_has_regions(self):
        """Loaded norms must contain 'regions' key with at least default."""
        norms = _load_market_norms()
        assert "regions" in norms
        assert "default" in norms["regions"]

    def test_market_norms_has_bengaluru(self):
        """Bengaluru regional overrides must be present."""
        norms = _load_market_norms()
        assert "bangalore" in norms["regions"] or "bengaluru" in norms["regions"]


# =====================================================================
# 2. Heuristic Classifier — Security Deposit
# =====================================================================


class TestSecurityDepositClassification:
    """Validate security deposit clause extraction and risk assignment."""

    def test_detects_security_deposit_clause(self):
        """Classifier must identify security deposit mention."""
        norms = _load_market_norms()
        text = "The Tenant agrees to pay a security deposit of 10 months rent."
        risks = _heuristic_classify_clauses(text, norms)
        categories = [r.category for r in risks]
        assert ClauseCategory.SECURITY_DEPOSIT in categories

    def test_extracts_deposit_months_correctly(self):
        """Classifier must parse the numeric months value from text."""
        norms = _load_market_norms()
        text = "Security deposit required: 12 months rent upfront."
        risks = _heuristic_classify_clauses(text, norms)
        deposit_risks = [r for r in risks if r.category == ClauseCategory.SECURITY_DEPOSIT]
        assert len(deposit_risks) == 1
        assert "12" in deposit_risks[0].extracted_text

    def test_high_deposit_gets_high_risk(self):
        """Deposit > 11 months should be flagged as HIGH risk."""
        norms = _load_market_norms()
        text = "Tenant must pay 15 months rent as security deposit."
        risks = _heuristic_classify_clauses(text, norms)
        deposit_risks = [r for r in risks if r.category == ClauseCategory.SECURITY_DEPOSIT]
        assert deposit_risks[0].risk_level == RiskLevel.HIGH

    def test_standard_deposit_gets_low_risk(self):
        """Deposit <= standard (10 months for Bengaluru) should be LOW risk."""
        norms = _load_market_norms()
        text = "Security deposit of 10 months rent is required."
        risks = _heuristic_classify_clauses(text, norms)
        deposit_risks = [r for r in risks if r.category == ClauseCategory.SECURITY_DEPOSIT]
        assert deposit_risks[0].risk_level == RiskLevel.LOW


# =====================================================================
# 3. Heuristic Classifier — Lock-in Period
# =====================================================================


class TestLockInPeriodClassification:
    """Validate lock-in period clause extraction."""

    def test_detects_lock_in_clause(self):
        """Classifier must identify lock-in period mention."""
        norms = _load_market_norms()
        text = "Both parties agree to a lock-in period of 6 months."
        risks = _heuristic_classify_clauses(text, norms)
        categories = [r.category for r in risks]
        assert ClauseCategory.LOCK_IN_PERIOD in categories

    def test_long_lock_in_gets_high_risk(self):
        """Lock-in of 6+ months should be HIGH risk."""
        norms = _load_market_norms()
        text = "Lock-in period is 6 months from the date of agreement."
        risks = _heuristic_classify_clauses(text, norms)
        lock_in_risks = [r for r in risks if r.category == ClauseCategory.LOCK_IN_PERIOD]
        assert lock_in_risks[0].risk_level == RiskLevel.HIGH

    def test_short_lock_in_gets_moderate_risk(self):
        """Lock-in of 2-5 months should be MODERATE risk."""
        norms = _load_market_norms()
        text = "Lock-in period of 3 months applies."
        risks = _heuristic_classify_clauses(text, norms)
        lock_in_risks = [r for r in risks if r.category == ClauseCategory.LOCK_IN_PERIOD]
        assert lock_in_risks[0].risk_level == RiskLevel.MODERATE


# =====================================================================
# 4. Heuristic Classifier — Rent Escalation
# =====================================================================


class TestRentEscalationClassification:
    """Validate rent escalation clause extraction."""

    def test_detects_escalation_clause(self):
        """Classifier must identify rent escalation/increase mention."""
        norms = _load_market_norms()
        text = "Rent shall increase by 5% upon renewal after 11 months."
        risks = _heuristic_classify_clauses(text, norms)
        categories = [r.category for r in risks]
        assert ClauseCategory.RENT_ESCALATION in categories

    def test_standard_escalation_gets_low_risk(self):
        """5% escalation (market standard) should be LOW risk."""
        norms = _load_market_norms()
        text = "Annual rent escalation of 5% on renewal."
        risks = _heuristic_classify_clauses(text, norms)
        esc_risks = [r for r in risks if r.category == ClauseCategory.RENT_ESCALATION]
        assert esc_risks[0].risk_level == RiskLevel.LOW

    def test_high_escalation_gets_high_risk(self):
        """Escalation > 10% should be HIGH risk."""
        norms = _load_market_norms()
        text = "Rent will increase by 20% annually upon renewal."
        risks = _heuristic_classify_clauses(text, norms)
        esc_risks = [r for r in risks if r.category == ClauseCategory.RENT_ESCALATION]
        assert esc_risks[0].risk_level == RiskLevel.HIGH


# =====================================================================
# 5. Edge Cases
# =====================================================================


class TestClassifierEdgeCases:
    """Edge case testing for the heuristic classifier."""

    def test_unrelated_text_produces_no_risks(self):
        """Text with no recognizable lease clauses should produce empty results."""
        norms = _load_market_norms()
        text = "The weather today is sunny with clear skies across the city."
        risks = _heuristic_classify_clauses(text, norms)
        assert len(risks) == 0

    def test_all_clauses_present_produces_multiple_risks(self):
        """Text mentioning all clause types should produce multiple risks."""
        norms = _load_market_norms()
        text = (
            "Security deposit of 10 months rent. "
            "Lock-in period of 6 months. "
            "Notice period of 1 month. "
            "Rent escalation of 5% annually upon renewal."
        )
        risks = _heuristic_classify_clauses(text, norms)
        assert len(risks) >= 4

    def test_educational_notes_contain_disclaimer(self):
        """All educational notes from classifier must contain professional review advisory."""
        norms = _load_market_norms()
        text = "Security deposit of 10 months rent. Lock-in period of 3 months."
        risks = _heuristic_classify_clauses(text, norms)
        for risk in risks:
            assert "qualified legal professional" in risk.educational_note.lower()

    def test_deviation_percentage_is_numeric(self):
        """Deviation percentages must be valid floats, not None for heuristic results."""
        norms = _load_market_norms()
        text = "Security deposit required: 10 months rent."
        risks = _heuristic_classify_clauses(text, norms)
        for risk in risks:
            assert isinstance(risk.deviation_percentage, float)
