"""Tests for content validation checks."""

import pytest
from src.content_checks import ContentChecker


def test_length_check_pass():
    """Test that content within limits passes."""
    checker = ContentChecker()
    content = "Short tweet about our product!"
    passed, message = checker.check_length(content, "twitter")
    assert passed
    assert "Length OK" in message


def test_length_check_fail():
    """Test that content exceeding limits fails."""
    checker = ContentChecker()
    content = "x" * 300
    passed, message = checker.check_length(content, "twitter")
    assert not passed
    assert "Too long" in message


def test_banned_words_pass():
    """Test content without banned words passes."""
    checker = ContentChecker()
    content = "Our product helps you stay hydrated throughout the day."
    passed, words = checker.check_banned_words(content)
    assert passed
    assert len(words) == 0


def test_banned_words_fail():
    """Test content with banned words fails."""
    checker = ContentChecker()
    content = "This miracle cure is guaranteed to work instantly!"
    passed, words = checker.check_banned_words(content)
    assert not passed
    assert "miracle" in words
    assert "guaranteed" in words


def test_overclaims_pass():
    """Test content without overclaims passes."""
    checker = ContentChecker()
    content = "Our product helps improve your daily hydration routine."
    passed, claims = checker.check_overclaims(content)
    assert passed


def test_overclaims_fail():
    """Test content with overclaims fails."""
    checker = ContentChecker()
    content = "The best product ever! 100% perfect and absolutely amazing!"
    passed, claims = checker.check_overclaims(content)
    assert not passed
    assert len(claims) > 0


def test_readability_short_content():
    """Test readability with very short content."""
    checker = ContentChecker()
    content = "Buy now"
    passed, scores = checker.check_readability(content)
    assert "note" in scores


def test_readability_normal_content():
    """Test readability with normal content."""
    checker = ContentChecker()
    content = "Our water bottle keeps your drinks cold for up to 24 hours. Made from sustainable materials."
    passed, scores = checker.check_readability(content)
    assert "flesch_reading_ease" in scores
    assert "flesch_kincaid_grade" in scores


def test_unverifiable_claims_pass():
    """Test content without unverifiable claims passes."""
    checker = ContentChecker()
    content = "Our product may help improve your experience."
    passed, issues = checker.check_unverifiable_claims(content)
    assert passed


def test_unverifiable_claims_fail():
    """Test content with unverifiable claims fails."""
    checker = ContentChecker()
    content = "The best product guaranteed to work 100% of the time!"
    passed, issues = checker.check_unverifiable_claims(content)
    assert not passed
    assert len(issues) > 0


def test_run_all_checks_clean_content():
    """Test comprehensive check on clean content."""
    checker = ContentChecker()
    content = "Stay hydrated with our eco-friendly water bottle. Keeps drinks cold for hours!"
    results = checker.run_all_checks(content, "twitter")

    assert results["passed"]
    assert "length" in results["checks"]
    assert "banned_words" in results["checks"]
    assert "overclaims" in results["checks"]
    assert "readability" in results["checks"]
    assert "unverifiable_claims" in results["checks"]


def test_run_all_checks_problematic_content():
    """Test comprehensive check on problematic content."""
    checker = ContentChecker()
    content = "x" * 300 + " This is the best miracle product guaranteed to work 100%!"
    results = checker.run_all_checks(content, "twitter")

    assert not results["passed"]
    assert not results["checks"]["length"]["passed"]
