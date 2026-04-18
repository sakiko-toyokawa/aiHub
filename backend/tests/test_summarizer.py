"""Tests for the summarizer module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from summarizer.llm_client import LLMClient, SummaryResult


class TestLLMClient:
    """Test cases for LLMClient."""

    def test_init_with_default_provider(self):
        """Test initialization with default provider (openai)."""
        client = LLMClient()
        assert client.provider == 'openai'
        assert client.model == 'gpt-4o-mini'

    def test_init_with_supported_providers(self):
        """Test initialization with all supported providers."""
        providers = {
            'openai': 'gpt-4o-mini',
            'claude': 'claude-3-haiku-20240307',
            'deepseek': 'deepseek-chat',
            'glm': 'glm-4',
            'kimi': 'moonshot-v1-8k',
            'minimax': 'abab6.5-chat'
        }
        for provider, expected_model in providers.items():
            client = LLMClient(provider=provider)
            assert client.provider == provider
            assert client.model == expected_model

    def test_init_with_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LLMClient(provider='unsupported')
        assert "Unsupported provider: unsupported" in str(exc_info.value)

    def test_build_prompt(self):
        """Test prompt building."""
        client = LLMClient()
        title = "Test Title"
        content = "This is test content."
        prompt = client._build_prompt(content, title)

        assert title in prompt
        assert content in prompt
        assert "## 核心主题" in prompt
        assert "## 关键要点" in prompt
        assert "## 相关技术/工具" in prompt
        assert "## 重要性评估" in prompt
        assert "## 标签" in prompt

    def test_build_prompt_content_truncation(self):
        """Test that content longer than 8000 chars is truncated."""
        client = LLMClient()
        long_content = "x" * 10000
        prompt = client._build_prompt(long_content, "Test")

        # Content should be truncated to 8000 chars
        assert len(prompt) < 9000

    def test_parse_result_complete(self):
        """Test parsing a complete result."""
        client = LLMClient()
        text = """## 核心主题
This is the summary.

## 关键要点
- Point 1
- Point 2
- Point 3

## 相关技术/工具
- Tech 1
- Tech 2

## 重要性评估
星级: 4/5

## 标签
tag1, tag2, tag3"""

        result = client._parse_result(text)
        assert result['summary'] == "This is the summary."
        assert result['key_points'] == ["Point 1", "Point 2", "Point 3"]
        assert result['tags'] == ["tag1", "tag2", "tag3"]
        assert result['importance'] == 4

    def test_parse_result_empty(self):
        """Test parsing an empty result."""
        client = LLMClient()
        result = client._parse_result("")
        assert result['summary'] == ""
        assert result['key_points'] == []
        assert result['tags'] == []
        assert result['importance'] == 3

    def test_parse_result_importance_bounds(self):
        """Test that importance is clamped to 1-5 range."""
        client = LLMClient()
        text_high = "## 重要性评估\n星级: 10/5"
        text_low = "## 重要性评估\n星级: -5/5"

        result_high = client._parse_result(text_high)
        result_low = client._parse_result(text_low)

        assert result_high['importance'] == 5
        assert result_low['importance'] == 1

    @pytest.mark.asyncio
    async def test_summarize(self):
        """Test summarize method with mocked litellm."""
        client = LLMClient(provider='openai')

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """## 核心主题
Test summary.

## 关键要点
- Point 1
- Point 2

## 相关技术/工具
- Python

## 重要性评估
星级: 4/5

## 标签
test, python"""
        mock_response.usage.total_tokens = 150

        with patch('summarizer.llm_client.litellm.acompletion', new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response

            result = await client.summarize("Test content", "Test Title")

            assert isinstance(result, SummaryResult)
            assert result.summary_text == "Test summary."
            assert result.key_points == ["Point 1", "Point 2"]
            assert result.tags == ["test", "python"]
            assert result.importance == 4
            assert result.model_used == "gpt-4o-mini"
            assert result.provider == "openai"
            assert result.tokens_used == 150

            # Verify the mock was called
            mock_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_fallback(self):
        """Test summarize with unparseable response - uses defaults for missing fields."""
        client = LLMClient(provider='openai')

        # Mock response with unparseable content (no proper sections)
        raw_content = "This is just raw text without proper formatting."
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = raw_content
        mock_response.usage = None

        with patch('summarizer.llm_client.litellm.acompletion', new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response

            result = await client.summarize("Test content")

            assert isinstance(result, SummaryResult)
            # Parser initializes summary as empty string when no section found
            # The dict.get() fallback only triggers when key is missing, not when value is empty
            assert result.summary_text == ""
            assert result.key_points == []
            assert result.tags == []
            assert result.importance == 3
            assert result.tokens_used == 0


class TestSummaryResult:
    """Test cases for SummaryResult dataclass."""

    def test_summary_result_creation(self):
        """Test creating a SummaryResult instance."""
        result = SummaryResult(
            summary_text="Test summary",
            key_points=["point1", "point2"],
            tags=["tag1", "tag2"],
            importance=4,
            model_used="gpt-4o-mini",
            provider="openai",
            tokens_used=100
        )

        assert result.summary_text == "Test summary"
        assert result.key_points == ["point1", "point2"]
        assert result.tags == ["tag1", "tag2"]
        assert result.importance == 4
        assert result.model_used == "gpt-4o-mini"
        assert result.provider == "openai"
        assert result.tokens_used == 100
