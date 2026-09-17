"""Pydantic Schema Validation Test Suite for LeaseLens.

Validates:
1. ClauseRisk construction with valid and invalid data.
2. LeaseAnalysis model constraints (score bounds, default disclaimer).
3. Enum membership for RiskLevel and ClauseCategory.
4. Edge cases: empty risks list, boundary values, missing optional fields.

Run with:
    pytest test_schemas.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from schemas.lease_schema import (
    ClauseCategory,
    ClauseRisk,
    LeaseAnalysis,
    RiskLevel,
)


# =====================================================================
# 1. RiskLevel Enum Tests
# =====================================================================


class TestRiskLevelEnum:
    """Verify RiskLevel enum membership and string values."""

    def test_risk_level_values(self):
        """All three risk levels must exist with correct string values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MODERATE.value == "moderate"
        assert RiskLevel.HIGH.value == "high"

    def test_risk_level_from_string(self):
        """Enum must be constructible from string values."""
        assert RiskLevel("low") == RiskLevel.LOW
        assert RiskLevel("moderate") == RiskLevel.MODERATE
        assert RiskLevel("high") == RiskLevel.HIGH

    def test_invalid_risk_level_raises(self):
        """Invalid risk level string must raise ValueError."""
        with pytest.raises(ValueError):
            RiskLevel("critical")


# =====================================================================
# 2. ClauseCategory Enum Tests
# =====================================================================


class TestClauseCategoryEnum:
    """Verify all CUAD-aligned clause categories are defined."""

    def test_all_categories_exist(self):
        """All 10 clause categories must be defined."""
        expected = {
            "Security Deposit",
            "Lock-in Period",
            "Notice Period",
            "Maintenance Liability",
            "Rent Escalation",
            "Subletting",
            "Termination",
            "Painting & Restoration Charges",
            "Utilities & Common Area",
            "Other",
        }
        actual = {c.value for c in ClauseCategory}
        assert actual == expected

    def test_category_count(self):
        """Exactly 10 categories must be defined."""
        assert len(ClauseCategory) == 10


# =====================================================================
# 3. ClauseRisk Model Tests
# =====================================================================


class TestClauseRiskModel:
    """Validate ClauseRisk Pydantic model construction and constraints."""

    def test_valid_clause_risk_construction(self, mock_clause_risk):
        """A well-formed ClauseRisk must construct without error."""
        assert mock_clause_risk.category == ClauseCategory.SECURITY_DEPOSIT
        assert mock_clause_risk.risk_level == RiskLevel.LOW
        assert mock_clause_risk.deviation_percentage == 0.0

    def test_clause_risk_with_none_deviation(self):
        """deviation_percentage is optional and defaults to None."""
        risk = ClauseRisk(
            category=ClauseCategory.NOTICE_PERIOD,
            extracted_text="Notice period: 1 month.",
            market_standard="1 month standard",
            risk_level=RiskLevel.LOW,
            educational_note="Standard notice period observed.",
        )
        assert risk.deviation_percentage is None

    def test_clause_risk_rejects_empty_extracted_text(self):
        """extracted_text must have min_length=1; empty string rejected."""
        with pytest.raises(Exception):
            ClauseRisk(
                category=ClauseCategory.SUBLETTING,
                extracted_text="",
                market_standard="Standard subletting clause",
                risk_level=RiskLevel.LOW,
                educational_note="Subletting clause analysis.",
            )

    def test_clause_risk_serialization_roundtrip(self, mock_clause_risk):
        """Model must survive dump → reconstruct roundtrip."""
        data = mock_clause_risk.model_dump()
        reconstructed = ClauseRisk(**data)
        assert reconstructed.category == mock_clause_risk.category
        assert reconstructed.extracted_text == mock_clause_risk.extracted_text
        assert reconstructed.risk_level == mock_clause_risk.risk_level


# =====================================================================
# 4. LeaseAnalysis Model Tests
# =====================================================================


class TestLeaseAnalysisModel:
    """Validate LeaseAnalysis Pydantic model construction and constraints."""

    def test_valid_analysis_construction(self, mock_lease_analysis):
        """A well-formed LeaseAnalysis must construct without error."""
        assert mock_lease_analysis.total_clauses_analyzed == 1
        assert len(mock_lease_analysis.risks) == 1
        assert 0.0 <= mock_lease_analysis.overall_risk_score <= 10.0

    def test_default_disclaimer_present(self, mock_lease_analysis):
        """The mandatory legal disclaimer must be populated by default."""
        assert "does not constitute legal advice" in mock_lease_analysis.disclaimer
        assert "informational" in mock_lease_analysis.disclaimer

    def test_default_document_title(self):
        """document_title defaults to 'Untitled Lease Agreement'."""
        analysis = LeaseAnalysis(
            document_summary="Test summary.",
            total_clauses_analyzed=0,
            risks=[],
            overall_risk_score=0.0,
        )
        assert analysis.document_title == "Untitled Lease Agreement"

    def test_empty_risks_list_valid(self):
        """LeaseAnalysis with zero risks is valid."""
        analysis = LeaseAnalysis(
            document_summary="No clauses found.",
            total_clauses_analyzed=0,
            risks=[],
            overall_risk_score=0.0,
        )
        assert analysis.risks == []
        assert analysis.total_clauses_analyzed == 0

    def test_risk_score_lower_bound(self):
        """overall_risk_score must reject negative values."""
        with pytest.raises(Exception):
            LeaseAnalysis(
                document_summary="Test.",
                total_clauses_analyzed=0,
                risks=[],
                overall_risk_score=-1.0,
            )

    def test_risk_score_upper_bound(self):
        """overall_risk_score must reject values above 10.0."""
        with pytest.raises(Exception):
            LeaseAnalysis(
                document_summary="Test.",
                total_clauses_analyzed=0,
                risks=[],
                overall_risk_score=11.0,
            )

    def test_risk_score_at_boundary(self):
        """Risk scores at exact boundaries (0.0, 10.0) are valid."""
        zero = LeaseAnalysis(
            document_summary="Zero risk.",
            total_clauses_analyzed=0,
            risks=[],
            overall_risk_score=0.0,
        )
        max_score = LeaseAnalysis(
            document_summary="Max risk.",
            total_clauses_analyzed=0,
            risks=[],
            overall_risk_score=10.0,
        )
        assert zero.overall_risk_score == 0.0
        assert max_score.overall_risk_score == 10.0

    def test_serialization_includes_all_fields(self, mock_lease_analysis):
        """Model dump must include all required fields."""
        data = mock_lease_analysis.model_dump()
        required_keys = {
            "document_title",
            "document_summary",
            "total_clauses_analyzed",
            "risks",
            "overall_risk_score",
            "disclaimer",
        }
        assert required_keys.issubset(data.keys())
