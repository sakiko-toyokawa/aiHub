import httpx
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)
TIMEOUT_CONFIG = httpx.Timeout(20.0, connect=10.0)
MAX_RETRIES = 3
SAMPLE_SIZE = 20
SAMPLE_SIZE_EXPANDED = 50


class HackerNewsCrawler(BaseCrawler):
    platform = "hackernews"
    TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
    ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)

    async def login(self, credentials: Dict[str, str]) -> bool:
        return True

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        expanded = kwargs.get('expanded', False)
        sample_size = SAMPLE_SIZE_EXPANDED if expanded else SAMPLE_SIZE
        logger.info(f"[HackerNews] 开始抓取热门故事... (expanded={expanded}, sample={sample_size})")
        story_ids = await self._fetch_top_story_ids()
        if not story_ids:
            logger.warning("[HackerNews] 无法获取故事列表")
            return []

        sampled_ids = self.random_sample(story_ids, sample_size)
        logger.info(f"[HackerNews] 随机选择 {len(sampled_ids)} 个故事")

        results = []
        for story_id in sampled_ids:
            try:
                story = await self._fetch_story(story_id)
                if story:
                    results.append(story)
            except Exception as e:
                logger.warning(f"[HackerNews] 获取故事 {story_id} 失败: {e}")
                continue

        ai_filtered = self.filter_ai_content(results)
        shuffled = self.random_shuffle(ai_filtered)
        limited = shuffled[:sample_size]
        logger.info(
            f"[HackerNews] 完成: 原始 {len(results)} 条, "
            f"AI过滤后 {len(ai_filtered)} 条, 返回 {len(limited)} 条"
        )
        return limited

    async def _fetch_top_story_ids(self) -> List[int]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
                    resp = await client.get(self.TOP_STORIES_URL, follow_redirects=True)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.warning(
                    f"[HackerNews] 获取 top stories 失败 (尝试 {attempt}/{MAX_RETRIES}): {e}"
                )
                if attempt == MAX_RETRIES:
                    return []
                await asyncio.sleep(2 ** attempt)
        return []

    async def _fetch_story(self, story_id: int) -> CrawlResult:
        url = self.ITEM_URL.format(story_id)
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

        if not data or data.get("type") != "story":
            return None

        title = data.get("title", "")
        story_url = data.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
        text = data.get("text", "")
        content = text if text else title

        return CrawlResult(
            platform=self.platform,
            external_id=str(story_id),
            title=title,
            content=content,
            author=data.get("by", ""),
            author_url=f"https://news.ycombinator.com/user?id={data.get('by', '')}",
            url=story_url,
            raw_data={
                "score": data.get("score", 0),
                "descendants": data.get("descendants", 0),
                "time": data.get("time", 0),
                "type": data.get("type"),
            },
            fetched_at=datetime.now(),
        )
