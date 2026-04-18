import logging
import os
import re
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import get_settings

router = APIRouter(prefix="/api/config", tags=["config"])
logger = logging.getLogger(__name__)


def update_env_file(key: str, value: str) -> bool:
    """更新 .env 文件中的配置项"""
    try:
        # 查找 .env 文件
        env_paths = [
            Path(".env"),
            Path("../.env"),
            Path("backend/.env"),
            Path("../backend/.env"),
        ]

        env_file = None
        for path in env_paths:
            if path.exists():
                env_file = path
                break

        if not env_file:
            # 创建新的 .env 文件
            env_file = Path(".env")
            env_file.touch()

        # 读取现有内容
        content = env_file.read_text(encoding="utf-8")

        # 处理 value 中的特殊字符
        if value and (" " in value or "#" in value or "\"" in value):
            value = f'"{value}"'

        # 查找并替换或添加配置项
        pattern = rf"^{key}\s*=.*$"
        if re.search(pattern, content, re.MULTILINE):
            # 更新现有配置
            new_content = re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
        else:
            # 添加新配置
            new_content = content.rstrip() + f"\n{key}={value}\n"

        # 写入文件
        env_file.write_text(new_content, encoding="utf-8")
        logger.info(f"Updated .env file: {key}")
        return True
    except Exception as e:
        logger.error(f"Failed to update .env file: {e}")
        return False


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str


class ProviderInfo(BaseModel):
    id: str
    name: str
    models: List[ModelInfo]
    default_model: str


class ConfigResponse(BaseModel):
    default_ai_provider: str
    default_ai_model: str  # 格式: "provider:model"
    openai_api_key: str
    deepseek_api_key: str
    kimi_api_key: str
    kimi_coding_api_key: str
    glm_api_key: str
    minimax_api_key: str
    anthropic_api_key: str
    # 各供应商的模型选择
    openai_model: str
    claude_model: str
    deepseek_model: str
    glm_model: str
    kimi_model: str
    kimi_coding_model: str
    minimax_model: str
    database_url: str
    email_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_to: str
    crawl_schedule: str
    summarize_schedule: str
    email_schedule: str
    timezone: str
    log_level: str


class ConfigUpdate(BaseModel):
    default_ai_provider: Optional[str] = None
    default_ai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    kimi_api_key: Optional[str] = None
    kimi_coding_api_key: Optional[str] = None
    glm_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    # 各供应商的模型选择
    openai_model: Optional[str] = None
    claude_model: Optional[str] = None
    deepseek_model: Optional[str] = None
    glm_model: Optional[str] = None
    kimi_model: Optional[str] = None
    kimi_coding_model: Optional[str] = None
    minimax_model: Optional[str] = None
    email_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_to: Optional[str] = None
    crawl_schedule: Optional[str] = None
    summarize_schedule: Optional[str] = None
    email_schedule: Optional[str] = None
    timezone: Optional[str] = None
    log_level: Optional[str] = None


@router.get("/providers", response_model=List[ProviderInfo])
async def get_providers():
    """获取所有可用的 LLM 供应商及其模型列表"""
    from summarizer.llm_client import LLMClient

    providers = []
    for provider_id in LLMClient.PROVIDER_CONFIGS.keys():
        models = LLMClient.PROVIDER_MODELS.get(provider_id, [])
        providers.append(ProviderInfo(
            id=provider_id,
            name=LLMClient.PROVIDER_NAMES.get(provider_id, provider_id),
            models=[ModelInfo(**m) for m in models],
            default_model=LLMClient.DEFAULT_MODELS.get(provider_id, '')
        ))
    return providers


@router.get("/models/{provider}", response_model=List[ModelInfo])
async def get_provider_models(provider: str):
    """获取指定供应商的模型列表"""
    from summarizer.llm_client import LLMClient

    if provider not in LLMClient.PROVIDER_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    models = LLMClient.PROVIDER_MODELS.get(provider, [])
    return [ModelInfo(**m) for m in models]


@router.get("/", response_model=ConfigResponse)
async def get_config():
    """获取当前配置（隐藏敏感信息）"""
    logger.info("[Config API] Getting configuration")
    settings = get_settings()

    def mask_key(key: str) -> str:
        if not key:
            return ""
        if len(key) <= 8:
            return "****"
        return key[:4] + "****" + key[-4:]

    # 获取默认供应商和模型
    default_provider, default_model = settings.get_default_provider_and_model()
    default_ai_model = f"{default_provider}:{default_model}"

    # 获取各供应商的模型配置
    def get_model_or_default(provider: str) -> str:
        model = settings.get_provider_model(provider)
        if model == 'unknown':
            from summarizer.llm_client import LLMClient
            return LLMClient.DEFAULT_MODELS.get(provider, '')
        return model

    result = ConfigResponse(
        default_ai_provider=settings.default_ai_provider,
        default_ai_model=default_ai_model,
        openai_api_key=mask_key(settings.openai_api_key),
        deepseek_api_key=mask_key(settings.deepseek_api_key),
        kimi_api_key=mask_key(settings.kimi_api_key),
        kimi_coding_api_key=mask_key(settings.kimi_coding_api_key),
        glm_api_key=mask_key(settings.glm_api_key),
        minimax_api_key=mask_key(settings.minimax_api_key),
        anthropic_api_key=mask_key(settings.anthropic_api_key),
        openai_model=get_model_or_default('openai'),
        claude_model=get_model_or_default('claude'),
        deepseek_model=get_model_or_default('deepseek'),
        glm_model=get_model_or_default('glm'),
        kimi_model=get_model_or_default('kimi'),
        kimi_coding_model=get_model_or_default('kimi-coding'),
        minimax_model=get_model_or_default('minimax'),
        database_url=settings.database_url.split("?")[0] if "?" in settings.database_url else settings.database_url,
        email_enabled=settings.email_enabled,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password="",
        email_to=settings.email_to,
        crawl_schedule=settings.crawl_schedule,
        summarize_schedule=settings.summarize_schedule,
        email_schedule=settings.email_schedule,
        timezone=settings.timezone,
        log_level=settings.log_level,
    )
    logger.info(f"[Config API] Returning config: provider={result.default_ai_provider}, model={result.default_ai_model}")
    return result


@router.put("/", response_model=dict)
async def update_config(config: ConfigUpdate):
    """
    更新配置
    同时更新内存中的配置和 .env 文件以实现持久化
    """
    logger.info("Updating configuration via API")
    settings = get_settings()

    update_data = config.model_dump(exclude_unset=True)
    updated_keys = list(update_data.keys())
    logger.info(f"[Config API] Updating config keys: {updated_keys}")
    updated_keys = []
    failed_keys = []

    for key, value in update_data.items():
        if hasattr(settings, key) and value is not None:
            # Don't overwrite with masked values
            if isinstance(value, str) and "****" in value:
                continue

            # 更新内存中的配置
            setattr(settings, key, value)
            updated_keys.append(key)

            # 持久化到 .env 文件
            if not update_env_file(key, str(value) if value is not None else ""):
                failed_keys.append(key)

    if failed_keys:
        logger.warning(f"Failed to persist some configs to .env: {failed_keys}")

    return {
        "status": "success" if not failed_keys else "partial",
        "message": f"Configuration updated: {', '.join(updated_keys)}",
        "persisted": len(failed_keys) == 0,
        "failed_persist": failed_keys if failed_keys else None
    }


@router.post("/test-email")
async def test_email():
    """立即发送今日摘要邮件"""
    from notifier.email_sender import send_daily_digest

    try:
        await send_daily_digest(force=True)
        return {"status": "success", "message": "今日摘要邮件已发送"}
    except Exception as e:
        logger.exception(f"Failed to send daily digest: {e}")
        raise HTTPException(status_code=500, detail=f"发送今日摘要邮件失败: {str(e)}")
