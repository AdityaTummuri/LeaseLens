"""Shared pytest fixtures for LeaseLens backend test suite.

Provides reusable test data and client instances for all test modules.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from schemas.lease_schema import (
    ClauseCategory,
    ClauseRisk,
    LeaseAnalysis,
    RiskLevel,
)


@pytest.fixture
def test_client():
    """Provide a FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def sample_lease_text():
    """Realistic residential lease text containing all major clause types."""
    return (
        "RESIDENTIAL LEASE AGREEMENT\n\n"
        "This agreement is made between Mr. Landlord (Owner) and Mr. Tenant (Tenant) "
        "for the property at 123 Main Street, Bengaluru.\n\n"
        "1. Security Deposit: The Tenant agrees to deposit an amount equal to "
        "10 months rent as security deposit, refundable upon vacating.\n\n"
        "2. Lock-in Period: Both parties agree to a lock-in period of 6 months "
        "from the date of this agreement.\n\n"
        "3. Notice Period: Tenant must provide 1 month written notice before vacating "
        "the premises.\n\n"
        "4. Maintenance Liability: Tenant responsible for internal repairs up to "
        "Rs 5,000 per incident.\n\n"
        "5. Rent Escalation: Rent shall increase by 5% upon renewal after 11 months.\n\n"
        "6. Monthly Rent: Rs 25,000 payable on the 1st of each month.\n\n"
        "7. Term: This agreement is valid for 11 months from the date of execution."
    )


@pytest.fixture
def sample_short_text():
    """Minimal lease text that is short enough to fit in a single chunk."""
    return (
        "Lease Agreement: Security deposit of 2 months rent. "
        "Notice period of 30 days. Rent Rs 15,000 per month."
    )


@pytest.fixture
def sample_empty_text():
    """Empty text for edge case testing."""
    return ""


@pytest.fixture
def sample_market_norms():
    """Market norms data matching the structure in data/market_norms.json."""
    return {
        "metadata": {
            "version": "1.0.0",
            "description": "Test market norms",
        },
        "regions": {
            "default": {
                "label": "Pan-India Standard",
                "norms": {
                    "Security Deposit": {
                        "standard_value": "2 months rent",
                        "standard_range": "1-3 months rent",
                        "high_threshold": "4+ months rent",
                    },
                    "Lock-in Period": {
                        "standard_value": "0-1 months",
                        "standard_range": "0-2 months",
                        "high_threshold": "3+ months",
                    },
                },
            },
            "bengaluru": {
                "label": "Bangalore Metro",
                "overrides": {
                    "Security Deposit": {
                        "standard_value": "10 months rent",
                        "standard_range": "8-10 months rent",
                        "high_threshold": "12+ months rent",
                    },
                },
            },
        },
    }


@pytest.fixture
def mock_clause_risk():
    """A single valid ClauseRisk instance for testing."""
    return ClauseRisk(
        category=ClauseCategory.SECURITY_DEPOSIT,
        extracted_text="Security deposit required: 10 months rent.",
        market_standard="10 months rent (Bengaluru baseline)",
        risk_level=RiskLevel.LOW,
        deviation_percentage=0.0,
        educational_note=(
            "The agreement specifies a 10-month security deposit, consistent "
            "with the regional standard of 10 months. "
            "Review by a qualified legal professional is advised prior to execution."
        ),
    )


@pytest.fixture
def mock_lease_analysis(mock_clause_risk):
    """A complete valid LeaseAnalysis instance for testing."""
    return LeaseAnalysis(
        document_title="Test Lease Agreement",
        document_summary="Residential lease for 123 Main Street, Bengaluru.",
        total_clauses_analyzed=1,
        risks=[mock_clause_risk],
        overall_risk_score=1.3,
    )
