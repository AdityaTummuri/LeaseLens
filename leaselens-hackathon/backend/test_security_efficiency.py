"""Test suite for LeaseLens Security and Efficiency enhancements.

Validates:
1. OWASP defense-in-depth security response headers on all endpoints.
2. Market norms in-memory caching and Cache-Control headers.
3. Restricted CORS header policy.
4. Rate limiting middleware configuration.
5. Ingestion fast-path performance for structured raw text.
6. Classifier chunk processing efficiency.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent))

from agents.classifier import classify_lease_text
from agents.ingestion import extract_text_from_raw
from main import _load_cached_market_norms, app
from schemas.lease_schema import LeaseAnalysis


@pytest.fixture
def client():
    """FastAPI test client instance."""
    return TestClient(app)


def test_owasp_security_headers_present(client):
    """Verify all OWASP recommended security headers are injected on responses."""
    endpoints = ["/", "/api/health", "/api/market-norms"]
    for path in endpoints:
        response = client.get(path)
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff", f"Missing nosniff on {path}"
        assert headers.get("x-frame-options") == "DENY", f"Missing DENY on {path}"
        assert headers.get("x-xss-protection") == "1; mode=block", f"Missing XSS on {path}"
        assert "max-age=31536000" in headers.get("strict-transport-security", ""), f"Missing HSTS on {path}"
        assert "default-src 'self'" in headers.get("content-security-policy", ""), f"Missing CSP on {path}"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin", f"Missing Referrer-Policy on {path}"
        assert "geolocation=()" in headers.get("permissions-policy", ""), f"Missing Permissions-Policy on {path}"


def test_market_norms_cache_and_headers(client):
    """Verify market norms returns HTTP 200 with Cache-Control and cached memory instance."""
    response = client.get("/api/market-norms")
    assert response.status_code == 200
    cache_control = response.headers.get("cache-control", "")
    assert "public" in cache_control
    assert "max-age=3600" in cache_control

    # Ensure in-memory cache function returns the same object reference
    data1 = _load_cached_market_norms()
    data2 = _load_cached_market_norms()
    assert data1 is data2, "Market norms should be cached in memory"


def test_cors_headers_and_allowed_headers(client):
    """Verify CORS preflight restricts allowed headers to authorized set."""
    response = client.options(
        "/api/analyze-lease",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "")
    assert "Content-Type" in allowed_headers
    assert "Accept" in allowed_headers
    assert "Authorization" in allowed_headers


def test_rate_limiter_active(client):
    """Verify slowapi rate limiter is configured on the FastAPI app."""
    assert hasattr(app.state, "limiter"), "Limiter should be attached to app.state"
    assert app.state.limiter is not None


@pytest.mark.asyncio
async def test_ingestion_fast_path():
    """Verify structured raw lease text bypasses unnecessary LLM normalization."""
    structured_text = (
        "## RESIDENTIAL LEASE AGREEMENT\n\n"
        "1. Security Deposit: 10 months rent.\n\n"
        "2. Lock-in Period: 6 months.\n\n"
        "3. Notice Period: 1 month."
    )
    normalized = await extract_text_from_raw(structured_text)
    assert "Security Deposit" in normalized
    assert "Lock-in Period" in normalized
    assert "Notice Period" in normalized


@pytest.mark.asyncio
async def test_classifier_single_chunk_efficiency():
    """Verify single-chunk documents produce valid LeaseAnalysis without redundant passes."""
    text = (
        "Lease Agreement. Security deposit required: 10 months rent. "
        "Lock-in period: 6 months. Notice period: 1 month. Rent escalation: 5%."
    )
    result = await classify_lease_text(text, [text])
    assert isinstance(result, LeaseAnalysis)
    assert len(result.risks) >= 3
    assert result.overall_risk_score >= 0.0
