import httpx
import logging
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)
TIMEOUT_CONFIG = httpx.Timeout(30.0, connect=10.0)
MAX_RETRIES = 3
MAX_ARTICLES = 12
MAX_ARTICLES_EXPANDED = 20
EXCLUDED_PATHS = {"/blog", "/blog/", "/blog/feed.xml", "/blog/feed/json", "/blog/feed/atom"}


class BuilderioCrawler(BaseCrawler):
    platform = "builderio"
    BASE_URL = "https://www.builder.io"
    LIST_URL = "https://www.builder.io/blog/"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def login(self, credentials: Dict[str, str]) -> bool:
        return True

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        expanded = kwargs.get('expanded', False)
        max_articles = MAX_ARTICLES_EXPANDED if expanded else MAX_ARTICLES
        logger.info(f"[Builder.io] 开始抓取博客... (expanded={expanded}, max={max_articles})")
        article_urls = await self._fetch_article_urls()
        logger.info(f"[Builder.io] 发现 {len(article_urls)} 篇文章链接")

        results = []
        for url in article_urls[:max_articles]:
            try:
                result = await self._fetch_article(url)
                if result:
                    results.append(result)
                await self.random_delay(1, 2)
            except Exception as e:
                logger.warning(f"[Builder.io] 抓取文章失败 {url}: {e}")
                continue

        ai_filtered = self.filter_ai_content(results)
        shuffled = self.random_shuffle(ai_filtered)
        limited = shuffled[:max_articles]
        logger.info(
            f"[Builder.io] 完成: 原始 {len(results)} 条, "
            f"AI过滤后 {len(ai_filtered)} 条, 返回 {len(limited)} 条"
        )
        return limited

    async def _fetch_article_urls(self) -> List[str]:
        html = await self._get_with_retry(self.LIST_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for tag in soup.find_all("a", href=re.compile(r"^/blog/")):
            href = tag.get("href", "")
            if href in EXCLUDED_PATHS:
                continue
            if href and not href.startswith("/blog/feed"):
                links.add(f"{self.BASE_URL}{href}")

        if not links:
            pattern = re.compile(r'href="(/blog/[^"]+)"')
            for match in pattern.findall(html):
                if match in EXCLUDED_PATHS or match.startswith("/blog/feed"):
                    continue
                links.add(f"{self.BASE_URL}{match}")

        return list(links)

    async def _fetch_article(self, url: str) -> CrawlResult:
        html = await self._get_with_retry(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # 移除 script/style/noscript 等无意义标签，避免 JSON-LD 和 CSS 混入正文
        for bad_tag in soup.find_all(["script", "style", "noscript", "nav", "header", "footer"]):
            bad_tag.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = self.clean_html(str(h1))

        content = ""
        selectors = ["main article", "article", "main", "[role='main']"]
        for sel in selectors:
            tag = soup.select_one(sel)
            if tag:
                content = self.clean_html(str(tag))
                break

        if not content:
            body = soup.find("body")
            if body:
                content = self.clean_html(str(body))

        slug = url.rstrip("/").split("/")[-1]
        external_id = f"builderio_{slug}"

        return CrawlResult(
            platform=self.platform,
            external_id=external_id,
            title=title,
            content=content[:3000],
            author="Builder.io",
            author_url="https://www.builder.io",
            url=url,
            raw_data={"slug": slug, "url": url},
            fetched_at=datetime.now(),
        )

    async def _get_with_retry(self, url: str) -> str:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
                    resp = await client.get(url, headers=self.headers, follow_redirects=True)
                    resp.raise_for_status()
                    return resp.text
            except httpx.TimeoutException as e:
                logger.warning(
                    f"[Builder.io] 请求超时 {url} (尝试 {attempt}/{MAX_RETRIES}): {e}"
                )
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"[Builder.io] HTTP 错误 {e.response.status_code} "
                    f"{url} (尝试 {attempt}/{MAX_RETRIES})"
                )
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.warning(
                    f"[Builder.io] 请求异常 {url} (尝试 {attempt}/{MAX_RETRIES}): {e}"
                )
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
        return ""
