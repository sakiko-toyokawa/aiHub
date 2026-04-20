import httpx
import logging
import xml.etree.ElementTree as ET
import asyncio
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import email.utils
from crawler.base import BaseCrawler, CrawlResult

logger = logging.getLogger(__name__)
TIMEOUT_CONFIG = httpx.Timeout(30.0, connect=10.0)
MAX_RETRIES = 3
MAX_ITEMS = 15
MAX_ITEMS_EXPANDED = 25


class RssCrawler(BaseCrawler):
    platform = "rss"
    supports_incremental = True

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.feed_url = config.get("feed_url") if config else None
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def login(self, credentials: Dict[str, str]) -> bool:
        return True

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        if not self.feed_url:
            logger.warning("[RSS] feed_url not configured")
            return []

        expanded = kwargs.get("expanded", False)
        max_items = MAX_ITEMS_EXPANDED if expanded else MAX_ITEMS
        last_fetched_at = kwargs.get("last_fetched_at")
        last_item_id = kwargs.get("last_item_id")

        logger.info(
            f"[RSS] Fetching feed: {self.feed_url} "
            f"(expanded={expanded}, max={max_items}, "
            f"incremental={last_fetched_at is not None})"
        )

        xml_text = await self._get_with_retry(self.feed_url)
        if not xml_text:
            logger.warning(f"[RSS] Failed to fetch feed: {self.feed_url}")
            return []

        items = self._parse_feed(xml_text, max_items, last_fetched_at, last_item_id)
        logger.info(f"[RSS] Parsed {len(items)} new items from feed (incremental)")

        # AI 内容过滤
        ai_filtered = self.filter_ai_content(items)
        shuffled = self.random_shuffle(ai_filtered)
        limited = shuffled[:max_items]
        logger.info(
            f"[RSS] Done: raw {len(items)}, AI-filtered {len(ai_filtered)}, "
            f"returning {len(limited)}"
        )
        return limited

    def _parse_feed(
        self,
        xml_text: str,
        max_items: int,
        last_fetched_at: Optional[datetime] = None,
        last_item_id: Optional[str] = None,
    ) -> List[CrawlResult]:
        """Parse RSS 2.0 or Atom feed XML into CrawlResult list.

        Args:
            xml_text: Raw XML text
            max_items: Maximum items to return
            last_fetched_at: Only return items newer than this timestamp (incremental)
            last_item_id: Only return items after this ID (incremental fallback)
        """
        """Parse RSS 2.0 or Atom feed XML into CrawlResult list."""
        results = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning(f"[RSS] XML parse error: {e}")
            return results

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        # Detect feed type by root tag
        root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

        entries = []
        if root_tag == "rss":
            # RSS 2.0
            channel = root.find("channel")
            if channel is not None:
                feed_title = self._text(channel.find("title"))
                entries = channel.findall("item")
                for item in entries:
                    result = self._parse_rss_item(item, feed_title, ns)
                    if self._should_stop_parsing(result, last_fetched_at, last_item_id):
                        break
                    if self._is_new_item(result, last_fetched_at, last_item_id):
                        results.append(result)
                        if len(results) >= max_items:
                            break
        elif root_tag == "feed":
            # Atom
            feed_title = self._text(root.find("atom:title", ns))
            entries = root.findall("atom:entry", ns)
            for entry in entries:
                result = self._parse_atom_entry(entry, feed_title, ns)
                if self._should_stop_parsing(result, last_fetched_at, last_item_id):
                    break
                if self._is_new_item(result, last_fetched_at, last_item_id):
                    results.append(result)
                    if len(results) >= max_items:
                        break
        else:
            logger.warning(f"[RSS] Unknown feed type: {root_tag}")

        return results

    def _is_new_item(
        self,
        result: CrawlResult,
        last_fetched_at: Optional[datetime] = None,
        last_item_id: Optional[str] = None,
    ) -> bool:
        """Check if item is new based on incremental criteria."""
        # If no incremental state, accept all
        if not last_fetched_at and not last_item_id:
            return True

        # Check by ID first (most reliable)
        if last_item_id and result.external_id == last_item_id:
            return False

        # Check by publication date
        if last_fetched_at:
            pub_date = self._extract_pub_date(result.raw_data)
            if pub_date and pub_date <= last_fetched_at:
                return False

        return True

    def _should_stop_parsing(
        self,
        result: CrawlResult,
        last_fetched_at: Optional[datetime] = None,
        last_item_id: Optional[str] = None,
    ) -> bool:
        """Check if we should stop parsing (for chronologically ordered feeds)."""
        if not last_fetched_at and not last_item_id:
            return False

        # If we hit the last seen ID, stop
        if last_item_id and result.external_id == last_item_id:
            return True

        # If item is older than last fetch, stop (feeds are typically reverse-chronological)
        if last_fetched_at:
            pub_date = self._extract_pub_date(result.raw_data)
            if pub_date and pub_date <= last_fetched_at:
                return True

        return False

    def _extract_pub_date(self, raw_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract publication date from raw_data dict."""
        pub_date_str = raw_data.get("pub_date") or raw_data.get("updated")
        if not pub_date_str:
            return None

        try:
            # Try RFC 822 format first (RSS)
            parsed = email.utils.parsedate_to_datetime(pub_date_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            pass

        # Try ISO 8601 format (Atom)
        for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
            try:
                dt = datetime.strptime(pub_date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        return None

    def _parse_rss_item(self, item: ET.Element, feed_title: str, ns: Dict[str, str]) -> CrawlResult:
        title = self._text(item.find("title"))
        link = self._text(item.find("link"))
        # Prefer content:encoded > description
        content_elem = item.find("content:encoded", ns)
        description = self._text(content_elem) if content_elem is not None else self._text(item.find("description"))
        pub_date = self._text(item.find("pubDate"))
        author = self._text(item.find("author"))
        if not author:
            author = self._text(item.find("dc:creator", ns))
        if not author:
            author = feed_title

        guid = self._text(item.find("guid"))
        external_id = guid or link or title or ""
        external_id = re.sub(r"[^a-zA-Z0-9_-]", "_", external_id)[:100]
        if not external_id:
            external_id = f"rss_{datetime.now().timestamp()}"

        # Clean HTML from description
        content = self.clean_html(description) if description else ""

        return CrawlResult(
            platform=self.platform,
            external_id=external_id,
            title=title or "无标题",
            content=content[:3000] if content else "",
            author=author or "RSS",
            author_url="",
            url=link or self.feed_url,
            raw_data={
                "feed_url": self.feed_url,
                "feed_title": feed_title,
                "pub_date": pub_date,
            },
            fetched_at=datetime.now(),
        )

    def _parse_atom_entry(self, entry: ET.Element, feed_title: str, ns: Dict[str, str]) -> CrawlResult:
        title = self._text(entry.find("atom:title", ns))
        # Atom link is an attribute
        link_elem = entry.find("atom:link", ns)
        link = link_elem.get("href") if link_elem is not None else ""

        # Prefer atom:content > atom:summary
        content_elem = entry.find("atom:content", ns)
        summary = self._text(content_elem) if content_elem is not None else self._text(entry.find("atom:summary", ns))

        updated = self._text(entry.find("atom:updated", ns))
        author_elem = entry.find("atom:author", ns)
        author = self._text(author_elem.find("atom:name", ns)) if author_elem is not None else ""
        if not author:
            author = feed_title

        external_id = link or title or ""
        external_id = re.sub(r"[^a-zA-Z0-9_-]", "_", external_id)[:100]
        if not external_id:
            external_id = f"rss_{datetime.now().timestamp()}"

        content = self.clean_html(summary) if summary else ""

        return CrawlResult(
            platform=self.platform,
            external_id=external_id,
            title=title or "无标题",
            content=content[:3000] if content else "",
            author=author or "RSS",
            author_url="",
            url=link or self.feed_url,
            raw_data={
                "feed_url": self.feed_url,
                "feed_title": feed_title,
                "updated": updated,
            },
            fetched_at=datetime.now(),
        )

    @staticmethod
    def _text(elem: ET.Element | None) -> str:
        """Safely extract text from an XML element."""
        if elem is None:
            return ""
        return (elem.text or "").strip()

    async def _get_with_retry(self, url: str) -> str:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
                    resp = await client.get(url, headers=self.headers, follow_redirects=True)
                    resp.raise_for_status()
                    return resp.text
            except httpx.TimeoutException as e:
                logger.warning(f"[RSS] Timeout {url} (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPStatusError as e:
                logger.warning(f"[RSS] HTTP {e.response.status_code} {url} (attempt {attempt}/{MAX_RETRIES})")
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.warning(f"[RSS] Error {url} (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
        return ""
