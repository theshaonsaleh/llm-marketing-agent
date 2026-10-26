"""
Tests for content validators.
"""

import pytest
from marketing_agent.validators import ContentValidator


class TestCharacterLimit:
    def test_within_limit(self):
        text = "Short tweet!"
        result = ContentValidator.check_character_limit(text, "twitter")
        assert result["passed"] is True
        assert result["char_count"] == len(text)
        assert result["char_count"] <= result["limit"]
    
    def test_over_limit(self):
        text = "a" * 300
        result = ContentValidator.check_character_limit(text, "twitter")
        assert result["passed"] is False
        assert result["char_count"] == 300
        assert result["limit"] == 280
        assert result["over_by"] == 20
    
    def test_exact_limit(self):
        text = "a" * 280
        result = ContentValidator.check_character_limit(text, "twitter")
        assert result["passed"] is True
        assert result["char_count"] == 280
        assert result["over_by"] == 0
    
    def test_unknown_channel(self):
        text = "Some content"
        result = ContentValidator.check_character_limit(text, "unknown_channel")
        assert result["passed"] is True
        assert "No character limit" in result["message"]


class TestReadability:
    def test_simple_text(self):
        text = "The cat sat on the mat. It was a nice day."
        result = ContentValidator.check_readability(text, target_grade_level=8)
        assert result["passed"] is True
        assert result["grade_level"] <= 8
    
    def test_complex_text(self):
        text = "The implementation of comprehensive methodological frameworks necessitates substantial deliberation."
        result = ContentValidator.check_readability(text, target_grade_level=8)
        assert result["grade_level"] > 8
        assert result["passed"] is False
    
    def test_short_text(self):
        text = "Hi there"
        result = ContentValidator.check_readability(text)
        assert result["passed"] is True
        assert "too short" in result["message"].lower()


class TestBannedClaims:
    def test_no_violations(self):
        text = "Great coffee for your morning routine. Try it today!"
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is True
        assert len(result["violations"]) == 0
    
    def test_best_claim(self):
        text = "The best coffee in the world!"
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is False
        assert len(result["violations"]) == 1
        assert "best" in result["violations"][0]["phrase"].lower()
    
    def test_guaranteed_claim(self):
        text = "We guarantee results overnight!"
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is False
        violations = [v["phrase"].lower() for v in result["violations"]]
        assert any("guarantee" in v for v in violations)
    
    def test_multiple_violations(self):
        text = "The best product with guaranteed miracle results!"
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is False
        assert len(result["violations"]) >= 2
    
    def test_allowed_exceptions(self):
        text = "The best way to learn. Free trial available. Money-back guarantee policy."
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is True
    
    def test_proven_without_context(self):
        text = "Our proven solution works instantly!"
        result = ContentValidator.check_banned_claims(text)
        assert result["passed"] is False


class TestBrandVoice:
    def test_professional_tone(self):
        brief = {"tone": "professional", "channel": "linkedin_post"}
        text = "Enhance your professional capabilities with our innovative solution. Learn more today."
        result = ContentValidator.check_brand_voice(text, brief)
        assert result["passed"] is True
    
    def test_professional_with_informal_language(self):
        brief = {"tone": "professional", "channel": "linkedin_post"}
        text = "OMG this product is amazing lol!"
        result = ContentValidator.check_brand_voice(text, brief)
        assert result["passed"] is False
        assert any("informal" in s.lower() for s in result["suggestions"])
    
    def test_missing_cta(self):
        brief = {"tone": "casual", "channel": "twitter"}
        text = "We have a new product available."
        result = ContentValidator.check_brand_voice(text, brief)
        assert result["passed"] is False
        assert any("action" in s.lower() for s in result["suggestions"])
    
    def test_with_cta(self):
        brief = {"tone": "casual", "channel": "twitter"}
        text = "Check out our new coffee! Try it today and discover the difference."
        result = ContentValidator.check_brand_voice(text, brief)
        assert result["passed"] is True


class TestValidateContent:
    def test_all_checks_pass(self):
        brief = {
            "product": "Coffee",
            "audience": "coffee lovers",
            "channel": "twitter",
            "tone": "casual"
        }
        text = "Great coffee for your morning! Try it now ☕"
        result = ContentValidator.validate_content(text, "twitter", brief)
        assert result["all_passed"] is True
        assert "character_limit" in result["checks"]
        assert "readability" in result["checks"]
        assert "banned_claims" in result["checks"]
        assert "brand_voice" in result["checks"]
    
    def test_character_limit_fails(self):
        brief = {
            "product": "Coffee",
            "audience": "coffee lovers",
            "channel": "twitter",
            "tone": "casual"
        }
        text = "a" * 300 + " Try it now!"
        result = ContentValidator.validate_content(text, "twitter", brief)
        assert result["all_passed"] is False
        assert result["checks"]["character_limit"]["passed"] is False
    
    def test_banned_claims_fail(self):
        brief = {
            "product": "Coffee",
            "audience": "coffee lovers",
            "channel": "twitter",
            "tone": "casual"
        }
        text = "The best coffee guaranteed to give you miracle results!"
        result = ContentValidator.validate_content(text, "twitter", brief)
        assert result["all_passed"] is False
        assert result["checks"]["banned_claims"]["passed"] is False
