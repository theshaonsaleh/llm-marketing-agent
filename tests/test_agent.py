"""Tests for the marketing agent."""

import pytest
from src.agent import MarketingAgent
from src.llm_client import LLMClient


@pytest.fixture
def agent():
    """Create agent with mock LLM."""
    llm = LLMClient()
    return MarketingAgent(llm)


@pytest.fixture
def sample_brief():
    """Sample marketing brief."""
    return {
        "product": "EcoFlow Reusable Water Bottle - fictional sustainable water bottle",
        "audience": "Environmentally conscious millennials",
        "channel": "instagram",
        "tone": "inspiring",
    }


def test_agent_initialization(agent):
    """Test agent initializes correctly."""
    assert agent.llm is not None
    assert agent.checker is not None
    assert len(agent.tools) == 3


def test_agent_creates_brief_prompt(agent, sample_brief):
    """Test agent creates system prompt from brief."""
    prompt = agent.create_brief_prompt(sample_brief)
    assert "EcoFlow" in prompt
    assert "instagram" in prompt
    assert "inspiring" in prompt


def test_agent_run_completes(agent, sample_brief):
    """Test agent completes execution."""
    results = agent.run(sample_brief, verbose=False)

    assert "brief" in results
    assert "variants" in results
    assert "drafts" in results
    assert "revisions" in results
    assert "iterations" in results
    assert results["iterations"] > 0


def test_agent_generates_variants(agent, sample_brief):
    """Test agent plans multiple variants."""
    results = agent.run(sample_brief, verbose=False)

    assert len(results["variants"]) >= 2
    for variant in results["variants"]:
        assert "id" in variant
        assert "angle" in variant
        assert "tone" in variant


def test_agent_generates_drafts(agent, sample_brief):
    """Test agent generates draft content."""
    results = agent.run(sample_brief, verbose=False)

    assert len(results["drafts"]) > 0
    for variant_id, draft_data in results["drafts"].items():
        assert "content" in draft_data
        assert "check_results" in draft_data
        assert len(draft_data["content"]) > 0


def test_agent_runs_checks(agent, sample_brief):
    """Test agent runs content checks."""
    results = agent.run(sample_brief, verbose=False)

    for variant_id, draft_data in results["drafts"].items():
        check_results = draft_data["check_results"]
        assert "passed" in check_results
        assert "checks" in check_results
        assert "length" in check_results["checks"]
        assert "banned_words" in check_results["checks"]


def test_agent_respects_max_iterations(agent, sample_brief):
    """Test agent stops at max iterations."""
    agent.max_iterations = 5
    results = agent.run(sample_brief, verbose=False)

    assert results["iterations"] <= 5


def test_agent_with_different_channel(agent):
    """Test agent works with different channels."""
    brief = {
        "product": "Test product",
        "audience": "Test audience",
        "channel": "twitter",
        "tone": "casual",
    }
    results = agent.run(brief, verbose=False)

    assert len(results["drafts"]) > 0
