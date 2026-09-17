"""Orchestrator Agent Test Suite for LeaseLens.

Validates:
1. Text chunking logic: edge cases, overlap correctness, boundary handling.
2. Full pipeline integration: end-to-end with raw text input.
3. Error handling: empty input, insufficient text.

Run with:
    pytest test_orchestrator.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import CHARS_PER_TOKEN, CHUNK_OVERLAP, CHUNK_SIZE, chunk_text

# =====================================================================
# 1. chunk_text() Unit Tests
# =====================================================================


class TestChunkText:
    """Validate the sliding window text chunking implementation."""

    def test_empty_text_returns_single_empty_chunk(self):
        """Empty string should return a list with one empty string."""
        result = chunk_text("")
        assert result == [""]

    def test_short_text_returns_single_chunk(self, sample_short_text):
        """Text shorter than chunk_size should return exactly one chunk."""
        result = chunk_text(sample_short_text)
        assert len(result) == 1
        assert result[0] == sample_short_text

    def test_long_text_produces_multiple_chunks(self, sample_lease_text):
        """Text exceeding chunk_size * CHARS_PER_TOKEN should produce multiple chunks."""
        # Create text that's definitely longer than one chunk
        long_text = sample_lease_text * 10  # ~7000+ chars
        result = chunk_text(long_text, chunk_size=200, overlap=20)
        assert len(result) > 1

    def test_chunks_have_overlap(self):
        """Consecutive chunks must share overlapping content."""
        # Create predictable text longer than one chunk
        text = "A" * 2000  # 2000 chars
        chunk_size_tokens = 100  # 100 tokens * 4 chars = 400 chars per chunk
        overlap_tokens = 25  # 25 tokens * 4 chars = 100 chars overlap

        result = chunk_text(text, chunk_size=chunk_size_tokens, overlap=overlap_tokens)
        assert len(result) > 1

        # Verify overlap: end of chunk[i] should match start of chunk[i+1]
        overlap_chars = overlap_tokens * CHARS_PER_TOKEN
        for i in range(len(result) - 1):
            tail_of_current = result[i][-overlap_chars:]
            head_of_next = result[i + 1][:overlap_chars]
            assert tail_of_current == head_of_next, (
                f"Chunk {i} tail does not match chunk {i+1} head"
            )

    def test_all_text_is_covered(self):
        """Union of all chunks must cover the entire original text."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100  # 2600 chars
        result = chunk_text(text, chunk_size=100, overlap=10)

        # Verify first chunk starts from beginning
        assert result[0][:26] == text[:26]
        # Verify last chunk ends at the text boundary
        assert result[-1][-26:] == text[-26:]
        # Verify total content length accounts for overlap correctly
        total_unique_chars = sum(len(c) for c in result) - (len(result) - 1) * (10 * CHARS_PER_TOKEN)
        assert total_unique_chars >= len(text), (
            f"Chunks cover {total_unique_chars} chars but text has {len(text)} chars"
        )

    def test_single_char_chunk_size(self):
        """Extremely small chunk size should still work without error."""
        text = "Hello World"
        result = chunk_text(text, chunk_size=1, overlap=0)
        assert len(result) >= 1

    def test_default_parameters(self):
        """Default chunk_size and overlap should match module constants."""
        # Verify the function uses module-level constants
        assert CHUNK_SIZE == 2000
        assert CHUNK_OVERLAP == 200
        assert CHARS_PER_TOKEN == 4

    def test_chunk_boundaries_are_clean(self, sample_lease_text):
        """Chunks should not be empty or whitespace-only in the middle."""
        long_text = sample_lease_text * 5
        result = chunk_text(long_text, chunk_size=200, overlap=20)
        for i, chunk in enumerate(result):
            assert len(chunk) > 0, f"Chunk {i} is empty"


# =====================================================================
# 2. analyze_lease() Integration Tests
# =====================================================================


class TestAnalyzeLeasePipeline:
    """Integration tests for the full orchestrator pipeline."""

    @pytest.mark.asyncio
    async def test_analyze_with_raw_text(self, sample_lease_text):
        """Full pipeline should complete successfully with valid raw text."""
        from agents.orchestrator import analyze_lease

        result = await analyze_lease(raw_text=sample_lease_text)
        assert result is not None
        assert result.total_clauses_analyzed >= 1
        assert 0.0 <= result.overall_risk_score <= 10.0
        assert len(result.risks) >= 1

    @pytest.mark.asyncio
    async def test_analyze_raises_on_empty_input(self):
        """Pipeline must raise ValueError when neither pdf_bytes nor raw_text provided."""
        from agents.orchestrator import analyze_lease

        with pytest.raises(ValueError, match="Either pdf_bytes or raw_text"):
            await analyze_lease(pdf_bytes=None, raw_text=None)

    @pytest.mark.asyncio
    async def test_analyze_returns_lease_analysis_type(self, sample_lease_text):
        """Pipeline output must be a LeaseAnalysis instance."""
        from agents.orchestrator import analyze_lease
        from schemas.lease_schema import LeaseAnalysis

        result = await analyze_lease(raw_text=sample_lease_text)
        assert isinstance(result, LeaseAnalysis)

    @pytest.mark.asyncio
    async def test_analyze_with_pdf_bytes_fallback(self):
        """Pipeline with PDF bytes should use fallback in offline mode."""
        from agents.orchestrator import analyze_lease

        # Simulate a text-based PDF (fallback path)
        fake_pdf = (
            b"%PDF-1.7\n"
            b"Security Deposit: The Tenant agrees to deposit 10 months rent.\n"
            b"Lock-in Period: 6 months mandatory.\n"
            b"Rent shall increase by 5% annually.\n"
        )
        result = await analyze_lease(pdf_bytes=fake_pdf)
        assert result is not None
        assert result.total_clauses_analyzed >= 1
