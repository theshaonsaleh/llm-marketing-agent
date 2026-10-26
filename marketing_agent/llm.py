"""
LLM interface supporting OpenAI and deterministic mock mode.
"""

import os
import json
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """Abstract base class for LLM implementations."""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Generate a response from the LLM."""
        pass


class OpenAILLM(LLMInterface):
    """OpenAI API implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.model = model
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Generate a response using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content


class MockLLM(LLMInterface):
    """
    Deterministic mock LLM for testing and demos without API keys.
    Returns structured, realistic marketing content based on the brief.
    """
    
    MOCK_TEMPLATES = {
        "twitter": [
            "☕ Start your day right with {product}! {value_prop} Perfect for {audience}. {cta} ✨",
            "Transform your {context} with {product}. {value_prop} Try it today! {emoji}",
        ],
        "facebook_post": [
            "Introducing {product}! 🎉\n\n{value_prop}\n\nPerfect for {audience} who want to {benefit}.\n\n{cta} Learn more at our website!",
            "Looking for {solution}? Meet {product}!\n\n{value_prop}\n\nIdeal for {audience}. {cta}",
        ],
        "instagram_caption": [
            "{emoji} {product} is here!\n\n{value_prop}\n\n✨ Perfect for {audience}\n💪 {benefit}\n🎯 {feature}\n\n{cta}\n\n{hashtags}",
        ],
        "linkedin_post": [
            "{product}: {value_prop}\n\nDesigned for {audience}, our solution helps you {benefit}.\n\nKey features:\n• {feature}\n• {feature2}\n• {feature3}\n\n{cta}",
        ],
        "email_subject": [
            "{product}: {hook} for {audience}",
            "Get started with {product} today",
            "Discover how {product} helps {audience}",
        ],
        "ad_headline": [
            "{product} for {audience}",
            "{value_prop} - Try {product}",
            "Get {benefit} with {product}",
        ],
    }
    
    MOCK_ITERATIONS = {
        1: "iteration_1",
        2: "iteration_2_improved",
        3: "iteration_3_final",
    }
    
    def __init__(self):
        self.call_count = 0
    
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Generate deterministic mock content based on messages."""
        self.call_count += 1
        
        last_message = messages[-1]["content"]
        
        brief_info = self._extract_brief_info(last_message)
        
        if "plan" in last_message.lower() and "strategy" in last_message.lower():
            return self._generate_plan(brief_info)
        
        if any(word in last_message.lower() for word in ["revise", "improve", "fix", "update"]):
            return self._generate_revision(brief_info, self.call_count)
        
        return self._generate_content(brief_info, self.call_count)
    
    def _extract_brief_info(self, message: str) -> Dict:
        """Extract key information from the brief in the message."""
        info = {
            "product": "Product",
            "audience": "customers",
            "channel": "twitter",
            "tone": "casual",
            "value_prop": "Amazing value",
            "benefit": "save time",
            "feature": "Easy to use",
            "feature2": "Fast results",
            "feature3": "Great support",
            "solution": "better results",
            "context": "daily routine",
            "hook": "Something special",
            "cta": "Try it now!",
            "emoji": "🚀",
            "hashtags": "#Marketing #Growth",
        }
        
        message_lower = message.lower()
        
        if "twitter" in message_lower:
            info["channel"] = "twitter"
        elif "facebook" in message_lower:
            info["channel"] = "facebook_post"
        elif "instagram" in message_lower:
            info["channel"] = "instagram_caption"
        elif "linkedin" in message_lower:
            info["channel"] = "linkedin_post"
        elif "email" in message_lower and "subject" in message_lower:
            info["channel"] = "email_subject"
        elif "ad" in message_lower and "headline" in message_lower:
            info["channel"] = "ad_headline"
        
        for line in message.split("\n"):
            if "product:" in line.lower():
                info["product"] = line.split(":", 1)[1].strip()
            elif "audience:" in line.lower():
                info["audience"] = line.split(":", 1)[1].strip()
            elif "tone:" in line.lower():
                info["tone"] = line.split(":", 1)[1].strip()
        
        return info
    
    def _generate_plan(self, brief_info: Dict) -> str:
        """Generate a mock content strategy plan."""
        return f"""Content Strategy Plan:

1. Primary Message: Highlight {brief_info['product']} value for {brief_info['audience']}
2. Key Channels: Focus on {brief_info['channel']} with {brief_info['tone']} tone
3. Variants to Create:
   - Main promotional post
   - Engagement-focused variant
   - Call-to-action variant
4. Validation Approach:
   - Check character limits
   - Ensure readability
   - Avoid unverifiable claims
   - Maintain brand voice consistency
5. Success Criteria: All validation checks pass"""
    
    def _generate_content(self, brief_info: Dict, iteration: int) -> str:
        """Generate mock marketing content."""
        channel = brief_info["channel"]
        templates = self.MOCK_TEMPLATES.get(channel, self.MOCK_TEMPLATES["twitter"])
        
        template = templates[min(iteration - 1, len(templates) - 1)]
        
        content = template.format(**brief_info)
        
        if iteration > 1:
            if channel == "twitter" and len(content) > 280:
                content = content[:270] + "..."
            
            content = content.replace("guaranteed", "designed to help")
            content = content.replace("best", "great")
            content = content.replace("miracle", "effective")
        
        return content
    
    def _generate_revision(self, brief_info: Dict, iteration: int) -> str:
        """Generate a revised version of content."""
        revisions = {
            1: "I'll make it more concise and remove any potentially problematic claims.",
            2: "I'll improve readability and strengthen the call-to-action.",
            3: "Final polish: ensuring all guidelines are met.",
        }
        
        revision_note = revisions.get(min(iteration, 3), "Applying improvements.")
        
        content = self._generate_content(brief_info, iteration + 1)
        
        return f"{revision_note}\n\n{content}"


def create_llm(mock: bool = False, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> LLMInterface:
    """
    Factory function to create an LLM instance.
    
    Args:
        mock: If True, use MockLLM. If False, use OpenAI.
        api_key: OpenAI API key (if not using mock)
        model: OpenAI model name
    
    Returns:
        LLMInterface instance
    """
    if mock:
        return MockLLM()
    else:
        return OpenAILLM(api_key=api_key, model=model)
