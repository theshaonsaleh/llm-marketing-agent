"""LLM client abstraction with mock implementation."""

import json
from typing import Any, Dict, List, Optional
from openai import OpenAI


class MockLLM:
    """Deterministic offline mock LLM for testing and demo without API key."""

    def __init__(self):
        self.call_count = 0

    def chat(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Mock chat completion with tool calling."""
        self.call_count += 1

        last_message = messages[-1]["content"]

        if "plan the content variants" in last_message.lower():
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call_{self.call_count}",
                        "type": "function",
                        "function": {
                            "name": "plan_variants",
                            "arguments": json.dumps(
                                {
                                    "variants": [
                                        {
                                            "id": "v1",
                                            "angle": "eco-friendly focus",
                                            "tone": "inspiring",
                                        },
                                        {
                                            "id": "v2",
                                            "angle": "cost savings",
                                            "tone": "practical",
                                        },
                                        {
                                            "id": "v3",
                                            "angle": "style and design",
                                            "tone": "trendy",
                                        },
                                    ]
                                }
                            ),
                        },
                    }
                ],
            }

        elif "draft_content" in str(tools) and "tool_calls" not in str(messages[-2:]):
            tool_msgs = [m for m in messages if m.get("role") == "tool"]
            num_drafts = len([m for m in tool_msgs if "next_action" in m.get("content", "")])
            
            if num_drafts == 0:
                content = "Save the planet one sip at a time! Our sleek reusable bottles keep drinks cold for 24hrs. Join the zero-waste movement today! 🌍💧"
            elif num_drafts == 1:
                content = "Stop wasting money on disposable bottles! Our premium reusable bottle pays for itself in just 2 weeks. Smart choice for your wallet and the planet. 💰"
            elif num_drafts == 2:
                content = "Hydration meets high fashion! Trending designs that turn heads while keeping drinks at the perfect temp. Your new must-have accessory! ✨"
            else:
                content = "Stay hydrated in style with our premium reusable water bottles! Perfect for daily use."

            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call_{self.call_count}",
                        "type": "function",
                        "function": {
                            "name": "draft_content",
                            "arguments": json.dumps({"content": content}),
                        },
                    }
                ],
            }

        elif "needs_revision" in str(messages[-2:]) or "still_needs_work" in str(messages[-2:]):
            revisions = [m for m in messages if m.get("role") == "tool" and "needs_revision" in m.get("content", "")]
            
            if len(revisions) == 1:
                if "zero" in str(messages[-3:]):
                    content = "Save the planet one sip at a time! Our sleek reusable bottles keep drinks cold for 24hrs. Join the movement today! 🌍💧"
                    changes = "Removed absolute claim 'zero-waste'"
                elif "perfect" in str(messages[-3:]):
                    content = "Hydration meets high fashion! Trending designs that turn heads while keeping drinks at great temp. Your new must-have accessory! ✨"
                    changes = "Changed 'perfect' to 'great' to avoid absolute claim"
                else:
                    content = "Stay hydrated with our reusable bottles! Great for daily use and kind to the planet. 💧"
                    changes = "Simplified language for better readability"
            elif len(revisions) == 2:
                content = "Stop wasting money on bottles! Our reusable bottle saves you cash and helps the planet. Smart choice! 💰"
                changes = "Simplified readability and removed absolute claims"
            else:
                content = "Eco friendly water bottles! Keep drinks cold all day. Sustainable and stylish. 🌍"
                changes = "Further simplified all content"
            
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call_{self.call_count}",
                        "type": "function",
                        "function": {
                            "name": "revise_content",
                            "arguments": json.dumps(
                                {
                                    "revised_content": content,
                                    "changes_made": changes,
                                }
                            ),
                        },
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": "Task completed successfully. All content has been generated and checked.",
        }


class LLMClient:
    """LLM client that uses OpenAI API or falls back to mock."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.model = model
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.use_mock = False
        else:
            self.client = MockLLM()
            self.use_mock = True

    def chat_completion(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Get chat completion with optional tool calling."""
        if self.use_mock:
            return self.client.chat(messages, tools)

        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        result = {"role": message.role, "content": message.content}

        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        return result
