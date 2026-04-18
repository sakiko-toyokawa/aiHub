import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from crawler.base import BaseCrawler, CrawlResult
from crawler.github_crawler import GitHubCrawler


class MockCrawler(BaseCrawler):
    platform = "mock"

    async def fetch(self, **kwargs):
        return []

    async def login(self, credentials):
        return True


class TestCrawlResult:
    def test_crawl_result_creation(self):
        result = CrawlResult(
            platform="test",
            external_id="123",
            title="Test Title",
            content="Test Content",
            author="Test Author",
            author_url="https://example.com/author",
            url="https://example.com/post",
            raw_data={"key": "value"},
            fetched_at=datetime.now()
        )
        assert result.platform == "test"
        assert result.external_id == "123"
        assert result.title == "Test Title"
        assert result.content == "Test Content"
        assert result.author == "Test Author"


class TestBaseCrawler:
    def test_is_ai_related_with_ai_keywords(self):
        crawler = MockCrawler()
        assert crawler.is_ai_related("This is about AI and machine learning") is True
        assert crawler.is_ai_related("LLM models are great") is True
        assert crawler.is_ai_related("深度学习技术") is True

    def test_is_ai_related_without_ai_keywords(self):
        crawler = MockCrawler()
        assert crawler.is_ai_related("This is about cooking") is False
        assert crawler.is_ai_related("Sports and games") is False

    def test_is_ai_related_empty_text(self):
        crawler = MockCrawler()
        assert crawler.is_ai_related("") is False
        assert crawler.is_ai_related(None) is False

    def test_filter_ai_content(self):
        crawler = MockCrawler()
        items = [
            CrawlResult(
                platform="test",
                external_id="1",
                title="AI Research Paper",
                content="About machine learning",
                author="Author1",
                author_url="https://example.com/author1",
                url="https://example.com/1",
                raw_data={},
                fetched_at=datetime.now()
            ),
            CrawlResult(
                platform="test",
                external_id="2",
                title="Cooking Recipe",
                content="How to bake a cake",
                author="Author2",
                author_url="https://example.com/author2",
                url="https://example.com/2",
                raw_data={},
                fetched_at=datetime.now()
            ),
            CrawlResult(
                platform="test",
                external_id="3",
                title="Some Title",
                content="GPT implementation details",
                author="Author3",
                author_url="https://example.com/author3",
                url="https://example.com/3",
                raw_data={},
                fetched_at=datetime.now()
            )
        ]
        filtered = crawler.filter_ai_content(items)
        assert len(filtered) == 2
        assert filtered[0].external_id == "1"
        assert filtered[1].external_id == "3"

    @pytest.mark.asyncio
    async def test_random_delay(self):
        crawler = MockCrawler()
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await crawler.random_delay(1.0, 2.0)
            mock_sleep.assert_called_once()
            assert 1.0 <= mock_sleep.call_args[0][0] <= 2.0


class TestGitHubCrawler:
    def test_init_without_token(self):
        crawler = GitHubCrawler()
        assert crawler.api_token == ""
        assert "Authorization" not in crawler.headers

    def test_init_with_token(self):
        crawler = GitHubCrawler(config={"api_token": "test_token"})
        assert crawler.api_token == "test_token"
        assert crawler.headers["Authorization"] == "token test_token"

    @pytest.mark.asyncio
    async def test_login(self):
        crawler = GitHubCrawler()
        result = await crawler.login({})
        assert result is True

    @pytest.mark.asyncio
    async def test_fetch_trending(self):
        crawler = GitHubCrawler()
        mock_response = {
            "items": [
                {
                    "id": 123,
                    "name": "awesome-llm",
                    "description": "A collection of LLM resources",
                    "owner": {"login": "testuser", "html_url": "https://github.com/testuser"},
                    "html_url": "https://github.com/testuser/awesome-llm"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get = AsyncMock(return_value=Mock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            ))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await crawler._fetch_trending()
            assert len(results) == 1
            assert results[0].platform == "github"
            assert results[0].external_id == "123"
            assert results[0].title == "awesome-llm"

    @pytest.mark.asyncio
    async def test_fetch_topic_repos_rate_limit(self):
        crawler = GitHubCrawler()

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get = AsyncMock(return_value=Mock(status_code=403))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            results = await crawler._fetch_topic_repos("llm")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_fetch(self):
        crawler = GitHubCrawler()

        with patch.object(crawler, '_fetch_trending', new_callable=AsyncMock) as mock_trending, \
             patch.object(crawler, '_fetch_topic_repos', new_callable=AsyncMock) as mock_topic, \
             patch.object(crawler, 'random_delay', new_callable=AsyncMock):

            mock_trending.return_value = [
                CrawlResult(
                    platform="github",
                    external_id="1",
                    title="AI Project",
                    content="Machine learning project",
                    author="user1",
                    author_url="https://github.com/user1",
                    url="https://github.com/user1/ai-project",
                    raw_data={},
                    fetched_at=datetime.now()
                )
            ]
            mock_topic.return_value = [
                CrawlResult(
                    platform="github",
                    external_id="2",
                    title="LLM Model",
                    content="GPT implementation",
                    author="user2",
                    author_url="https://github.com/user2",
                    url="https://github.com/user2/llm-model",
                    raw_data={},
                    fetched_at=datetime.now()
                )
            ]

            results = await crawler.fetch()
            assert len(results) == 4  # 1 trending + 3 topics (each returns 1)
