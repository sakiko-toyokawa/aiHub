import json
import logging
import re
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from summarizer.llm_client import LLMClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


class ParseRequest(BaseModel):
    command: str


class AgentAction(BaseModel):
    type: str
    params: Dict[str, Any] = {}
    message: str = ""


class ParseResponse(BaseModel):
    action: AgentAction


# Agent 系统提示词
# 设计决策：
# 1. 明确列出所有支持的 action type，让 LLM 输出结构化 JSON，
#    而不是自由文本，这样前端可以直接 switch case 执行，无需二次 NLP。
# 2. params 尽量使用简单标量（int/str/bool），避免嵌套对象，
#    降低前后端类型对齐成本。
# 3. 对于无法识别的命令，统一返回 unknown action，并附带友好提示，
#    让前端给用户明确的反馈。
AGENT_SYSTEM_PROMPT = """你是一个 AI 命令解析助手。请将用户的自然语言命令解析为结构化的 JSON action。

支持的 action type 列表：
- list_summaries: 列出摘要（可带 platform 筛选）
  params: { platform?: string, page?: int, page_size?: int }
- get_summary: 查看摘要详情
  params: { summary_id: int }
- mark_read: 标记摘要已读
  params: { summary_id: int | "latest" }
- toggle_favorite: 切换收藏状态
  params: { summary_id: int }
- delete_summary: 删除摘要
  params: { summary_id: int }
- cleanup: 清理旧摘要
  params: { keep_count: int }
- trigger_crawl: 触发爬虫
  params: { source_id?: int }
- get_crawl_status: 查看爬虫任务状态
  params: { task_id: string }
- list_tasks: 列出所有爬虫任务
  params: { page?: int, page_size?: int }
- list_sources: 列出所有数据源
  params: {}
- toggle_source_active: 切换数据源启用状态
  params: { source_id: int }
- get_stats: 查看统计数据
  params: {}
- get_trending_tags: 查看热门标签
  params: { limit?: int }
- get_config: 获取当前配置
  params: {}
- update_config: 更新配置项
  params: { key: string, value: any }
- test_email: 发送今日摘要
  params: {}
- get_providers: 查看 AI 提供商列表
  params: {}
- get_provider_models: 查看指定提供商模型
  params: { provider: string }
- navigate: 页面导航
  params: { path: string }
- unknown: 无法识别的命令
  params: {}

请严格按以下 JSON 格式返回，不要添加任何解释：
{
  "type": "<action_type>",
  "params": { ... },
  "message": "<给用户的友好提示>"
}

规则：
1. 如果用户说"查看/列出/显示" + "摘要/文章/内容" → list_summaries
2. 如果用户说"查看" + "第X条/ID为X" + "摘要" → get_summary，summary_id 尽量提取数字
3. 如果用户说"标记已读/已读" → mark_read；如果提到"第一条/最新一条"，summary_id 填 "latest"，不要填数字 1
4. 如果用户说"收藏/取消收藏" → toggle_favorite
5. 如果用户说"删除/移除" + "摘要" → delete_summary
6. 如果用户说"清理/删除旧" + "摘要" → cleanup，默认 keep_count=5
7. 如果用户说"抓取/爬虫/更新" → trigger_crawl
8. 如果用户说"任务状态/查看任务 xxx" → get_crawl_status，task_id 尽量提取用户提到的 ID
9. 如果用户说"列出所有任务/历史任务" → list_tasks
10. 如果用户说"数据源/来源/平台" + "列出/显示/查看" → list_sources
11. 如果用户明确提到"启用/暂停/切换"某个具体数据源 → toggle_source_active；source_id 尽量提取数字，若提到平台名称（如"知乎"）可将其作为 source_id 字符串返回；**如果完全提取不到任何具体数据源标识，则返回 unknown，不要瞎猜 toggle_source_active**
12. 如果用户说"统计/数据/概况" → get_stats
13. 如果用户说"热门标签/趋势标签/常用标签" → get_trending_tags，默认 limit=10
14. 如果用户说"查看配置/当前设置/系统设置" → get_config
15. 如果用户说"修改配置/更新设置/更改配置" + 具体 key 和 value → update_config；key 尽量提取明确的配置项名称（如 default_ai_model、email_enabled），value 尽量提取用户给定的值；**如果完全提取不到 key，则返回 unknown**
16. 如果用户说"发送今日摘要/发送邮件/手动发邮件" → test_email
17. 如果用户说"查看所有 AI 提供商/模型供应商/有哪些 AI 提供商" → get_providers
18. 如果用户说"查看 XX 有哪些模型/XX 的模型列表" → get_provider_models，provider 尽量提取用户提到的供应商名称（如 deepseek、openai、claude）
19. 如果用户说"去XX页/打开XX" → navigate，path 使用前端路由如 "/", "/favorites", "/settings"
20. 其他无法明确匹配的命令 → unknown，message 中给出建议
"""


@router.post("/parse", response_model=ParseResponse)
async def parse_command(request: ParseRequest):
    """解析用户自然语言命令为结构化 action"""
    try:
        settings = get_settings()
        provider, model = settings.get_default_provider_and_model()

        client = LLMClient(provider=provider, model=model)
        response_text = await client.chat(
            system_prompt=AGENT_SYSTEM_PROMPT,
            user_message=request.command,
            temperature=0.1,
            max_tokens=500,
        )

        # 尝试从响应中提取 JSON 块
        # LLM 有时会包裹在 ```json ... ``` 中，需要清洗
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(text)

        action = AgentAction(
            type=parsed.get("type", "unknown"),
            params=parsed.get("params", {}),
            message=parsed.get("message", ""),
        )

        logger.info(f"Agent parsed command '{request.command}' -> {action.type}")
        return ParseResponse(action=action)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse agent response as JSON: {e}. Response: {response_text}")
        return ParseResponse(
            action=AgentAction(
                type="unknown",
                message="AI 解析结果格式异常，请尝试更明确的指令",
            )
        )
    except Exception as e:
        logger.exception(f"Agent parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 解析失败: {str(e)}")
