"""
Tests for LLM interfaces.
"""

import pytest
from marketing_agent.llm import MockLLM, create_llm


class TestMockLLM:
    def test_initialization(self):
        llm = MockLLM()
        assert llm.call_count == 0
    
    def test_generate_increments_count(self):
        llm = MockLLM()
        messages = [{"role": "user", "content": "test"}]
        llm.generate(messages)
        assert llm.call_count == 1
        llm.generate(messages)
        assert llm.call_count == 2
    
    def test_generate_plan(self):
        llm = MockLLM()
        messages = [
            {"role": "system", "content": "strategist"},
            {"role": "user", "content": "Create a plan and strategy for twitter"}
        ]
        result = llm.generate(messages)
        assert "strategy" in result.lower() or "plan" in result.lower()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_content_twitter(self):
        llm = MockLLM()
        messages = [
            {"role": "user", "content": "Write twitter content\nProduct: Coffee\nAudience: workers"}
        ]
        result = llm.generate(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_content_facebook(self):
        llm = MockLLM()
        messages = [
            {"role": "user", "content": "Write facebook content\nProduct: App\nAudience: users"}
        ]
        result = llm.generate(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_revision(self):
        llm = MockLLM()
        messages = [
            {"role": "user", "content": "Revise this content\nProduct: Coffee"}
        ]
        result = llm.generate(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_deterministic_behavior(self):
        llm1 = MockLLM()
        llm2 = MockLLM()
        
        messages = [{"role": "user", "content": "Write twitter content for Coffee"}]
        
        result1 = llm1.generate(messages)
        result2 = llm2.generate(messages)
        
        assert result1 == result2


class TestCreateLLM:
    def test_create_mock_llm(self):
        llm = create_llm(mock=True)
        assert isinstance(llm, MockLLM)
    
    def test_create_openai_without_key_raises_error(self):
        import os
        old_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        with pytest.raises(ValueError, match="API key"):
            create_llm(mock=False)
        
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
    
    def test_create_openai_with_key(self):
        from marketing_agent.llm import OpenAILLM
        try:
            llm = create_llm(mock=False, api_key="sk-test-key-123")
            assert isinstance(llm, OpenAILLM)
        except ImportError:
            pytest.skip("OpenAI package not installed")
