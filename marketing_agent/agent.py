"""
Core marketing content agent implementation.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .llm import LLMInterface
from .validators import ContentValidator


@dataclass
class ContentVariant:
    """Represents a single content variant."""
    channel: str
    content: str
    iteration: int
    validation_results: Optional[Dict] = None


@dataclass
class AgentResult:
    """Final result from the agent run."""
    brief: Dict
    plan: str
    variants: List[ContentVariant]
    final_iteration: int
    success: bool
    summary: str


class MarketingAgent:
    """
    LLM agent that drafts and validates marketing content.
    
    Flow:
    1. Receive brief (product, audience, channel, tone)
    2. Plan content strategy
    3. Draft content variants
    4. Validate against rules
    5. Revise if needed (up to max_iterations)
    6. Return results
    """
    
    def __init__(
        self,
        llm: LLMInterface,
        max_iterations: int = 3,
        channels: Optional[List[str]] = None,
    ):
        """
        Initialize the marketing agent.
        
        Args:
            llm: LLM interface to use
            max_iterations: Maximum revision iterations per variant
            channels: List of channels to generate content for (defaults to brief channel only)
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.channels = channels
        self.validator = ContentValidator()
    
    def run(self, brief: Dict) -> AgentResult:
        """
        Execute the agent workflow.
        
        Args:
            brief: Dictionary with keys:
                - product: Product/topic name
                - audience: Target audience
                - channel: Primary marketing channel
                - tone: Desired tone (e.g., professional, casual, friendly)
                - additional_context: Optional extra context
        
        Returns:
            AgentResult with plan, variants, and validation results
        """
        plan = self._generate_plan(brief)
        
        channels_to_generate = self.channels or [brief["channel"]]
        
        variants = []
        for channel in channels_to_generate:
            variant = self._generate_and_validate_variant(brief, channel)
            variants.append(variant)
        
        all_passed = all(
            v.validation_results and v.validation_results.get("all_passed", False)
            for v in variants
        )
        
        summary = self._generate_summary(variants, all_passed)
        
        return AgentResult(
            brief=brief,
            plan=plan,
            variants=variants,
            final_iteration=max(v.iteration for v in variants),
            success=all_passed,
            summary=summary,
        )
    
    def _generate_plan(self, brief: Dict) -> str:
        """Generate content strategy plan."""
        messages = [
            {
                "role": "system",
                "content": "You are a marketing content strategist. Create a brief plan for content creation based on the brief.",
            },
            {
                "role": "user",
                "content": f"""Create a content strategy plan for this brief:

Product/Topic: {brief.get('product', 'N/A')}
Audience: {brief.get('audience', 'N/A')}
Channel: {brief.get('channel', 'N/A')}
Tone: {brief.get('tone', 'casual')}
Additional Context: {brief.get('additional_context', 'N/A')}

Provide a numbered list of key steps and considerations."""
            }
        ]
        
        return self.llm.generate(messages, temperature=0.5)
    
    def _generate_and_validate_variant(self, brief: Dict, channel: str) -> ContentVariant:
        """Generate and iteratively validate a content variant."""
        current_content = ""
        validation_results = None
        
        for iteration in range(1, self.max_iterations + 1):
            if iteration == 1:
                current_content = self._generate_initial_content(brief, channel)
            else:
                current_content = self._revise_content(
                    brief,
                    channel,
                    current_content,
                    validation_results,
                    iteration
                )
            
            validation_results = self.validator.validate_content(
                current_content,
                channel,
                brief
            )
            
            if validation_results["all_passed"]:
                break
        
        return ContentVariant(
            channel=channel,
            content=current_content,
            iteration=iteration,
            validation_results=validation_results,
        )
    
    def _generate_initial_content(self, brief: Dict, channel: str) -> str:
        """Generate initial content draft."""
        limit_info = ""
        if channel in ContentValidator.CHANNEL_LIMITS:
            limit_info = f"\nMaximum length: {ContentValidator.CHANNEL_LIMITS[channel]} characters"
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an expert marketing copywriter. Write compelling {channel} content.

Rules:
- Be specific and value-focused
- Avoid unverifiable claims like "best", "guaranteed", "#1", "miracle", "proven" without context
- Use clear, simple language (grade 8 reading level or below)
- Include a call-to-action{limit_info}
- Match the specified tone""",
            },
            {
                "role": "user",
                "content": f"""Write {channel} content for:

Product/Topic: {brief.get('product')}
Audience: {brief.get('audience')}
Tone: {brief.get('tone', 'casual')}
Additional Context: {brief.get('additional_context', '')}

Write ONLY the content text, no explanations."""
            }
        ]
        
        return self.llm.generate(messages, temperature=0.7).strip()
    
    def _revise_content(
        self,
        brief: Dict,
        channel: str,
        current_content: str,
        validation_results: Dict,
        iteration: int
    ) -> str:
        """Revise content based on validation feedback."""
        issues = []
        
        checks = validation_results.get("checks", {})
        
        if not checks.get("character_limit", {}).get("passed"):
            char_check = checks["character_limit"]
            issues.append(
                f"- Too long: {char_check['char_count']} chars (limit: {char_check['limit']}). Shorten by {char_check['over_by']} chars."
            )
        
        if not checks.get("readability", {}).get("passed"):
            read_check = checks["readability"]
            issues.append(
                f"- Readability: grade {read_check['grade_level']:.1f} (target: ≤{read_check['target']}). Use simpler words."
            )
        
        if not checks.get("banned_claims", {}).get("passed"):
            violations = checks["banned_claims"].get("violations", [])
            for v in violations:
                issues.append(f"- Remove/revise: '{v['phrase']}' (unverifiable claim)")
        
        if not checks.get("brand_voice", {}).get("passed"):
            suggestions = checks["brand_voice"].get("suggestions", [])
            for s in suggestions:
                issues.append(f"- Brand voice: {s}")
        
        issues_text = "\n".join(issues)
        
        messages = [
            {
                "role": "system",
                "content": f"You are a marketing copywriter. Revise content to fix validation issues while maintaining quality.",
            },
            {
                "role": "user",
                "content": f"""Revise this {channel} content to fix these issues:

Current content:
{current_content}

Issues to fix:
{issues_text}

Brief context:
- Product: {brief.get('product')}
- Audience: {brief.get('audience')}
- Tone: {brief.get('tone')}

Write ONLY the revised content text."""
            }
        ]
        
        return self.llm.generate(messages, temperature=0.6).strip()
    
    def _generate_summary(self, variants: List[ContentVariant], all_passed: bool) -> str:
        """Generate a summary of the agent run."""
        if all_passed:
            return f"Successfully generated {len(variants)} content variant(s). All validation checks passed."
        else:
            failed = sum(
                1 for v in variants
                if not v.validation_results.get("all_passed", False)
            )
            return f"Generated {len(variants)} variant(s). {failed} variant(s) did not pass all checks after {self.max_iterations} iterations."


def format_result_as_json(result: AgentResult) -> str:
    """Format agent result as JSON."""
    data = {
        "brief": result.brief,
        "plan": result.plan,
        "variants": [
            {
                "channel": v.channel,
                "content": v.content,
                "iteration": v.iteration,
                "validation": v.validation_results,
            }
            for v in result.variants
        ],
        "final_iteration": result.final_iteration,
        "success": result.success,
        "summary": result.summary,
    }
    return json.dumps(data, indent=2)


def format_result_as_markdown(result: AgentResult) -> str:
    """Format agent result as Markdown report."""
    lines = ["# Marketing Content Agent Report", ""]
    
    lines.append("## Brief")
    for key, value in result.brief.items():
        lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    lines.append("")
    
    lines.append("## Content Strategy Plan")
    lines.append(result.plan)
    lines.append("")
    
    lines.append("## Generated Content Variants")
    lines.append("")
    
    for i, variant in enumerate(result.variants, 1):
        lines.append(f"### Variant {i}: {variant.channel.replace('_', ' ').title()}")
        lines.append("")
        lines.append("**Content:**")
        lines.append("```")
        lines.append(variant.content)
        lines.append("```")
        lines.append("")
        lines.append(f"**Iterations:** {variant.iteration}")
        lines.append("")
        
        if variant.validation_results:
            lines.append("**Validation Results:**")
            checks = variant.validation_results.get("checks", {})
            
            for check_name, check_result in checks.items():
                status = "✅ PASS" if check_result.get("passed") else "❌ FAIL"
                lines.append(f"- **{check_name.replace('_', ' ').title()}**: {status}")
                lines.append(f"  - {check_result.get('message', 'N/A')}")
                
                if check_name == "banned_claims" and check_result.get("violations"):
                    for v in check_result["violations"]:
                        lines.append(f"    - Issue: '{v['phrase']}'")
                
                if check_name == "brand_voice" and check_result.get("suggestions"):
                    for s in check_result["suggestions"]:
                        lines.append(f"    - {s}")
            
            lines.append("")
    
    lines.append("## Summary")
    status = "✅ Success" if result.success else "⚠️ Partial Success"
    lines.append(f"**Status**: {status}")
    lines.append("")
    lines.append(result.summary)
    lines.append("")
    
    return "\n".join(lines)
