from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
import logging
import os
from crawler.base import BaseCrawler, CrawlResult
from summarizer.llm_client import LLMClient

logger = logging.getLogger(__name__)

# 超时配置
TIMEOUT_CONFIG = httpx.Timeout(20.0, connect=10.0)


class ZhihuCrawler(BaseCrawler):
    """
    知乎爬虫 - 使用 httpx 直接调用知乎 API
    """

    platform = "zhihu"

    # AI 相关话题/关键词 - 带权重，优先搜索高权重词
    AI_TOPICS = {
        # Agent 核心词（最高权重）
        "AI Agent": 10,
        "智能体": 10,
        "多智能体": 10,
        "AutoGPT": 9,
        "LangChain": 9,
        "LangGraph": 9,
        "CrewAI": 9,
        "AutoGen": 9,
        # RAG/框架（高权重）
        "RAG": 9,
        "Agent框架": 8,
        "AI工作流": 7,
        # LLM/大模型（中高权重）
        "大模型": 8,
        "LLM": 8,
        "ChatGPT": 7,
        "Claude": 7,
        "Transformer": 6,
        # 应用/开发（中等权重）
        "AI应用": 6,
        "AI开发": 6,
        "提示词工程": 7,
        "Stable Diffusion": 6,
        # 泛化词（较低权重）
        "人工智能": 4,
        "神经网络": 4,
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.cookie = config.get("cookie", "") if config else ""
        self.llm_client: Optional[LLMClient] = config.get("llm_client") if config else None
        if self.cookie:
            logger.info(f"[知乎] Cookie 已配置: {self.cookie[:30]}...")
        else:
            logger.warning("[知乎] Cookie 未配置")
        if self.llm_client:
            logger.info("[知乎] LLMClient 已配置，支持AI生成标题")
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.zhihu.com/",
            "X-Requested-With": "fetch",
        }

    async def login(self, credentials: Dict[str, str]) -> bool:
        """验证 Cookie 是否有效"""
        if not self.cookie:
            logger.warning("[知乎] Cookie 未配置")
            return False
        try:
            logger.info("[知乎] 验证 Cookie 有效性...")
            async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as http:
                resp = await http.get(
                    "https://www.zhihu.com/api/v4/me",
                    headers=self.headers
                )
                if resp.status_code == 200:
                    logger.info("[知乎] Cookie 验证通过")
                else:
                    logger.warning(f"[知乎] Cookie 验证失败: HTTP {resp.status_code}")
                return resp.status_code == 200
        except httpx.TimeoutException:
            logger.error("[知乎] Cookie 验证超时")
            return False
        except Exception as e:
            logger.error(f"[知乎] Cookie 验证异常: {e}")
            return False

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        """抓取知乎 AI 相关内容"""
        expanded = kwargs.get('expanded', False)
        results = []
        logger.info("=" * 50)
        logger.info(f"[知乎] 开始抓取 AI 相关内容... (expanded={expanded})")

        # expanded 模式下放宽时间限制
        time_threshold = None if expanded else (datetime.now() - timedelta(days=5))

        try:
            # 按权重随机选择话题，expanded 模式下选更多
            topics_count = 10 if expanded else 6
            topics_to_search = self.weighted_random_sample(self.AI_TOPICS, topics_count)
            logger.info(f"[知乎] 按权重随机选择 {len(topics_to_search)} 个话题: {topics_to_search}")

            for idx, topic_name in enumerate(topics_to_search, 1):
                try:
                    logger.info(f"[知乎] [{idx}/{len(topics_to_search)}] 搜索话题: '{topic_name}'")
                    topic_results = await self._search_topic(topic_name, time_threshold)
                    logger.info(f"[知乎] 话题 '{topic_name}' 获取到 {len(topic_results)} 条结果")
                    results.extend(topic_results)
                    if idx < len(topics_to_search):
                        await self.random_delay(2, 4)
                except Exception as e:
                    logger.error(f"[知乎] 搜索话题 '{topic_name}' 失败: {e}")
                    continue

            # 获取热门推荐
            try:
                logger.info("[知乎] 获取热门热榜内容...")
                hot_results = await self._fetch_hot()
                logger.info(f"[知乎] 热榜获取到 {len(hot_results)} 条 AI 相关内容")
                results.extend(hot_results)
            except Exception as e:
                logger.error(f"[知乎] 获取热榜失败: {e}")

        except Exception as e:
            logger.exception(f"[知乎] 抓取过程发生错误: {e}")

        # 去重
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.external_id not in seen_ids:
                seen_ids.add(r.external_id)
                unique_results.append(r)

        ai_filtered = self.filter_ai_content(unique_results)
        # expanded 模式下放宽限制
        max_return = 10 if expanded else 5
        shuffled_results = self.random_shuffle(ai_filtered)
        limited_results = shuffled_results[:max_return]
        logger.info(f"[知乎] 抓取完成: 原始 {len(results)} 条, 去重后 {len(unique_results)} 条, AI过滤后 {len(ai_filtered)} 条, 返回 {len(limited_results)} 条")
        logger.info("=" * 50)

        return limited_results

    async def _search_topic(self, topic_name: str, time_threshold: Optional[datetime] = None) -> List[CrawlResult]:
        """搜索话题获取内容（按时间排序，获取最近内容）"""
        results = []

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as http:
                search_url = "https://www.zhihu.com/api/v4/search_v3"
                # 随机偏移量，获取不同位置的内容
                random_offset = self.random_offset(0, 10)
                params = {
                    "t": "general",
                    "q": topic_name,
                    "correction": "1",
                    "offset": str(random_offset),
                    "limit": "15",
                    "sort": "created_time"  # 按创建时间排序，获取最新内容
                }
                logger.debug(f"[知乎] 话题 '{topic_name}' 使用随机偏移量: {random_offset}")

                logger.debug(f"[知乎] 请求搜索 API: {search_url}, params={params}")
                resp = await http.get(
                    search_url,
                    headers=self.headers,
                    params=params
                )

                if resp.status_code != 200:
                    logger.warning(f"[知乎] 搜索 API 返回错误: HTTP {resp.status_code}")
                    return results

                data = resp.json()
                items = data.get("data", [])
                logger.debug(f"[知乎] 搜索 '{topic_name}' 返回 {len(items)} 个结果")

                for item in items:
                    try:
                        if item.get("type") != "search_result":
                            continue

                        obj = item.get("object", {})
                        if obj.get("type") == "answer":
                            result = await self._parse_answer(obj, time_threshold)
                            if result:
                                results.append(result)
                        elif obj.get("type") == "article":
                            result = await self._parse_article(obj, time_threshold)
                            if result:
                                results.append(result)

                    except Exception as e:
                        logger.warning(f"[知乎] 解析搜索结果失败: {e}")
                        continue

        except Exception as e:
            logger.error(f"[知乎] 搜索话题 '{topic_name}' 发生错误: {e}")

        return results

    async def _fetch_hot(self) -> List[CrawlResult]:
        """获取热门内容"""
        results = []

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as http:
                hot_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
                logger.debug(f"[知乎] 请求热榜 API: {hot_url}")

                resp = await http.get(
                    hot_url,
                    headers=self.headers
                )

                if resp.status_code != 200:
                    logger.warning(f"[知乎] 热榜 API 返回错误: HTTP {resp.status_code}")
                    return results

                data = resp.json()
                items = data.get("data", [])
                logger.debug(f"[知乎] 热榜返回 {len(items)} 条内容")

                ai_count = 0
                for item in items[:20]:
                    try:
                        card = item.get("target", {})
                        if not card:
                            continue

                        # 清理标题和内容中的HTML标签
                        title = self.clean_html(card.get("title", ""))
                        excerpt = self.clean_html(card.get("excerpt", ""))
                        if not self.is_ai_related(title):
                            continue

                        ai_count += 1
                        result = CrawlResult(
                            platform=self.platform,
                            external_id=f"hot_{card.get('id', '')}",
                            title=title,
                            content=excerpt,
                            author="",
                            author_url="",
                            url=card.get("url", ""),
                            raw_data={
                                "type": "hot",
                                "metrics": card.get("metrics", ""),
                                "heat": card.get("heat", 0)
                            },
                            fetched_at=datetime.now()
                        )
                        results.append(result)
                        logger.debug(f"[知乎] 热榜 AI 内容: {title[:50]}...")

                    except Exception as e:
                        logger.warning(f"[知乎] 解析热榜条目失败: {e}")
                        continue

                logger.debug(f"[知乎] 热榜中 AI 相关内容: {ai_count} 条")

        except Exception as e:
            logger.error(f"[知乎] 获取热榜失败: {e}")

        return results

    async def _parse_answer(self, obj: Dict, time_threshold: Optional[datetime] = None) -> Optional[CrawlResult]:
        """解析回答数据"""
        try:
            question = obj.get("question", {})
            author = obj.get("author", {})

            # 获取原始内容并清理HTML
            raw_content = obj.get("content", "")
            content = self.clean_html(raw_content)

            # 优先使用 highlight_title，否则使用 title
            title = question.get("highlight_title", "") or question.get("title", "")

            # 时间过滤
            if time_threshold:
                created_time = obj.get("created_time", 0)
                if created_time and datetime.fromtimestamp(created_time) < time_threshold:
                    return None

            # 使用 BaseCrawler 的权重评分系统
            text = f"{title} {content}"
            score = self.score_ai_relevance(text)
            if score < self.SCORE_THRESHOLD:
                return None

            return CrawlResult(
                platform=self.platform,
                external_id=f"answer_{obj.get('id', '')}",
                title=title,
                content=content[:2000],
                author=author.get("name", ""),
                author_url=f"https://www.zhihu.com/people/{author.get('url_token', '')}" if author.get("url_token") else "",
                url=f"https://www.zhihu.com/question/{question.get('id', '')}/answer/{obj.get('id', '')}",
                raw_data={
                    "question_id": question.get("id"),
                    "answer_id": obj.get("id"),
                    "votes": obj.get("voteup_count", 0),
                    "comments": obj.get("comment_count", 0)
                },
                fetched_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"[知乎] 解析回答失败: {e}")
            return None

    async def _parse_article(self, obj: Dict, time_threshold: Optional[datetime] = None) -> Optional[CrawlResult]:
        """解析文章数据"""
        try:
            author = obj.get("author", {})

            # 获取原始内容并清理HTML
            raw_excerpt = obj.get("excerpt", "")
            content = self.clean_html(raw_excerpt)

            # 优先使用 highlight_title，否则使用 title
            title = obj.get("highlight_title", "") or obj.get("title", "")

            # 时间过滤
            if time_threshold:
                created_time = obj.get("created", 0)
                if created_time and datetime.fromtimestamp(created_time) < time_threshold:
                    return None

            # 使用 BaseCrawler 的权重评分系统
            text = f"{title} {content}"
            score = self.score_ai_relevance(text)
            if score < self.SCORE_THRESHOLD:
                return None

            return CrawlResult(
                platform=self.platform,
                external_id=f"article_{obj.get('id', '')}",
                title=title,
                content=content[:2000],
                author=author.get("name", ""),
                author_url=f"https://www.zhihu.com/people/{author.get('url_token', '')}" if author.get("url_token") else "",
                url=f"https://zhuanlan.zhihu.com/p/{obj.get('id', '')}",
                raw_data={
                    "article_id": obj.get("id"),
                    "votes": obj.get("voteup_count", 0),
                    "comments": obj.get("comment_count", 0)
                },
                fetched_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"[知乎] 解析文章失败: {e}")
            return None
