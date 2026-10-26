"""
Content validation tools for marketing materials.
"""

import re
from typing import Dict, List, Tuple
import textstat


class ContentValidator:
    """Validates marketing content against various rules and standards."""
    
    CHANNEL_LIMITS = {
        "twitter": 280,
        "facebook_post": 500,
        "instagram_caption": 2200,
        "linkedin_post": 3000,
        "email_subject": 60,
        "ad_headline": 30,
        "meta_description": 160,
    }
    
    BANNED_CLAIMS = [
        r"\b(best|#1|top|leading)\b(?!\s+(way|practice|tip|approach|method))",
        r"\bguarantee[d]?\b(?!\s+(money.back|refund|policy))",
        r"\b(miracle|magic|instant|overnight)\s+(result|solution|cure|fix)",
        r"\bproven\b(?!\s+(track\s+record|methodology|by\s+research))",
        r"\b(always|never|100%|forever)\b(?!\s+(free|satisfaction))",
        r"\bfree\b(?!\s+(trial|shipping|sample|consultation|tier|version))",
    ]
    
    BRAND_VOICE_CHECKLIST = [
        "clear_value_proposition",
        "audience_appropriate_tone",
        "action_oriented",
        "brand_consistent",
    ]

    @staticmethod
    def check_character_limit(text: str, channel: str) -> Dict:
        """Check if text meets character limit for the given channel."""
        limit = ContentValidator.CHANNEL_LIMITS.get(channel)
        if limit is None:
            return {
                "passed": True,
                "message": f"No character limit defined for channel: {channel}",
                "char_count": len(text),
            }
        
        char_count = len(text)
        passed = char_count <= limit
        
        return {
            "passed": passed,
            "message": f"Character count: {char_count}/{limit}",
            "char_count": char_count,
            "limit": limit,
            "over_by": max(0, char_count - limit),
        }

    @staticmethod
    def check_readability(text: str, target_grade_level: int = 8) -> Dict:
        """
        Check readability using Flesch-Kincaid Grade Level.
        Target: Grade 8 or below for general marketing content.
        """
        if len(text.split()) < 3:
            return {
                "passed": True,
                "message": "Text too short for readability analysis",
                "grade_level": 0,
            }
        
        grade_level = textstat.flesch_kincaid_grade(text)
        passed = grade_level <= target_grade_level
        
        return {
            "passed": passed,
            "message": f"Reading grade level: {grade_level:.1f} (target: ≤{target_grade_level})",
            "grade_level": grade_level,
            "target": target_grade_level,
        }

    @staticmethod
    def check_banned_claims(text: str) -> Dict:
        """Check for potentially misleading or unverifiable claims."""
        violations = []
        
        for pattern in ContentValidator.BANNED_CLAIMS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append({
                    "phrase": match.group(),
                    "position": match.span(),
                    "rule": "Unverifiable or potentially misleading claim",
                })
        
        passed = len(violations) == 0
        
        return {
            "passed": passed,
            "message": f"Found {len(violations)} potential issue(s)" if violations else "No banned claims detected",
            "violations": violations,
        }

    @staticmethod
    def check_brand_voice(text: str, brief: Dict) -> Dict:
        """
        Check brand voice alignment.
        This is a simplified heuristic-based check.
        """
        issues = []
        text_lower = text.lower()
        
        if brief.get("tone") == "professional" and any(word in text_lower for word in ["lol", "omg", "haha", "🔥"]):
            issues.append("Informal language detected in professional tone content")
        
        if brief.get("tone") == "casual" and len([w for w in text.split() if len(w) > 12]) > len(text.split()) * 0.2:
            issues.append("Complex vocabulary may not suit casual tone")
        
        if "!" not in text and brief.get("channel") in ["twitter", "instagram_caption"]:
            issues.append("Consider adding energy/excitement for social media")
        
        if not any(action in text_lower for action in ["try", "get", "discover", "learn", "join", "start", "shop", "see", "explore", "find"]):
            issues.append("Missing clear call-to-action")
        
        passed = len(issues) == 0
        
        return {
            "passed": passed,
            "message": f"Brand voice check: {len(issues)} suggestion(s)" if issues else "Brand voice alignment looks good",
            "suggestions": issues,
            "checklist": ContentValidator.BRAND_VOICE_CHECKLIST,
        }

    @staticmethod
    def validate_content(text: str, channel: str, brief: Dict) -> Dict:
        """Run all validation checks on the content."""
        results = {
            "character_limit": ContentValidator.check_character_limit(text, channel),
            "readability": ContentValidator.check_readability(text),
            "banned_claims": ContentValidator.check_banned_claims(text),
            "brand_voice": ContentValidator.check_brand_voice(text, brief),
        }
        
        all_passed = all(r["passed"] for r in results.values())
        
        return {
            "all_passed": all_passed,
            "checks": results,
        }
