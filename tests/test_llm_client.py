"""Tests for LLM client."""

import pytest
from src.llm_client import LLMClient, MockLLM


def test_mock_llm_plan_variants():
    """Test mock LLM returns plan_variants tool call."""
    mock = MockLLM()
    messages = [{"role": "user", "content": "Please plan the content variants"}]
    response = mock.chat(messages, tools=[])

    assert "tool_calls" in response
    assert response["tool_calls"][0]["function"]["name"] == "plan_variants"


def test_mock_llm_draft_content():
    """Test mock LLM returns draft_content tool call."""
    mock = MockLLM()
    messages = [
        {"role": "user", "content": "Draft content for variant v1: eco-friendly focus"}
    ]
    tools = [{"type": "function", "function": {"name": "draft_content"}}]
    response = mock.chat(messages, tools)

    assert "tool_calls" in response
    assert response["tool_calls"][0]["function"]["name"] == "draft_content"


def test_mock_llm_revise_content():
    """Test mock LLM returns revise_content tool call."""
    mock = MockLLM()
    messages = [
        {"role": "user", "content": "Draft content"},
        {"role": "tool", "content": '{"status": "needs_revision", "issues": ["zero"]}'}
    ]
    response = mock.chat(messages, tools=[])

    assert "tool_calls" in response
    assert response["tool_calls"][0]["function"]["name"] == "revise_content"


def test_llm_client_without_api_key():
    """Test LLM client uses mock when no API key provided."""
    client = LLMClient()
    assert client.use_mock
    assert isinstance(client.client, MockLLM)


def test_llm_client_chat_completion_mock():
    """Test chat completion with mock client."""
    client = LLMClient()
    messages = [{"role": "user", "content": "Plan the content variants"}]
    response = client.chat_completion(messages, tools=[])

    assert "role" in response
    assert response["role"] == "assistant"
