"""Automated UPL Guardrail Tests for LeaseLens.

Verifies that:
1. Forbidden legal terms are caught and sanitized by the regex layer.
2. Direct requests for legal advice are blocked.
3. Clean informational text passes through unchanged.
4. All educational notes contain the standard disclaimer suffix.

Run with pytest: pytest test_upl_guardrail.py -v
Run with unittest: python3 test_upl_guardrail.py
"""

import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path so agents can be imported
sys.path.insert(0, str(Path(__file__).parent))

from agents.upl_guardrail import (
    check_for_violations,
    _rule_based_sanitize,
    _ensure_disclaimer_suffix,
    FORBIDDEN_PATTERN,
)


class TestForbiddenTermDetection(unittest.TestCase):
    """Verify that check_for_violations catches all prohibited terms."""

    def test_detects_forbidden_terms(self):
        cases = [
            ("This clause is illegal and should be voided.", "illegal"),
            ("This is void and unenforceable.", "void"),
            ("You should sue your landlord.", "sue"),
            ("I recommend rejecting this lease.", "recommend"),
            ("You should sign this lease immediately.", "should sign"),
            ("You should reject this clause.", "should reject"),
            ("You must accept these terms.", "must accept"),
            ("This violates your legal right to quiet enjoyment.", "legal right"),
            ("You should take legal action against the landlord.", "take legal action"),
            ("File a complaint with the housing authority.", "File a complaint"),
            ("This is an unlawful clause.", "unlawful"),
            ("This is a predatory lease term.", "predatory"),
        ]
        for text, expected_match in cases:
            with self.subTest(text=text):
                result = check_for_violations(text)
                self.assertIsNotNone(result, f"Failed to detect '{expected_match}' in: {text}")
                self.assertEqual(result.lower(), expected_match.lower())

    def test_clean_text_passes(self):
        clean_texts = [
            "This clause deviates from standard market practice.",
            "Review by a qualified legal professional is advised.",
            "The security deposit is 10 months, which is standard for Bangalore.",
            "This lock-in period of 6 months exceeds the 1-month market standard.",
            "No significant deviations found in this clause.",
        ]
        for text in clean_texts:
            with self.subTest(text=text):
                result = check_for_violations(text)
                self.assertIsNone(result, f"False positive on clean text: {text}")


class TestRegexSanitization(unittest.TestCase):
    """Verify that _rule_based_sanitize replaces forbidden terms correctly."""

    def test_replaces_illegal(self):
        result = _rule_based_sanitize("This clause is illegal.")
        self.assertNotIn("illegal", result.lower())
        self.assertIn("deviates from standard market practice", result)

    def test_replaces_void(self):
        result = _rule_based_sanitize("This clause is void.")
        self.assertNotIn("void", result.lower())
        self.assertIn("may warrant further review", result)

    def test_replaces_sue(self):
        result = _rule_based_sanitize("You should sue the landlord.")
        self.assertNotIn("sue", result.lower())
        self.assertIn("seek consultation with a qualified legal professional", result)

    def test_replaces_recommend(self):
        result = _rule_based_sanitize("I recommend you negotiate.")
        self.assertNotIn("recommend", result.lower())
        self.assertIn("note that", result)

    def test_replaces_should_sign(self):
        result = _rule_based_sanitize("You should sign this lease.")
        self.assertNotIn("should sign", result.lower())
        self.assertIn("[removed", result)

    def test_replaces_predatory(self):
        result = _rule_based_sanitize("This is a predatory clause.")
        self.assertNotIn("predatory", result.lower())
        self.assertIn("significantly above market standard", result)

    def test_multiple_violations_in_one_text(self):
        text = "This illegal clause is void and you should sue."
        result = _rule_based_sanitize(text)
        self.assertIsNone(
            check_for_violations(result),
            f"Sanitized text still contains violations: {result}"
        )

    def test_preserves_clean_text(self):
        clean = "This clause deviates from standard market parameters."
        result = _rule_based_sanitize(clean)
        self.assertEqual(result, clean)


class TestDisclaimerSuffix(unittest.TestCase):
    """Verify that _ensure_disclaimer_suffix appends the required advisory."""

    EXPECTED_SUFFIX = (
        "Review by a qualified legal professional is advised prior to execution."
    )

    def test_adds_suffix_when_missing(self):
        note = "This clause deviates significantly from market norms."
        result = _ensure_disclaimer_suffix(note)
        self.assertIn(self.EXPECTED_SUFFIX, result)

    def test_does_not_duplicate_suffix(self):
        note = f"Deviation detected. {self.EXPECTED_SUFFIX}"
        result = _ensure_disclaimer_suffix(note)
        self.assertEqual(result.count(self.EXPECTED_SUFFIX), 1)

    def test_handles_empty_string(self):
        result = _ensure_disclaimer_suffix("")
        self.assertIn(self.EXPECTED_SUFFIX, result)


class TestAdversarialInputs(unittest.TestCase):
    """Simulate adversarial user prompts that attempt to extract legal advice."""

    ADVERSARIAL_PROMPTS = [
        "Should I sue my landlord for this clause?",
        "Is this clause illegal under Indian law?",
        "Tell me my legal rights as a tenant.",
        "Can I take legal action against the landlord?",
        "Should I sign this lease or reject it?",
        "File a case against the builder.",
        "This is fraudulent — what should I do?",
        "Is this clause unenforceable in court?",
    ]

    def test_adversarial_prompts_detected(self):
        for prompt in self.ADVERSARIAL_PROMPTS:
            with self.subTest(prompt=prompt):
                result = check_for_violations(prompt)
                self.assertIsNotNone(result, f"Adversarial prompt slipped through: {prompt}")

    def test_adversarial_prompts_sanitized(self):
        for prompt in self.ADVERSARIAL_PROMPTS:
            with self.subTest(prompt=prompt):
                sanitized = _rule_based_sanitize(prompt)
                remaining = check_for_violations(sanitized)
                self.assertIsNone(
                    remaining,
                    f"Sanitization incomplete for: {prompt}\nRemaining: {remaining}\nSanitized: {sanitized}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
