from typing import Any, Dict, Optional
from crawler.base import BaseCrawler, CrawlResult
from crawler.github_crawler import GitHubCrawler
from crawler.zhihu_crawler import ZhihuCrawler
from crawler.bilibili_crawler import BilibiliCrawler
from crawler.anthropic_crawler import AnthropicCrawler
from crawler.builderio_crawler import BuilderioCrawler
from crawler.hackernews_crawler import HackerNewsCrawler
from summarizer.llm_client import LLMClient

__all__ = [
    "BaseCrawler",
    "CrawlResult",
    "GitHubCrawler",
    "ZhihuCrawler",
    "BilibiliCrawler",
    "AnthropicCrawler",
    "BuilderioCrawler",
    "HackerNewsCrawler",
]

# 爬虫注册表
CRAWLERS = {
    "github": GitHubCrawler,
    "zhihu": ZhihuCrawler,
    "bilibili": BilibiliCrawler,
    "anthropic": AnthropicCrawler,
    "builderio": BuilderioCrawler,
    "hackernews": HackerNewsCrawler,
}


def get_crawler(platform: str, config: Dict[str, Any] = None, llm_client: Optional[LLMClient] = None) -> BaseCrawler:
    """获取指定平台的爬虫实例

    Args:
        platform: 平台名称 (github, zhihu, bilibili, anthropic, builderio, hackernews)
        config: 爬虫配置
        llm_client: 可选的LLMClient实例，用于AI生成标题等功能

    Returns:
        爬虫实例

    Raises:
        ValueError: 如果平台不存在
    """
    crawler_class = CRAWLERS.get(platform)
    if not crawler_class:
        raise ValueError(f"Unknown platform: {platform}")

    config = config or {}
    if llm_client:
        config['llm_client'] = llm_client

    return crawler_class(config)
