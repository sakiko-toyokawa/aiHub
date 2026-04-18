import httpx
import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)

# 超时配置
TIMEOUT_CONFIG = httpx.Timeout(30.0, connect=10.0)  # 总超时30秒，连接超时10秒
MAX_RETRIES = 3


class GitHubCrawler(BaseCrawler):
    platform = "github"
    TRENDING_TOPICS = {
        # Agent 核心词（最高权重，优先搜索）
        "agent": 10,
        "ai-agent": 10,
        "multi-agent": 10,
        "autonomous-agent": 9,
        "langchain": 9,
        "langgraph": 9,
        "crewai": 9,
        "autogen": 9,
        "swarm": 8,
        # LLM/大模型（高权重）
        "llm": 8,
        "gpt": 7,
        "transformers": 7,
        "llama-index": 7,
        # RAG/工具（中高权重）
        "rag": 8,
        "prompt-engineering": 6,
        "ai-orchestration": 7,
        # 泛化 AI 词（较低权重，作为补充）
        "artificial-intelligence": 4,
        "machine-learning": 4,
        "deep-learning": 4,
        "neural-network": 3,
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_token = config.get("api_token", "") if config else ""
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Knowledge-Hub"
        }
        if self.api_token:
            self.headers["Authorization"] = f"token {self.api_token}"
            logger.info(f"[GitHub] Token 已配置: {self.api_token[:10]}...")
        else:
            logger.warning("[GitHub] Token 未配置，将使用匿名访问（速率限制更低）")

    async def login(self, credentials: Dict[str, str]) -> bool:
        return True

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        expanded = kwargs.get('expanded', False)
        logger.info("=" * 50)
        logger.info(f"[GitHub] 开始抓取 AI 相关仓库... (expanded={expanded})")
        results = []

        logger.info("[GitHub] 获取 Trending 仓库...")
        trending = await self._fetch_with_retry(self._fetch_trending, expanded)
        if trending:
            logger.info(f"[GitHub] Trending 获取到 {len(trending)} 条")
            results.extend(trending)
        else:
            logger.warning("[GitHub] Trending 获取失败或为空")

        # 按权重随机选择话题，expanded 模式下选更多
        topics_count = 5 if expanded else 3
        topics_to_search = self.weighted_random_sample(self.TRENDING_TOPICS, topics_count)
        logger.info(f"[GitHub] 按权重随机选择 {len(topics_to_search)} 个话题: {topics_to_search}")
        for idx, topic in enumerate(topics_to_search, 1):
            logger.info(f"[GitHub] [{idx}/{len(topics_to_search)}] 搜索 topic: '{topic}'")
            topic_repos = await self._fetch_with_retry(self._fetch_topic_repos, topic, expanded)
            if topic_repos:
                logger.info(f"[GitHub] topic '{topic}' 获取到 {len(topic_repos)} 条")
                results.extend(topic_repos)
            else:
                logger.warning(f"[GitHub] topic '{topic}' 获取失败或为空")
            if idx < len(topics_to_search):
                await self.random_delay(1, 2)

        ai_filtered = self.filter_ai_content(results)
        # expanded 模式下放宽限制，返回更多结果
        max_return = 10 if expanded else 5
        shuffled_results = self.random_shuffle(ai_filtered)
        limited_results = shuffled_results[:max_return]
        logger.info(f"[GitHub] 抓取完成: 原始 {len(results)} 条, AI过滤后 {len(ai_filtered)} 条, 返回 {len(limited_results)} 条")
        logger.info("=" * 50)
        return limited_results

    async def _fetch_with_retry(self, fetch_func, *args) -> List[CrawlResult]:
        """带重试机制的抓取"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await fetch_func(*args)
            except httpx.TimeoutException as e:
                logger.warning(f"[GitHub] 请求超时 (尝试 {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    logger.error(f"[GitHub] 达到最大重试次数，放弃请求")
                    return []
                await asyncio.sleep(2 ** attempt)  # 指数退避
            except httpx.HTTPStatusError as e:
                logger.warning(f"[GitHub] HTTP 错误 {e.response.status_code} (尝试 {attempt}/{MAX_RETRIES})")
                if e.response.status_code in (403, 429):  # 限流
                    if attempt == MAX_RETRIES:
                        return []
                    await asyncio.sleep(5 * attempt)
                else:
                    return []
            except Exception as e:
                logger.error(f"[GitHub] 请求异常 (尝试 {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
                if attempt == MAX_RETRIES:
                    return []
                await asyncio.sleep(2 ** attempt)
        return []

    async def _fetch_trending(self, expanded: bool = False) -> List[CrawlResult]:
        """Fetch trending AI repositories - using topic-based search with time range"""
        # Use topic-based search with time range (最近5天/30天更新的仓库)
        days_back = 30 if expanded else 5
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # expanded 模式下取更多话题构建查询
        topic_count = 8 if expanded else 5
        top_topics = self.weighted_random_sample(self.TRENDING_TOPICS, topic_count)
        topics_query = " OR ".join([f"topic:{t}" for t in top_topics])

        # expanded 模式下降低 stars 门槛
        stars_threshold = 50 if expanded else 100
        query = f"({topics_query}) stars:>{stars_threshold} pushed:>{since_date}"
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "sort": "updated", "order": "desc", "per_page": 20}

        logger.debug(f"[GitHub] 请求 trending API: {url}")
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

        results = []
        items = data.get("items", [])
        logger.debug(f"[GitHub] trending API 返回 {len(items)} 条")
        for item in items:
            result = CrawlResult(
                platform=self.platform,
                external_id=str(item["id"]),
                title=item["name"],
                content=item.get("description", ""),
                author=item["owner"]["login"],
                author_url=item["owner"]["html_url"],
                url=item["html_url"],
                raw_data=item,
                fetched_at=datetime.now()
            )
            results.append(result)
        return results

    async def _fetch_topic_repos(self, topic: str, expanded: bool = False) -> List[CrawlResult]:
        """Fetch repositories by topic with time range"""
        days_back = 30 if expanded else 5
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        url = "https://api.github.com/search/repositories"
        # expanded 模式下降低 stars 门槛
        stars_threshold = 20 if expanded else 50
        params = {"q": f"topic:{topic} stars:>{stars_threshold} pushed:>{since_date}", "sort": "updated", "order": "desc", "per_page": 10}

        logger.debug(f"[GitHub] 请求 topic '{topic}' API")
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

        results = []
        items = data.get("items", [])
        logger.debug(f"[GitHub] topic '{topic}' 返回 {len(items)} 条")
        for item in items:
            result = CrawlResult(
                platform=self.platform,
                external_id=str(item["id"]),
                title=item["name"],
                content=item.get("description", ""),
                author=item["owner"]["login"],
                author_url=item["owner"]["html_url"],
                url=item["html_url"],
                raw_data=item,
                fetched_at=datetime.now()
            )
            results.append(result)
        return results
