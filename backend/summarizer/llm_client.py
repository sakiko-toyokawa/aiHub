import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import litellm
from dotenv import load_dotenv

# Load .env file
load_dotenv()

litellm.set_verbose = False
logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    summary_text: str
    key_points: List[str]
    tags: List[str]
    importance: int  # 1-5
    model_used: str
    provider: str
    tokens_used: int


class LLMClient:
    # 供应商基础配置（不含默认模型）
    # 结构: provider_id: {litellm_provider, api_base, api_key_env}
    PROVIDER_CONFIGS = {
        'openai': {'litellm_provider': 'openai', 'api_base': None, 'api_key_env': 'OPENAI_API_KEY'},
        'claude': {'litellm_provider': 'anthropic', 'api_base': None, 'api_key_env': 'ANTHROPIC_API_KEY'},
        'deepseek': {'litellm_provider': 'deepseek', 'api_base': 'https://api.deepseek.com/v1', 'api_key_env': 'DEEPSEEK_API_KEY'},
        'glm': {'litellm_provider': 'openai', 'api_base': 'https://open.bigmodel.cn/api/paas/v4', 'api_key_env': 'GLM_API_KEY'},
        'kimi': {'litellm_provider': 'openai', 'api_base': 'https://api.moonshot.cn/v1', 'api_key_env': 'KIMI_API_KEY'},
        'kimi-coding': {'litellm_provider': 'anthropic', 'api_base': 'https://api.kimi.com/coding/', 'api_key_env': 'KIMI_CODING_API_KEY'},
        'minimax': {'litellm_provider': 'minimax', 'api_base': 'https://api.minimax.chat/v1', 'api_key_env': 'MINIMAX_API_KEY'}
    }

    # 各供应商支持的模型列表
    PROVIDER_MODELS = {
        'openai': [
            {'id': 'gpt-4o', 'name': 'GPT-4o', 'description': '最强大的多模态模型'},
            {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini', 'description': '快速、便宜的日常任务'},
            {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'description': '长上下文，复杂任务'},
            {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'description': '经济实惠'},
        ],
        'claude': [
            {'id': 'claude-3-5-sonnet-20241022', 'name': 'Claude 3.5 Sonnet', 'description': '最佳性价比'},
            {'id': 'claude-3-5-haiku-20241022', 'name': 'Claude 3.5 Haiku', 'description': '快速响应'},
            {'id': 'claude-3-opus-20240229', 'name': 'Claude 3 Opus', 'description': '最强推理能力'},
            {'id': 'claude-3-sonnet-20240229', 'name': 'Claude 3 Sonnet', 'description': '平衡选择'},
            {'id': 'claude-3-haiku-20240307', 'name': 'Claude 3 Haiku', 'description': '最快速度（旧版）'},
        ],
        'deepseek': [
            {'id': 'deepseek-chat', 'name': 'DeepSeek Chat', 'description': '通用对话'},
            {'id': 'deepseek-coder', 'name': 'DeepSeek Coder', 'description': '代码生成'},
            {'id': 'deepseek-reasoner', 'name': 'DeepSeek Reasoner', 'description': '推理能力'},
        ],
        'glm': [
            {'id': 'glm-4', 'name': 'GLM-4', 'description': '最新版，强大通用'},
            {'id': 'glm-4-air', 'name': 'GLM-4 Air', 'description': '快速响应'},
            {'id': 'glm-4-flash', 'name': 'GLM-4 Flash', 'description': '极速，免费'},
            {'id': 'glm-3-turbo', 'name': 'GLM-3 Turbo', 'description': '经济实惠'},
        ],
        'kimi': [
            {'id': 'kimi-k2.5', 'name': 'Kimi K2.5', 'description': '最新多模态'},
            {'id': 'kimi-k2', 'name': 'Kimi K2', 'description': '长上下文'},
            {'id': 'kimi-k1.5', 'name': 'Kimi K1.5', 'description': '平衡选择'},
            {'id': 'moonshot-v1-8k', 'name': 'Moonshot V1 8K', 'description': '轻量级'},
        ],
        'kimi-coding': [
            {'id': 'kimi-for-coding', 'name': 'Kimi for Coding', 'description': '编程专用'},
        ],
        'minimax': [
            {'id': 'abab6.5-chat', 'name': 'abab6.5 Chat', 'description': '最新对话模型'},
            {'id': 'abab6-chat', 'name': 'abab6 Chat', 'description': '上一代模型'},
            {'id': 'abab5.5-chat', 'name': 'abab5.5 Chat', 'description': '轻量级'},
        ]
    }

    # 默认模型映射（向后兼容）
    DEFAULT_MODELS = {
        'openai': 'gpt-4o-mini',
        'claude': 'claude-3-5-haiku-20241022',
        'deepseek': 'deepseek-chat',
        'glm': 'glm-4',
        'kimi': 'kimi-k2.5',
        'kimi-coding': 'kimi-for-coding',
        'minimax': 'abab6.5-chat'
    }

    # 供应商显示名称
    PROVIDER_NAMES = {
        'openai': 'OpenAI',
        'claude': 'Claude',
        'deepseek': 'DeepSeek',
        'glm': 'GLM',
        'kimi': 'Kimi',
        'kimi-coding': 'Kimi Coding',
        'minimax': 'MiniMax'
    }

    def __init__(self, provider: str = 'openai', model: Optional[str] = None):
        """
        初始化 LLM 客户端

        Args:
            provider: 供应商 ID（如 'openai', 'claude'）
            model: 模型名称（可选，默认使用供应商的默认模型）
        """
        if provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(self.PROVIDER_CONFIGS.keys())}")

        self.provider = provider
        config = self.PROVIDER_CONFIGS[provider]
        self.litellm_provider = config['litellm_provider']
        self.api_base = config['api_base']
        self.api_key_env = config['api_key_env']

        # 如果未指定模型，使用默认模型
        self.model = model or self.DEFAULT_MODELS.get(provider, 'unknown')

    def _get_api_key(self) -> Optional[str]:
        """获取 API Key"""
        return os.environ.get(self.api_key_env)

    @classmethod
    def get_available_models(cls, provider: str) -> List[Dict[str, str]]:
        """获取指定供应商的可用模型列表"""
        return cls.PROVIDER_MODELS.get(provider, [])

    @classmethod
    def get_all_providers(cls) -> List[Dict[str, Any]]:
        """获取所有供应商信息"""
        providers = []
        for provider_id, config in cls.PROVIDER_CONFIGS.items():
            models = cls.PROVIDER_MODELS.get(provider_id, [])
            providers.append({
                'id': provider_id,
                'name': cls.PROVIDER_NAMES.get(provider_id, provider_id),
                'models': models,
                'default_model': cls.DEFAULT_MODELS.get(provider_id)
            })
        return providers

    @classmethod
    def get_default_model(cls, provider: str) -> str:
        """获取供应商的默认模型"""
        return cls.DEFAULT_MODELS.get(provider, 'unknown')

    @classmethod
    def validate_model(cls, provider: str, model: str) -> bool:
        """验证模型是否属于指定供应商"""
        if provider not in cls.PROVIDER_CONFIGS:
            return False
        available_models = cls.PROVIDER_MODELS.get(provider, [])
        return any(m['id'] == model for m in available_models)

    async def summarize(self, content: str, title: str = "", url: str = "") -> SummaryResult:
        prompt = self._build_prompt(content, title, url)

        # 构建请求参数
        completion_params = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }

        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(f"Missing API key for {self.provider}. Please set {self.api_key_env} in .env file.")

        # 使用 LiteLLM 标准格式：provider/model
        completion_params["model"] = f"{self.litellm_provider}/{self.model}"
        completion_params["api_key"] = api_key
        if self.api_base:
            completion_params["api_base"] = self.api_base

        response = await litellm.acompletion(**completion_params)
        result_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        parsed = self._parse_result(result_text)

        # 在总结末尾添加原文链接
        summary = parsed.get('summary', result_text[:500])
        if url and '原文链接' not in summary:
            summary = f"{summary}\n\n📎 [原文链接]({url})"

        return SummaryResult(
            summary_text=summary,
            key_points=parsed.get('key_points', []),
            tags=parsed.get('tags', []),
            importance=parsed.get('importance', 3),
            model_used=self.model,
            provider=self.provider,
            tokens_used=tokens_used
        )

    def _build_prompt(self, content: str, title: str, url: str = "") -> str:
        url_section = f"\n原文链接: {url}" if url else ""
        return f"""请总结以下内容，提取关键信息：

标题: {title}
内容: {content[:8000]}{url_section}

请按以下格式返回（使用中文）：

## 核心主题
（一句话概括内容主旨）

## 关键要点
- 要点1
- 要点2
- 要点3
- 要点4
- 要点5

## 相关技术/工具
- 技术1
- 技术2

## 重要性评估
星级: X/5

## 标签
tag1, tag2, tag3, tag4, tag5

## 原文链接
{url if url else '无'}
"""

    def _parse_result(self, text: str) -> Dict:
        result = {'summary': '', 'key_points': [], 'tags': [], 'importance': 3}
        lines = text.split('\n')
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('## 核心主题'):
                current_section = 'summary'
            elif line.startswith('## 关键要点'):
                current_section = 'key_points'
            elif line.startswith('## 相关技术/工具'):
                current_section = 'tech'
            elif line.startswith('## 重要性评估'):
                current_section = 'importance'
            elif line.startswith('## 标签'):
                current_section = 'tags'
            elif line.startswith('- ') and current_section == 'key_points':
                result['key_points'].append(line[2:])
            elif line.startswith('- ') and current_section == 'tech':
                if 'tech' not in result:
                    result['tech'] = []
                result['tech'].append(line[2:])
            elif current_section == 'summary' and line and not line.startswith('#'):
                result['summary'] = line
            elif current_section == 'tags' and ',' in line:
                result['tags'] = [t.strip() for t in line.split(',')]
            elif current_section == 'importance' and '星级:' in line:
                try:
                    importance = int(line.split(':')[1].strip().split('/')[0])
                    result['importance'] = max(1, min(5, importance))
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse importance from '{line}': {e}")
        return result

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        """通用对话接口，用于 Agent 命令解析等场景

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 采样温度
            max_tokens: 最大生成 token 数

        Returns:
            LLM 生成的文本响应
        """
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(f"Missing API key for {self.provider}. Please set {self.api_key_env} in .env file.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        completion_params = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": f"{self.litellm_provider}/{self.model}",
            "api_key": api_key,
        }
        if self.api_base:
            completion_params["api_base"] = self.api_base

        try:
            response = await litellm.acompletion(**completion_params)
            result_text = response.choices[0].message.content
            logger.info(f"Chat response generated using {self.provider}")
            return result_text or ""
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def generate_title(self, content: str, max_length: int = 50) -> str:
        """基于内容生成标题

        Args:
            content: 内容文本
            max_length: 标题最大长度（默认50字符）

        Returns:
            生成的标题
        """
        if not content or len(content.strip()) < 10:
            return "无标题"

        prompt = f"""请为以下内容生成一个简洁准确的标题（不超过{max_length}字符）：

内容：{content[:500]}

要求：
- 概括内容核心主题
- 简洁明了，不要包含无关信息
- 直接返回标题文本，不要添加解释或引号

标题："""

        api_key = self._get_api_key()
        if not api_key:
            logger.warning(f"Missing API key for {self.provider}, cannot generate title")
            return "无标题"

        completion_params = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 100,
            "model": f"{self.litellm_provider}/{self.model}",
            "api_key": api_key,
        }
        if self.api_base:
            completion_params["api_base"] = self.api_base

        try:
            response = await litellm.acompletion(**completion_params)
            title = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0

            # 移除可能的引号
            title = title.strip('"\'')

            # 截断到最大长度
            if len(title) > max_length:
                title = title[:max_length-3] + "..."

            logger.info(f"Generated title: '{title}' using {self.provider} (tokens: {tokens_used})")
            return title or "无标题"
        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            return "无标题"
