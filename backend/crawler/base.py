from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import random
import logging
import re
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    platform: str
    external_id: str
    title: Optional[str]
    content: Optional[str]
    author: Optional[str]
    author_url: Optional[str]
    url: str
    raw_data: Dict[Any, Any]
    fetched_at: datetime
    content_hash: Optional[str] = None


class BaseCrawler(ABC):
    platform: str

    # AI 关键词权重配置 - 权重越高表示与 Agent/AI 相关性越强
    AI_KEYWORD_WEIGHTS: Dict[str, int] = {
        # Agent 核心词（最高权重）
        'agent': 10,
        'agents': 10,
        'multi-agent': 10,
        'autonomous agent': 10,
        'ai agent': 10,
        '智能体': 10,
        'ai智能体': 10,
        '自主智能体': 10,
        '多智能体': 9,
        'ai代理': 8,
        '自主代理': 8,

        # 框架/平台（高权重）
        'langchain': 9,
        'langgraph': 9,
        'autogen': 9,
        'crewai': 9,
        'dify': 7,
        'coze': 7,
        'n8n': 6,
        'flowise': 7,
        'fastgpt': 7,
        'maxkb': 6,
        'openwebui': 7,
        'swarm': 8,
        'llama-index': 8,

        # 能力/技术（中高权重）
        'function calling': 8,
        'tool use': 8,
        'tool calling': 8,
        'planning': 6,
        'reasoning': 6,
        'orchestration': 7,
        'workflow': 5,
        'pipeline': 5,
        'automation': 4,

        # 记忆/上下文（中等权重）
        'memory': 5,
        'context': 4,
        'state management': 5,
        '长期记忆': 5,
        '短期记忆': 5,

        # RAG/MCP（高权重）
        'rag': 8,
        'retrieval': 6,
        'knowledge base': 6,
        'vector search': 6,
        'mcp': 9,
        'model context protocol': 9,

        # LLM/大模型（中高权重）
        'llm': 7,
        '大模型': 7,
        'gpt': 6,
        'claude': 6,
        'chatgpt': 6,
        'o1': 6,
        'o3': 6,
        'gpt-4': 6,
        'gpt-4o': 6,
        'gpt-3.5': 5,
        '文心一言': 5,
        '通义千问': 5,
        '智谱': 5,
        'kimi': 5,
        'deepseek': 6,
        'qwen': 5,

        # 其他 AI 相关（中等权重）
        'ai': 3,
        'artificial intelligence': 3,
        '人工智能': 3,
        '机器学习': 4,
        '深度学习': 4,
        '神经网络': 4,
        'nlp': 4,
        '自然语言处理': 4,
        'computer vision': 4,
        '计算机视觉': 4,
        '多模态': 5,
        'multimodal': 5,
        'generative ai': 5,
        '生成式': 4,
        'embedding': 5,
        '向量': 4,

        # Prompt/微调（中等权重）
        'prompt engineering': 5,
        'prompt': 3,
        'fine-tune': 4,
        '微调': 4,
        'rlhf': 5,

        # 其他相关框架
        'stable diffusion': 5,
        'midjourney': 4,
        'dall-e': 4,
        'openai': 4,
        'anthropic': 4,
        'transformer': 5,
    }

    # 相关性评分阈值，超过此值视为 AI 相关内容
    SCORE_THRESHOLD = 15

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    async def fetch(self, **kwargs) -> List[CrawlResult]:
        pass

    @abstractmethod
    async def login(self, credentials: Dict[str, str]) -> bool:
        pass

    def score_ai_relevance(self, text: str) -> int:
        """计算文本与 AI 的相关性分数（0-100）

        遍历所有关键词，命中则累加对应权重。短词使用边界匹配避免误触。
        """
        if not text:
            return 0

        text_lower = text.lower()
        score = 0
        matched = set()

        # 按权重降序遍历，优先匹配高权重关键词
        sorted_keywords = sorted(
            self.AI_KEYWORD_WEIGHTS.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for keyword, weight in sorted_keywords:
            if keyword in matched:
                continue

            kw_lower = keyword.lower()

            # 短词（<=3 字符）使用边界匹配，避免匹配到普通单词中的片段
            if len(kw_lower) <= 3:
                pattern = rf'(^|\s|[^a-z]){re.escape(kw_lower)}($|\s|[^a-z])'
                if re.search(pattern, text_lower):
                    score += weight
                    matched.add(keyword)
            else:
                if kw_lower in text_lower:
                    score += weight
                    matched.add(keyword)

        return min(score, 100)

    def is_ai_related(self, text: str) -> bool:
        """检查文本是否与 AI 相关 - 基于权重评分"""
        return self.score_ai_relevance(text) >= self.SCORE_THRESHOLD

    def filter_ai_content(
        self,
        items: List[CrawlResult],
        min_score: Optional[int] = None
    ) -> List[CrawlResult]:
        """过滤 AI 相关内容，并按相关性分数降序排序

        Args:
            items: 待过滤的内容列表
            min_score: 最小相关性分数，默认使用 SCORE_THRESHOLD

        Returns:
            按相关性分数降序排列的过滤后列表
        """
        threshold = min_score if min_score is not None else self.SCORE_THRESHOLD
        scored_items = []

        for item in items:
            text = f"{item.title or ''} {item.content or ''}"
            score = self.score_ai_relevance(text)
            if score >= threshold:
                scored_items.append((score, item))

        # 按分数降序排序
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items]

    def compute_hash(self, content: str) -> str:
        """计算内容的 MD5 哈希，用于增量去重"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def random_delay(self, min_sec: float = 2.0, max_sec: float = 5.0):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    def random_sample(self, items: List[Any], k: int) -> List[Any]:
        """从列表中随机抽样（不重复）"""
        if not items:
            return []
        k = min(k, len(items))
        return random.sample(items, k)

    def weighted_random_sample(
        self,
        items: Dict[str, int],
        k: int
    ) -> List[str]:
        """按权重随机抽样（不重复）

        Args:
            items: 关键词到权重的映射字典
            k: 抽样数量

        Returns:
            按权重概率抽样的关键词列表
        """
        if not items:
            return []

        keys = list(items.keys())
        weights = list(items.values())
        k = min(k, len(keys))

        # 使用 weighted random sampling without replacement
        selected = []
        available_keys = keys.copy()
        available_weights = weights.copy()

        for _ in range(k):
            if not available_keys:
                break
            total = sum(available_weights)
            if total == 0:
                # 权重全为0时退化为均匀随机
                pick = random.choice(available_keys)
            else:
                pick = random.choices(available_keys, weights=available_weights, k=1)[0]

            selected.append(pick)
            idx = available_keys.index(pick)
            available_keys.pop(idx)
            available_weights.pop(idx)

        return selected

    def weighted_random_choice(self, items: Dict[str, int]) -> Optional[str]:
        """按权重随机选择一个元素"""
        if not items:
            return None
        keys = list(items.keys())
        weights = list(items.values())
        return random.choices(keys, weights=weights, k=1)[0]

    def random_choice(self, items: List[Any]) -> Any:
        """从列表中随机选择一个元素"""
        if not items:
            return None
        return random.choice(items)

    def random_shuffle(self, items: List[Any]) -> List[Any]:
        """随机打乱列表顺序"""
        shuffled = items.copy()
        random.shuffle(shuffled)
        return shuffled

    def random_offset(self, min_val: int = 0, max_val: int = 20) -> int:
        """生成随机偏移量，用于分页获取不同位置的内容"""
        return random.randint(min_val, max_val)

    @staticmethod
    def clean_html(html_content: str) -> str:
        """清理HTML标签，返回纯文本

        Args:
            html_content: 包含HTML标签的字符串

        Returns:
            清理后的纯文本
        """
        if not html_content:
            return ""

        # 1. 将 <br>, <br/>, <br /> 替换为换行
        text = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)

        # 2. 将 <p>, <div> 等块级标签结束符替换为换行
        text = re.sub(r'</(p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)

        # 3. 解码常见HTML entities（先解码，再移除标签）
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&#34;', '"')
        text = text.replace('&#38;', '&')
        text = text.replace('&#60;', '<')
        text = text.replace('&#62;', '>')

        # 4. 移除所有HTML标签（包括解码后产生的标签）
        text = re.sub(r'<[^>]+>', '', text)

        # 5. 清理多余空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()
