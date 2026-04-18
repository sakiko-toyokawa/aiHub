from datetime import datetime
from typing import List, Dict, Any, Optional
from crawler.base import BaseCrawler, CrawlResult
import logging

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """
    Bilibili 爬虫 - 使用 bilibili-api-python 库
    项目地址: https://github.com/Nemo2011/bilibili-api
    """

    platform = "bilibili"

    # AI 相关搜索关键词 - 带权重，聚焦明确的 AI/大模型相关内容
    SEARCH_KEYWORDS = {
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

    # 科技区 TID
    TID_TECH = 36

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.sessdata = config.get("sessdata", "") if config else ""
        self.credential = None

    def _get_credential(self):
        """获取认证信息"""
        if self.credential is None and self.sessdata:
            try:
                from bilibili_api import Credential
                self.credential = Credential(sessdata=self.sessdata)
            except ImportError:
                print("bilibili-api not installed")
                return None
        return self.credential

    async def login(self, credentials: Dict[str, str]) -> bool:
        """验证 SESSDATA 是否有效"""
        if not self.sessdata:
            # 未登录也可以获取公开内容
            return True

        try:
            from bilibili_api import user
            credential = self._get_credential()
            if credential:
                # 尝试获取用户信息验证
                u = user.User(credential=credential)
                info = await u.get_user_info()
                return info is not None
            return True
        except Exception as e:
            print(f"Bilibili login check failed: {e}")
            # 公开内容不需要登录
            return True

    async def fetch(self, **kwargs) -> List[CrawlResult]:
        """抓取 Bilibili AI 相关内容"""
        expanded = kwargs.get('expanded', False)
        results = []

        try:
            from bilibili_api import search

            credential = self._get_credential()

            # 按权重随机选择关键词，expanded 模式下选更多
            keywords_count = 5 if expanded else 3
            keywords_to_search = self.weighted_random_sample(self.SEARCH_KEYWORDS, keywords_count)
            logger.info(f"[Bilibili] 按权重随机选择关键词: {keywords_to_search} (expanded={expanded})")

            for keyword in keywords_to_search:
                try:
                    search_results = await self._search_videos(keyword, credential, expanded)
                    results.extend(search_results)
                    await self.random_delay(2, 3)
                except Exception as e:
                    print(f"Error searching Bilibili for '{keyword}': {e}")
                    continue

        except ImportError:
            print("bilibili-api not installed, skipping Bilibili crawler")
            return []
        except Exception as e:
            print(f"Bilibili crawler error: {e}")

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
        return shuffled_results[:max_return]

    async def _search_videos(self, keyword: str, credential, expanded: bool = False) -> List[CrawlResult]:
        """搜索视频"""
        from bilibili_api import search

        results = []

        # expanded 模式下切换排序方式以获取更多结果
        if expanded:
            order_type = search.OrderVideo.PUBDATE  # 按发布日期排序，获取最新内容
        else:
            order_type = search.OrderVideo.CLICK  # 按播放量排序

        # 搜索视频
        search_result = await search.search_by_type(
            keyword=keyword,
            search_type=search.SearchObjectType.VIDEO,
            order_type=order_type,
            page=1
        )

        for item in search_result.get("result", []):
            try:
                bvid = item.get("bvid")
                if not bvid:
                    continue

                # 保留原始标题（含HTML标签），API层会统一处理
                raw_title = item.get("title", "")

                result = CrawlResult(
                    platform=self.platform,
                    external_id=bvid,
                    title=raw_title,
                    content=item.get("description", ""),
                    author=item.get("author", ""),
                    author_url=f"https://space.bilibili.com/{item.get('mid', '')}",
                    url=f"https://www.bilibili.com/video/{bvid}",
                    raw_data={
                        "bvid": bvid,
                        "aid": item.get("aid"),
                        "pic": item.get("pic"),
                        "play": item.get("play"),
                        "video_review": item.get("video_review")
                    },
                    fetched_at=datetime.now()
                )
                results.append(result)
            except Exception as e:
                print(f"Error parsing Bilibili video: {e}")
                continue

        return results

    async def _fetch_tech_hot(self, credential) -> List[CrawlResult]:
        """获取科技区热门"""
        from bilibili_api import channel_series

        results = []

        # 获取科技区视频
        channel_videos = await channel_series.get_channel_videos(
            channel_id=self.TID_TECH,
            order=channel_series.ChannelOrder.VIEW,  # 按播放量
            page=1
        )

        for item in channel_videos.get("list", []):
            try:
                bvid = item.get("bvid")
                if not bvid:
                    continue

                result = CrawlResult(
                    platform=self.platform,
                    external_id=bvid,
                    title=item.get("title", ""),
                    content=item.get("desc", ""),
                    author=item.get("owner", {}).get("name", ""),
                    author_url=f"https://space.bilibili.com/{item.get('owner', {}).get('mid', '')}",
                    url=f"https://www.bilibili.com/video/{bvid}",
                    raw_data=item,
                    fetched_at=datetime.now()
                )
                results.append(result)
            except Exception as e:
                print(f"Error parsing Bilibili channel video: {e}")
                continue

        return results
