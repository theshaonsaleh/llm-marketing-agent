"""
Tests for the marketing agent.
"""

import pytest
from marketing_agent.agent import MarketingAgent, ContentVariant, format_result_as_json, format_result_as_markdown
from marketing_agent.llm import MockLLM


@pytest.fixture
def mock_llm():
    return MockLLM()


@pytest.fixture
def sample_brief():
    return {
        "product": "TestProduct",
        "audience": "test users",
        "channel": "twitter",
        "tone": "casual",
        "additional_context": "A test product"
    }


class TestMarketingAgent:
    def test_initialization(self, mock_llm):
        agent = MarketingAgent(mock_llm, max_iterations=3)
        assert agent.llm == mock_llm
        assert agent.max_iterations == 3
    
    def test_run_returns_result(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=2)
        result = agent.run(sample_brief)
        
        assert result.brief == sample_brief
        assert result.plan is not None
        assert len(result.plan) > 0
        assert len(result.variants) == 1
        assert result.variants[0].channel == "twitter"
        assert isinstance(result.success, bool)
        assert result.summary is not None
    
    def test_run_with_multiple_channels(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=2, channels=["twitter", "facebook_post"])
        result = agent.run(sample_brief)
        
        assert len(result.variants) == 2
        channels = [v.channel for v in result.variants]
        assert "twitter" in channels
        assert "facebook_post" in channels
    
    def test_variant_has_validation_results(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=2)
        result = agent.run(sample_brief)
        
        variant = result.variants[0]
        assert variant.validation_results is not None
        assert "all_passed" in variant.validation_results
        assert "checks" in variant.validation_results
    
    def test_max_iterations_respected(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=2)
        result = agent.run(sample_brief)
        
        for variant in result.variants:
            assert variant.iteration <= 2
    
    def test_successful_validation_stops_early(self, mock_llm):
        brief = {
            "product": "Coffee",
            "audience": "workers",
            "channel": "twitter",
            "tone": "casual",
        }
        agent = MarketingAgent(mock_llm, max_iterations=5)
        result = agent.run(brief)
        
        assert result.final_iteration <= 5


class TestFormatting:
    def test_format_as_json(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=1)
        result = agent.run(sample_brief)
        
        json_output = format_result_as_json(result)
        assert isinstance(json_output, str)
        assert "brief" in json_output
        assert "variants" in json_output
        assert "success" in json_output
        
        import json
        parsed = json.loads(json_output)
        assert parsed["brief"] == sample_brief
    
    def test_format_as_markdown(self, mock_llm, sample_brief):
        agent = MarketingAgent(mock_llm, max_iterations=1)
        result = agent.run(sample_brief)
        
        md_output = format_result_as_markdown(result)
        assert isinstance(md_output, str)
        assert "# Marketing Content Agent Report" in md_output
        assert "## Brief" in md_output
        assert "## Generated Content Variants" in md_output
        assert "## Summary" in md_output
        assert sample_brief["product"] in md_output


class TestContentVariant:
    def test_content_variant_creation(self):
        variant = ContentVariant(
            channel="twitter",
            content="Test content",
            iteration=1,
            validation_results={"all_passed": True}
        )
        assert variant.channel == "twitter"
        assert variant.content == "Test content"
        assert variant.iteration == 1
        assert variant.validation_results["all_passed"] is True
