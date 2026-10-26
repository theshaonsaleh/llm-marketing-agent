"""Content validation checks for marketing copy."""

import re
from typing import Dict, List, Tuple
import textstat


class ContentChecker:
    """Validates marketing content against various rules and best practices."""

    CHANNEL_LIMITS = {
        "twitter": 280,
        "instagram": 2200,
        "facebook": 63206,
        "linkedin": 3000,
        "tiktok": 2200,
        "ad_copy": 150,
    }

    BANNED_WORDS = [
        "guaranteed",
        "miracle",
        "cure",
        "free money",
        "get rich quick",
        "lose weight fast",
        "click here",
        "act now",
        "limited time only",
        "risk-free",
        "100% effective",
        "scientifically proven",
        "doctor recommended",
        "no side effects",
    ]

    OVERCLAIM_PATTERNS = [
        r"\b(best|#1|number one|top|leading|ultimate|perfect)\b",
        r"\b(always|never|everyone|nobody|guaranteed|certain)\b",
        r"\b(zero|100%|completely|totally|absolutely|instantly)\b",
        r"\b(revolutionary|breakthrough|amazing|incredible)\b",
    ]

    def check_length(self, content: str, channel: str) -> Tuple[bool, str]:
        """Check if content fits channel length limits."""
        limit = self.CHANNEL_LIMITS.get(channel.lower())
        if not limit:
            return True, f"Unknown channel: {channel}"

        length = len(content)
        if length <= limit:
            return True, f"Length OK: {length}/{limit} characters"
        return False, f"Too long: {length}/{limit} characters (exceeds by {length - limit})"

    def check_banned_words(self, content: str) -> Tuple[bool, List[str]]:
        """Check for banned or problematic words."""
        content_lower = content.lower()
        found = [word for word in self.BANNED_WORDS if word in content_lower]

        if not found:
            return True, []
        return False, found

    def check_overclaims(self, content: str) -> Tuple[bool, List[str]]:
        """Check for overclaiming language."""
        found = []
        content_lower = content.lower()

        for pattern in self.OVERCLAIM_PATTERNS:
            matches = re.finditer(pattern, content_lower, re.IGNORECASE)
            for match in matches:
                found.append(match.group(0))

        if not found:
            return True, []
        return False, list(set(found))

    def check_readability(self, content: str) -> Tuple[bool, Dict[str, float]]:
        """Check readability scores."""
        if len(content.split()) < 3:
            return True, {"note": "Content too short for meaningful readability score"}

        flesch_reading_ease = textstat.flesch_reading_ease(content)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(content)

        scores = {
            "flesch_reading_ease": round(flesch_reading_ease, 1),
            "flesch_kincaid_grade": round(flesch_kincaid_grade, 1),
        }

        passed = flesch_reading_ease >= 50 and flesch_kincaid_grade <= 10

        return passed, scores

    def check_unverifiable_claims(self, content: str) -> Tuple[bool, List[str]]:
        """Check for unverifiable advertising claims."""
        issues = []
        content_lower = content.lower()

        unverifiable_patterns = [
            (r"\bbest\b", "Claim: 'best' - requires evidence/context"),
            (r"\bguaranteed\b", "Claim: 'guaranteed' - must be substantiated"),
            (
                r"\b(always|never) (works|fails|breaks)\b",
                "Absolute claim without qualification",
            ),
            (
                r"\b100%\b",
                "Absolute percentage claim - rarely verifiable",
            ),
            (
                r"\beveryone (loves|uses|needs)\b",
                "Universal claim without evidence",
            ),
        ]

        for pattern, message in unverifiable_patterns:
            if re.search(pattern, content_lower):
                issues.append(message)

        if not issues:
            return True, []
        return False, issues

    def run_all_checks(self, content: str, channel: str) -> Dict:
        """Run all checks and return comprehensive results."""
        results = {
            "content": content,
            "channel": channel,
            "passed": True,
            "checks": {},
        }

        length_pass, length_msg = self.check_length(content, channel)
        results["checks"]["length"] = {
            "passed": length_pass,
            "message": length_msg,
        }
        if not length_pass:
            results["passed"] = False

        banned_pass, banned_words = self.check_banned_words(content)
        results["checks"]["banned_words"] = {
            "passed": banned_pass,
            "found": banned_words,
        }
        if not banned_pass:
            results["passed"] = False

        overclaim_pass, overclaims = self.check_overclaims(content)
        results["checks"]["overclaims"] = {
            "passed": overclaim_pass,
            "found": overclaims,
        }
        if not overclaim_pass:
            results["passed"] = False

        readability_pass, readability_scores = self.check_readability(content)
        results["checks"]["readability"] = {
            "passed": readability_pass,
            "scores": readability_scores,
        }
        if not readability_pass:
            results["passed"] = False

        claims_pass, claim_issues = self.check_unverifiable_claims(content)
        results["checks"]["unverifiable_claims"] = {
            "passed": claims_pass,
            "issues": claim_issues,
        }
        if not claims_pass:
            results["passed"] = False

        return results
