"""
初始化示例数据脚本
在首次启动时运行，创建示例数据用于演示
"""

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Source, RawContent, Summary, UserRead


# 内置平台配置：不需要凭证的源默认启用，需要凭证的源默认停用（等用户配置）
BUILTIN_SOURCES = [
    {"platform": "github", "name": "GitHub Trending", "url_pattern": "https://github.com/trending", "needs_auth": True},
    {"platform": "zhihu", "name": "知乎 AI 话题", "url_pattern": "https://www.zhihu.com/topic/19550228/hot", "needs_auth": True},
    {"platform": "bilibili", "name": "B站科技区", "url_pattern": "https://www.bilibili.com/v/tech", "needs_auth": True},
    {"platform": "anthropic", "name": "Anthropic Blog", "url_pattern": "https://www.anthropic.com/news", "needs_auth": False},
    {"platform": "builderio", "name": "Builder.io Blog", "url_pattern": "https://www.builder.io/blog", "needs_auth": False},
    {"platform": "hackernews", "name": "Hacker News", "url_pattern": "https://news.ycombinator.com", "needs_auth": False},
]


def _ensure_builtin_sources(db):
    """确保所有内置平台在 sources 表中都有记录（get_or_create）"""
    import os

    def _has_auth(platform: str) -> bool:
        if platform == "github":
            return bool(os.getenv("GITHUB_TOKEN"))
        if platform == "zhihu":
            return bool(os.getenv("ZHIHU_COOKIE"))
        if platform == "bilibili":
            return bool(os.getenv("BILIBILI_SESSDATA"))
        return True

    created = 0
    for cfg in BUILTIN_SOURCES:
        existing = db.query(Source).filter(Source.platform == cfg["platform"]).first()
        if existing:
            continue
        should_active = _has_auth(cfg["platform"]) if cfg["needs_auth"] else True
        db.add(Source(
            platform=cfg["platform"],
            name=cfg["name"],
            url_pattern=cfg["url_pattern"],
            is_active=should_active,
            config={},
        ))
        created += 1
    if created:
        db.commit()
        print(f"   + Created {created} builtin sources")


def init_sample_data():
    """初始化示例数据"""
    db = SessionLocal()

    try:
        # 1. 始终确保内置源存在（get_or_create，不会重复创建）
        print("Ensuring builtin sources...")
        _ensure_builtin_sources(db)

        # 2. 检查是否已有内容数据
        existing = db.query(RawContent).first()
        if existing:
            print("Database already has content data, skipping sample content")
            return

        print("Initializing sample data...")

        # 2. 创建示例原始内容
        raw_contents = [
            RawContent(
                source_id=1,
                platform="github",
                external_id="repo_1",
                title="awesome-mcp-servers: 精选 MCP 服务器集合",
                content="这个仓库收集了各种 Model Context Protocol (MCP) 服务器的实现，包括文件系统、数据库、API 集成等。MCP 是 Anthropic 推出的开放协议，用于标准化 AI 助手与外部数据源的连接方式。支持 50+ 种不同的 MCP 服务器实现，包含官方和社区的实现示例。",
                author="anthropic-community",
                author_url="https://github.com/anthropic-community",
                url="https://github.com/example/awesome-mcp-servers",
                raw_data={"stars": 1200, "language": "Python"},
                fetched_at=datetime.now()
            ),
            RawContent(
                source_id=2,
                platform="zhihu",
                external_id="zhihu_1",
                title="RAG 实践避坑指南：从理论到落地",
                content="本文分享了在实际项目中使用 RAG (检索增强生成) 的经验和教训，包括向量数据库选型、分块策略、重排序等关键环节的最佳实践。向量数据库选型要考虑延迟和召回率的平衡，文本分块大小对检索质量影响巨大。",
                author="AI实践者",
                author_url="https://www.zhihu.com/people/ai-practitioner",
                url="https://zhihu.com/question/1234567890",
                raw_data={"votes": 850},
                fetched_at=datetime.now()
            ),
            RawContent(
                source_id=3,
                platform="bilibili",
                external_id="bili_1",
                title="从零开始训练自己的大语言模型",
                content="UP 主详细介绍了如何使用 LoRA 和 QLoRA 技术微调大语言模型，包括环境配置、数据准备、训练流程和模型部署的完整流程。LoRA 可以大幅减少训练显存需求，数据质量比数据量更重要。",
                author="AI教程君",
                author_url="https://space.bilibili.com/123456",
                url="https://www.bilibili.com/video/BV1xxxxxx",
                raw_data={"views": 50000, "likes": 3000},
                fetched_at=datetime.now()
            ),
            RawContent(
                source_id=1,
                platform="github",
                external_id="repo_2",
                title="llama.cpp: 在本地运行 LLM 的C++实现",
                content="llama.cpp 是一个用 C++ 编写的高性能 LLM 推理库，支持在各种硬件上高效运行大语言模型，包括 CPU、GPU 和移动设备。纯 C/C++ 实现，无依赖，易于部署，支持 GGUF 格式模型量化。",
                author="ggerganov",
                author_url="https://github.com/ggerganov",
                url="https://github.com/ggerganov/llama.cpp",
                raw_data={"stars": 45000, "language": "C++"},
                fetched_at=datetime.now()
            ),
            RawContent(
                source_id=2,
                platform="zhihu",
                external_id="zhihu_2",
                title="ChatGPT vs Claude: 深度对比评测",
                content="详细对比了 ChatGPT 和 Claude 在不同任务上的表现，包括代码生成、逻辑推理、创意写作等方面。Claude 在长文本处理上有优势，ChatGPT 在代码生成上表现更好。",
                author="AI测评师",
                author_url="https://www.zhihu.com/people/ai-tester",
                url="https://zhihu.com/question/0987654321",
                raw_data={"votes": 1200},
                fetched_at=datetime.now()
            ),
        ]

        for content in raw_contents:
            db.add(content)
        db.commit()

        # 3. 创建示例总结
        summaries = [
            Summary(
                raw_content_id=1,
                summary_text="MCP (Model Context Protocol) 是 Anthropic 推出的开放协议，用于标准化 AI 助手与外部数据源的连接。awesome-mcp-servers 仓库收集了 50+ 种 MCP 服务器实现，包括文件系统、数据库、Git 等常用工具的集成示例。",
                key_points=[
                    "MCP 协议标准化 AI 与外部数据连接",
                    "支持 50+ 种服务器实现",
                    "涵盖文件系统、数据库、Git 等工具",
                    "提供详细配置和使用文档"
                ],
                tags=["MCP", "AI", "开源", "工具", "Anthropic"],
                ai_model="gpt-4o-mini",
                ai_provider="openai",
                tokens_used=450,
                generated_at=datetime.now()
            ),
            Summary(
                raw_content_id=2,
                summary_text="RAG (检索增强生成) 实践指南，分享了向量数据库选型、文本分块策略、重排序等关键环节的最佳实践。强调数据质量和分块大小对最终效果的影响。",
                key_points=[
                    "向量数据库要平衡延迟和召回率",
                    "文本分块大小对质量影响巨大",
                    "重排序模型能显著提升效果",
                    "需要建立完整的评估体系"
                ],
                tags=["RAG", "LLM", "向量数据库", "实践"],
                ai_model="claude-3-haiku",
                ai_provider="claude",
                tokens_used=380,
                generated_at=datetime.now()
            ),
            Summary(
                raw_content_id=3,
                summary_text="详细介绍使用 LoRA 和 QLoRA 技术微调大语言模型的完整流程，包括环境配置、数据准备、训练流程和模型部署。强调 LoRA 可以大幅减少显存需求。",
                key_points=[
                    "LoRA 技术减少训练显存需求",
                    "数据质量比数据量更重要",
                    "学习率调度影响训练效果",
                    "模型合并和量化部署技巧"
                ],
                tags=["LLM", "微调", "LoRA", "教程"],
                ai_model="deepseek-chat",
                ai_provider="deepseek",
                tokens_used=520,
                generated_at=datetime.now()
            ),
            Summary(
                raw_content_id=4,
                summary_text="llama.cpp 是高性能 LLM 推理库，用纯 C/C++ 实现，支持在各种硬件上运行大语言模型。特点是零依赖、易于部署，支持 GGUF 量化格式。",
                key_points=[
                    "纯 C/C++ 实现，零依赖",
                    "支持 CPU/GPU/移动设备",
                    "支持 GGUF 格式量化",
                    "跨平台：Windows/Linux/macOS"
                ],
                tags=["LLM", "C++", "本地部署", "开源"],
                ai_model="gpt-4o-mini",
                ai_provider="openai",
                tokens_used=410,
                generated_at=datetime.now()
            ),
            Summary(
                raw_content_id=5,
                summary_text="ChatGPT 与 Claude 的深度对比评测，覆盖代码生成、逻辑推理、创意写作等多个维度。Claude 在长文本处理上占优，ChatGPT 在代码生成方面更强。",
                key_points=[
                    "Claude 长文本处理更强",
                    "ChatGPT 代码生成更优",
                    "两者在创意写作上各有特色",
                    "选型应根据具体使用场景"
                ],
                tags=["ChatGPT", "Claude", "对比", "评测"],
                ai_model="claude-3-haiku",
                ai_provider="claude",
                tokens_used=390,
                generated_at=datetime.now()
            ),
        ]

        for summary in summaries:
            db.add(summary)
        db.commit()

        # 4. 创建示例阅读记录（部分标记为已读/收藏）
        user_reads = [
            UserRead(summary_id=2, is_read=True, read_at=datetime.now(), is_favorited=True),
            UserRead(summary_id=4, is_read=True, read_at=datetime.now()),
        ]

        for read in user_reads:
            db.add(read)
        db.commit()

        print(f"✅ Sample data initialized successfully!")
        print(f"   - {len(sources)} sources")
        print(f"   - {len(raw_contents)} raw contents")
        print(f"   - {len(summaries)} summaries")
        print(f"   - {len(user_reads)} user reads")

    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_sample_data()
