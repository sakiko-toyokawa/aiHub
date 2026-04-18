"""
爬虫集成测试
测试所有爬虫是否能正确初始化和运行（使用 mock）
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from crawler import (
    GitHubCrawler,
    ZhihuCrawler,
    BilibiliCrawler,
    TwitterCrawler,
    get_crawler
)


class TestCrawlerRegistry:
    """测试爬虫注册表"""

    def test_get_crawler_github(self):
        crawler = get_crawler("github")
        assert isinstance(crawler, GitHubCrawler)

    def test_get_crawler_zhihu(self):
        crawler = get_crawler("zhihu")
        assert isinstance(crawler, ZhihuCrawler)

    def test_get_crawler_bilibili(self):
        crawler = get_crawler("bilibili")
        assert isinstance(crawler, BilibiliCrawler)

    def test_get_crawler_twitter(self):
        crawler = get_crawler("twitter")
        assert isinstance(crawler, TwitterCrawler)

    def test_get_crawler_unknown(self):
        with pytest.raises(ValueError):
            get_crawler("unknown")


class TestGitHubCrawler:
    """测试 GitHub 爬虫"""

    @pytest.fixture
    def crawler(self):
        return GitHubCrawler(config={"api_token": "test_token"})

    def test_init(self, crawler):
        assert crawler.platform == "github"
        assert "Authorization" in crawler.headers

    @pytest.mark.asyncio
    async def test_login(self, crawler):
        # GitHub 不需要登录
        result = await crawler.login({})
        assert result is True


class TestZhihuCrawler:
    """测试知乎爬虫"""

    @pytest.fixture
    def crawler(self):
        return ZhihuCrawler(config={"cookie": "test_cookie"})

    def test_init(self, crawler):
        assert crawler.platform == "zhihu"
        assert crawler.cookie == "test_cookie"

    @pytest.mark.asyncio
    async def test_login_without_cookie(self):
        crawler = ZhihuCrawler(config={})
        result = await crawler.login({})
        assert result is False


class TestBilibiliCrawler:
    """测试 Bilibili 爬虫"""

    @pytest.fixture
    def crawler(self):
        return BilibiliCrawler(config={"sessdata": "test_sessdata"})

    def test_init(self, crawler):
        assert crawler.platform == "bilibili"

    @pytest.mark.asyncio
    async def test_login(self, crawler):
        # Bilibili 公开内容不需要登录
        result = await crawler.login({})
        assert result is True


class TestTwitterCrawler:
    """测试 Twitter 爬虫"""

    @pytest.fixture
    def crawler(self):
        return TwitterCrawler(config={
            "username": "test_user",
            "password": "test_pass"
        })

    def test_init(self, crawler):
        assert crawler.platform == "twitter"
        assert crawler.username == "test_user"

    @pytest.mark.asyncio
    async def test_login_without_credentials(self):
        crawler = TwitterCrawler(config={})
        result = await crawler.login({})
        assert result is False


class TestAIFiltering:
    """测试 AI 内容过滤功能"""

    @pytest.fixture
    def crawler(self):
        return GitHubCrawler()

    def test_is_ai_related(self, crawler):
        assert crawler.is_ai_related("ChatGPT is amazing") is True
        assert crawler.is_ai_related("GPT-4 new features") is True
        assert crawler.is_ai_related("人工智能发展趋势") is True
        assert crawler.is_ai_related("Python tutorial") is False
        assert crawler.is_ai_related("Cooking recipes") is False

    def test_filter_ai_content(self, crawler):
        from crawler.base import CrawlResult
        from datetime import datetime

        items = [
            CrawlResult(
                platform="test",
                external_id="1",
                title="GPT-4 new features",
                content="AI content",
                author="test",
                author_url=None,
                url="http://example.com/1",
                raw_data={},
                fetched_at=datetime.now()
            ),
            CrawlResult(
                platform="test",
                external_id="2",
                title="Cooking recipes",
                content="Food content",
                author="chef",
                author_url=None,
                url="http://example.com/2",
                raw_data={},
                fetched_at=datetime.now()
            )
        ]

        filtered = crawler.filter_ai_content(items)
        assert len(filtered) == 1
        assert filtered[0].external_id == "1"
