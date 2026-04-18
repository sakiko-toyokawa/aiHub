from typing import Tuple, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file on module import
load_dotenv()


class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost:5432/ai_knowledge"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    glm_api_key: str = ""
    kimi_api_key: str = ""
    kimi_coding_api_key: str = ""
    minimax_api_key: str = ""

    # AI 模型配置
    default_ai_provider: str = "openai"
    default_ai_model: str = ""  # 格式: "provider:model" 如 "claude:claude-3-5-sonnet-20241022"

    # 各供应商的模型选择（覆盖默认）
    openai_model: str = ""
    claude_model: str = ""
    deepseek_model: str = ""
    glm_model: str = ""
    kimi_model: str = ""
    kimi_coding_model: str = ""
    minimax_model: str = ""

    zhihu_cookie: str = ""
    bilibili_sessdata: str = ""
    github_token: str = ""
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_to: str = ""
    email_enabled: bool = False
    crawl_schedule: str = "0 */2 * * *"
    summarize_schedule: str = "0 */3 * * *"
    email_schedule: str = "0 22 * * *"
    log_level: str = "INFO"
    timezone: str = "Asia/Shanghai"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_provider_model(self, provider: str) -> str:
        """获取指定供应商配置的模型，如果没有则返回默认模型"""
        from summarizer.llm_client import LLMClient

        # 检查是否有特定配置
        model_attr = f"{provider}_model"
        if hasattr(self, model_attr):
            model = getattr(self, model_attr)
            if model:
                return model

        # 返回默认模型
        return LLMClient.DEFAULT_MODELS.get(provider, 'unknown')

    def get_default_provider_and_model(self) -> Tuple[str, str]:
        """获取默认的供应商和模型

        优先级：
        1. default_ai_model (格式: "provider:model")
        2. default_ai_provider + 该供应商的默认模型
        """
        from summarizer.llm_client import LLMClient

        # 如果配置了 default_ai_model，解析它
        if self.default_ai_model and ":" in self.default_ai_model:
            parts = self.default_ai_model.split(":", 1)
            if len(parts) == 2:
                provider, model = parts
                if provider in LLMClient.PROVIDER_CONFIGS:
                    return provider, model

        # 向后兼容：使用 default_ai_provider
        provider = self.default_ai_provider
        if provider not in LLMClient.PROVIDER_CONFIGS:
            provider = "openai"

        # 获取该供应商的模型配置
        model = self.get_provider_model(provider)
        return provider, model


@lru_cache()
def get_settings() -> Settings:
    return Settings()
