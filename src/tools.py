"""Tool definitions for the marketing agent."""

from typing import Dict, List


def get_tool_definitions() -> List[Dict]:
    """Return tool definitions for the LLM to use."""
    return [
        {
            "type": "function",
            "function": {
                "name": "plan_variants",
                "description": "Plan multiple content variants with different angles and tones",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "variants": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "angle": {"type": "string"},
                                    "tone": {"type": "string"},
                                },
                                "required": ["id", "angle", "tone"],
                            },
                            "description": "List of planned content variants",
                        }
                    },
                    "required": ["variants"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "draft_content",
                "description": "Draft marketing content for a specific variant",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The drafted marketing content",
                        }
                    },
                    "required": ["content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "revise_content",
                "description": "Revise content based on check results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "revised_content": {
                            "type": "string",
                            "description": "The revised marketing content",
                        },
                        "changes_made": {
                            "type": "string",
                            "description": "Description of changes made",
                        },
                    },
                    "required": ["revised_content", "changes_made"],
                },
            },
        },
    ]
