import os
import sys
import asyncio

# Windows: 必须先设置事件循环策略，再导入其他异步库
# 否则 Playwright 会报 NotImplementedError（ProactorEventLoop 不支持 subprocess）
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv

# 显式加载 .env 文件，确保配置在任何导入顺序下都可用
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    print(f"[scheduler] Loaded .env from: {env_path}")
else:
    print(f"[scheduler] .env file not found at: {env_path}")

# Verify key variables are loaded
if os.getenv('GITHUB_TOKEN'):
    print(f"[scheduler] GITHUB_TOKEN loaded: {os.getenv('GITHUB_TOKEN')[:15]}...")
else:
    print("[scheduler] WARNING: GITHUB_TOKEN not found in environment")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.exc import IntegrityError
from zoneinfo import ZoneInfo

scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)


def console_log(msg: str):
    """输出到控制台并强制刷新"""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

# 爬虫配置映射
CRAWLER_CONFIGS = {
    "github": {"token_env": "GITHUB_TOKEN", "use_token": False},
    "zhihu": {"cookie_env": "ZHIHU_COOKIE", "key": "cookie"},
    "bilibili": {"sessdata_env": "BILIBILI_SESSDATA", "key": "sessdata"},
}


def init_scheduler():
    """Initialize and start the scheduler"""
    from app.config import get_settings
    settings = get_settings()

    # 获取时区
    tz = ZoneInfo(settings.timezone)

    # Crawl job - every 2 hours
    scheduler.add_job(
        run_crawl_job,
        trigger=CronTrigger.from_crontab(settings.crawl_schedule, timezone=tz),
        id='crawl_job',
        replace_existing=True
    )

    # Summarize job - every 3 hours
    scheduler.add_job(
        run_summarize_job,
        trigger=CronTrigger.from_crontab(settings.summarize_schedule, timezone=tz),
        id='summarize_job',
        replace_existing=True
    )

    # Email job - daily at 10pm
    scheduler.add_job(
        run_email_job,
        trigger=CronTrigger.from_crontab(settings.email_schedule, timezone=tz),
        id='email_job',
        replace_existing=True
    )

    scheduler.start()
    return scheduler


def get_crawler_configs() -> Dict[str, Dict[str, Any]]:
    """Get all configured crawlers"""
    import os
    configs = {}

    # GitHub (optional token)
    github_token = os.getenv("GITHUB_TOKEN", "")
    configs["github"] = {"api_token": github_token} if github_token else {}

    # Zhihu (requires cookie)
    zhihu_cookie = os.getenv("ZHIHU_COOKIE", "")
    if zhihu_cookie:
        configs["zhihu"] = {"cookie": zhihu_cookie}

    # Bilibili (requires sessdata)
    bilibili_sessdata = os.getenv("BILIBILI_SESSDATA", "")
    if bilibili_sessdata:
        configs["bilibili"] = {"sessdata": bilibili_sessdata}

    # Anthropic (no auth)
    configs["anthropic"] = {}

    # Builder.io (no auth)
    configs["builderio"] = {}

    # Hacker News (no auth)
    configs["hackernews"] = {}

    return configs


async def run_crawl_job() -> List[Dict[str, Any]]:
    """Run crawl for all configured sources, returns list of newly saved items"""
    console_log("=" * 60)
    console_log("[CRAWL JOB] Starting crawl job...")
    logger.info("=" * 60)
    logger.info("[CRAWL JOB] Starting crawl job...")

    from crawler import get_crawler
    from app.database import SessionLocal
    from app.models import RawContent
    from summarizer.llm_client import LLMClient
    from app.config import get_settings
    from sqlalchemy import text

    configs = get_crawler_configs()
    newly_saved_items: List[Dict[str, Any]] = []

    # 创建LLMClient用于AI生成标题（可选）
    llm_client = None
    try:
        settings = get_settings()
        provider, model = settings.get_default_provider_and_model()
        llm_client = LLMClient(provider, model)
        logger.info(f"[CRAWL JOB] LLMClient 已创建，提供商: {provider}, 模型: {model}")
    except Exception as e:
        logger.warning(f"[CRAWL JOB] 无法创建LLMClient，标题生成将使用备用方案: {e}")

    if not configs:
        msg = "[CRAWL JOB] No crawlers configured. Please set platform credentials in .env"
        console_log(msg)
        logger.warning(msg)
        return newly_saved_items

    db = SessionLocal()
    total_crawled = 0

    # 检查 content_hash 列是否存在（兼容旧数据库）
    has_content_hash = False
    try:
        db.execute(text("SELECT content_hash FROM raw_contents LIMIT 1"))
        has_content_hash = True
    except Exception:
        logger.warning("[CRAWL JOB] content_hash 列不存在，跳过基于内容的增量去重（建议重建数据库）")

    def _save_results(results, crawler, label):
        nonlocal total_crawled
        saved_count = 0
        skipped_count = 0
        batch_seen: Set[Tuple[str, str]] = set()

        for result in results:
            key = (result.platform, result.external_id)
            if key in batch_seen:
                skipped_count += 1
                continue
            batch_seen.add(key)

            try:
                existing = db.query(RawContent).filter(
                    RawContent.platform == result.platform,
                    RawContent.external_id == result.external_id
                ).first()
                if existing:
                    skipped_count += 1
                    continue

                content_hash = ""
                if has_content_hash:
                    content_hash = crawler.compute_hash(
                        f"{result.title or ''}{result.content or ''}"
                    )
                    if content_hash:
                        hash_existing = db.query(RawContent).filter(
                            RawContent.content_hash == content_hash
                        ).first()
                        if hash_existing:
                            logger.info(
                                f"【抓取】{label} 内容哈希重复跳过: "
                                f"{result.external_id} (与 {hash_existing.platform} 重复)"
                            )
                            skipped_count += 1
                            continue

                raw_content = RawContent(
                    platform=result.platform,
                    external_id=result.external_id,
                    title=result.title,
                    content=result.content,
                    author=result.author,
                    author_url=result.author_url,
                    url=result.url,
                    raw_data=result.raw_data,
                    content_hash=content_hash if has_content_hash else None
                )
                db.add(raw_content)
                db.flush()
                saved_count += 1

                newly_saved_items.append({
                    "id": raw_content.id,
                    "platform": result.platform,
                    "external_id": result.external_id,
                    "title": result.title,
                    "url": result.url,
                    "author": result.author,
                })

            except IntegrityError as e:
                db.rollback()
                logger.warning(f"【抓取】{label} 数据重复跳过: {result.external_id}")
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"【抓取】保存 {label} 条目失败: {e}")
                continue

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            logger.error(f"【抓取】{label} 批量提交失败(存在重复数据): {e}")
        total_crawled += saved_count
        logger.info(f"【抓取】{label} 完成: 抓取 {len(results)} 条, 新增 {saved_count} 条, 跳过 {skipped_count} 条")

    try:
        # 1. 硬编码平台抓取
        for platform, config in configs.items():
            try:
                logger.info(f"【抓取】开始抓取平台: {platform}")
                crawler = get_crawler(platform, config, llm_client=llm_client)
                results = await crawler.fetch()

                if not results:
                    logger.warning(f"【抓取】{platform} 首次抓取未找到内容，触发扩展抓取...")
                    results = await crawler.fetch(expanded=True)
                    if results:
                        logger.info(f"【抓取】{platform} 扩展抓取成功，获取 {len(results)} 条")
                    else:
                        logger.warning(f"【抓取】{platform} 扩展抓取后仍无内容，跳过")
                        continue

                _save_results(results, crawler, platform)

                if platform != list(configs.keys())[-1]:
                    await asyncio.sleep(5)

            except Exception as e:
                logger.exception(f"【抓取】{platform} 抓取失败: {e}")
                continue

        # 2. RSS 源抓取
        try:
            from app.models import Source
            rss_sources = db.query(Source).filter(
                Source.platform == 'rss',
                Source.is_active == True
            ).all()
            logger.info(f"【抓取】发现 {len(rss_sources)} 个 RSS 源")

            for rss_source in rss_sources:
                try:
                    logger.info(
                        f"【抓取】RSS 源: {rss_source.name} ({rss_source.url_pattern}), "
                        f"增量: last_fetched_at={rss_source.last_fetched_at}, last_item_id={rss_source.last_item_id}"
                    )
                    crawler = get_crawler('rss', {
                        'feed_url': rss_source.url_pattern,
                        'llm_client': llm_client
                    })

                    # 增量抓取：传入上次抓取状态
                    incremental_kwargs = {}
                    if rss_source.last_fetched_at:
                        incremental_kwargs['last_fetched_at'] = rss_source.last_fetched_at
                    if rss_source.last_item_id:
                        incremental_kwargs['last_item_id'] = rss_source.last_item_id

                    results = await crawler.fetch(**incremental_kwargs)

                    # 如果增量抓取无结果，首次抓取时尝试扩展抓取
                    if not results and rss_source.fetch_count == 0:
                        logger.warning(f"【抓取】{rss_source.name} 首次抓取未找到内容，触发扩展抓取...")
                        results = await crawler.fetch(expanded=True)
                        if results:
                            logger.info(f"【抓取】{rss_source.name} 扩展抓取成功，获取 {len(results)} 条")
                        else:
                            logger.warning(f"【抓取】{rss_source.name} 扩展抓取后仍无内容，跳过")

                    if results:
                        _save_results(results, crawler, rss_source.name)

                        # 更新增量状态
                        latest_id = crawler.get_latest_item_id(results)
                        latest_time = crawler.get_latest_fetched_at(results)
                        rss_source.last_item_id = latest_id or rss_source.last_item_id
                        rss_source.last_fetched_at = latest_time or rss_source.last_fetched_at
                        rss_source.fetch_count = (rss_source.fetch_count or 0) + 1
                        rss_source.error_count = 0
                        rss_source.last_error = None
                        db.commit()
                        logger.info(
                            f"【抓取】{rss_source.name} 增量状态已更新: "
                            f"last_item_id={latest_id}, last_fetched_at={latest_time}"
                        )
                    else:
                        logger.info(f"【抓取】{rss_source.name} 无新内容，跳过")

                    await asyncio.sleep(3)

                except Exception as e:
                    error_msg = str(e)
                    logger.exception(f"【抓取】RSS 源 {rss_source.name} 抓取失败: {e}")
                    # 更新失败计数
                    rss_source.error_count = (rss_source.error_count or 0) + 1
                    rss_source.last_error = error_msg[:500]  # 限制长度
                    # 连续失败 3 次自动禁用
                    if rss_source.error_count >= 3:
                        rss_source.is_active = False
                        logger.warning(
                            f"【抓取】RSS 源 {rss_source.name} 连续失败 {rss_source.error_count} 次，已自动禁用"
                        )
                    db.commit()
                    continue
        except Exception as e:
            logger.warning(f"【抓取】查询 RSS 源失败: {e}")

        msg = f"[CRAWL JOB] Crawl job completed. Total added: {total_crawled}"
        console_log(msg)
        logger.info(f"[CRAWL JOB] Crawl job completed. Total added: {total_crawled}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"【定时任务】抓取任务异常: {e}")
    finally:
        db.close()

    return newly_saved_items


async def run_summarize_job():
    """Summarize unprocessed raw content with streaming filter"""
    logger.info("【定时任务】开始执行总结任务...")
    from app.database import SessionLocal
    from app.models import RawContent, Summary
    from summarizer.llm_client import LLMClient
    from app.config import get_settings

    def _is_qualified_for_summary(raw_content) -> bool:
        """检查内容是否符合总结质量标准"""
        raw_data = raw_content.raw_data or {}
        platform = raw_content.platform

        if platform == 'github':
            stars = raw_data.get('stars', 0)
            forks = raw_data.get('forks', 0)
            return stars >= 50 or forks >= 10

        elif platform == 'bilibili':
            view_count = raw_data.get('view_count', 0) or raw_data.get('stat', {}).get('view', 0)
            return view_count >= 1000

        elif platform == 'zhihu':
            voteup_count = raw_data.get('voteup_count', 0) or raw_data.get('vote_count', 0)
            answer_count = raw_data.get('answer_count', 0)
            return voteup_count >= 50 or answer_count >= 10

        elif platform == 'hackernews':
            score = raw_data.get('score', 0)
            descendants = raw_data.get('descendants', 0)
            return score >= 50 or descendants >= 10

        elif platform in ('anthropic', 'builderio'):
            return True  # 官方博客默认高质量

        return True  # 其他平台默认通过

    def _get_qualified_contents(db, platform: str, target_count: int, batch_size: int = 20):
        """流式获取符合质量标准的内容,直到达到目标数量"""
        qualified = []
        offset = 0

        while len(qualified) < target_count:
            # 获取一批未总结的该平台内容
            batch = db.query(RawContent).outerjoin(Summary).filter(
                Summary.id == None,
                RawContent.platform == platform
            ).limit(batch_size).offset(offset).all()

            if not batch:
                logger.warning(f"【{platform}】没有更多未总结内容,已获取 {len(qualified)}/{target_count}")
                break

            for raw in batch:
                if _is_qualified_for_summary(raw):
                    qualified.append(raw)
                    logger.info(f"【{platform}】符合质量标准: {raw.title[:50] if raw.title else '无标题'}...")
                    if len(qualified) >= target_count:
                        break
                else:
                    logger.info(f"【{platform}】跳过低质量内容: {raw.title[:50] if raw.title else '无标题'}...")

            offset += batch_size

        return qualified

    db = SessionLocal()
    try:
        settings = get_settings()

        # 平台权重目标: 流式获取直到达到目标数量
        platform_targets = {
            'github': 4,
            'bilibili': 2,
            'zhihu': 1,
            'anthropic': 1,
            'builderio': 1,
            'hackernews': 1,
            'rss': 1,
        }

        # 流式获取各平台合格内容
        raw_contents = []
        for platform, target in platform_targets.items():
            platform_contents = _get_qualified_contents(db, platform, target)
            raw_contents.extend(platform_contents)
            logger.info(f"【{platform}】获取 {len(platform_contents)}/{target} 条合格内容")

        # 如果总数不足7条,从其他未总结内容补充(不再过滤质量)
        if len(raw_contents) < 7:
            existing_ids = [r.id for r in raw_contents]
            additional = db.query(RawContent).outerjoin(Summary).filter(
                Summary.id == None,
                ~RawContent.id.in_(existing_ids) if existing_ids else True
            ).limit(7 - len(raw_contents)).all()
            raw_contents.extend(additional)
            logger.info(f"【补充】额外获取 {len(additional)} 条内容")

        logger.info(f"【总结】共 {len(raw_contents)} 条内容待总结")

        if not raw_contents:
            logger.info("【总结】没有新内容需要总结")
            return

        provider, model = settings.get_default_provider_and_model()
        client = LLMClient(provider, model)
        logger.info(f"【总结】使用 LLM 提供商: {provider}, 模型: {model}")
        success_count = 0
        fail_count = 0

        for raw in raw_contents:
            try:
                # 过滤已在获取阶段完成,这里直接总结
                result = await client.summarize(
                    content=raw.content or "",
                    title=raw.title or "",
                    url=raw.url or ""
                )
                summary = Summary(
                    raw_content_id=raw.id,
                    summary_text=result.summary_text,
                    key_points=result.key_points,
                    tags=result.tags,
                    ai_model=result.model_used,
                    ai_provider=result.provider,
                    tokens_used=result.tokens_used,
                    importance=result.importance,
                    highlight_sentence=result.highlight_sentence,
                )
                db.add(summary)
                db.commit()
                success_count += 1

                # Update FTS search index
                try:
                    from sqlalchemy import text
                    tags_str = ' '.join(result.tags or [])
                    db.execute(text("""
                        INSERT INTO search_index(summary_id, title, content, summary_text, tags)
                        VALUES(:sid, :title, :content, :summary_text, :tags)
                    """), {
                        "sid": summary.id,
                        "title": raw.title or "",
                        "content": raw.content or "",
                        "summary_text": result.summary_text or "",
                        "tags": tags_str,
                    })
                    db.commit()
                except Exception as fts_err:
                    logger.warning(f"[FTS] Index insert failed for summary {summary.id}: {fts_err}")
                    try:
                        db.rollback()
                    except Exception:
                        pass

                logger.info(f"【总结】已总结: {raw.title[:50]}...")
            except Exception as e:
                fail_count += 1
                logger.error(f"【总结】总结失败 (id={raw.id}): {e}")
                # Continue with next item even if one fails
                continue

        logger.info(f"【定时任务】总结任务完成 - 成功: {success_count}, 失败: {fail_count}")
    except Exception as e:
        logger.exception(f"【定时任务】总结任务异常: {e}")
    finally:
        db.close()


async def run_email_job():
    """Send daily email digest"""
    logger.info("【定时任务】开始执行邮件任务...")
    from notifier.email_sender import send_daily_digest
    try:
        await send_daily_digest()
        logger.info("【定时任务】邮件任务完成")
    except Exception as e:
        logger.exception(f"【定时任务】邮件任务异常: {e}")


async def trigger_crawl_and_reset() -> dict:
    """Manually trigger crawl and reset scheduler interval, returns new items with summaries"""
    console_log("\n[TRIGGER CRAWL] Manual crawl triggered...")
    from app.config import get_settings
    from app.database import SessionLocal
    from app.models import RawContent, Summary
    settings = get_settings()

    # Get timezone
    tz = ZoneInfo(settings.timezone)

    # Run crawl immediately and get new items
    console_log("[TRIGGER CRAWL] Starting crawl...")
    newly_saved = await run_crawl_job()
    console_log(f"[TRIGGER CRAWL] Crawl completed, {len(newly_saved)} new items saved")

    # Reset the crawl job timer (reschedule from now)
    job = scheduler.get_job('crawl_job')
    if job:
        scheduler.reschedule_job(
            'crawl_job',
            trigger=CronTrigger.from_crontab(settings.crawl_schedule, timezone=tz)
        )

    # Also trigger summarize for new content
    console_log("[TRIGGER CRAWL] Starting summarize job...")
    await run_summarize_job()
    console_log("[TRIGGER CRAWL] Summarize completed")

    # Reset summarize job timer
    summarize_job = scheduler.get_job('summarize_job')
    if summarize_job:
        scheduler.reschedule_job(
            'summarize_job',
            trigger=CronTrigger.from_crontab(settings.summarize_schedule, timezone=tz)
        )

    # Fetch the newly created summaries to return to frontend
    db = SessionLocal()
    new_summaries = []
    try:
        # Get summaries for the newly saved raw content
        raw_ids = [item["id"] for item in newly_saved]
        if raw_ids:
            summaries = db.query(Summary, RawContent).join(
                RawContent, Summary.raw_content_id == RawContent.id
            ).filter(RawContent.id.in_(raw_ids)).all()

            for summary, raw in summaries:
                # 清理标题中的 HTML 标签
                from app.routers.summaries import clean_html
                title = clean_html(raw.title)
                new_summaries.append({
                    "id": summary.id,
                    "raw_content_id": summary.raw_content_id,
                    "platform": raw.platform,
                    "title": title,
                    "summary_text": summary.summary_text,
                    "key_points": summary.key_points,
                    "tags": summary.tags,
                    "ai_model": summary.ai_model,
                    "ai_provider": summary.ai_provider,
                    "url": raw.url,
                    "author": raw.author,
                    "is_read": False,
                    "is_favorited": False,
                    "created_at": summary.created_at.isoformat() if summary.created_at else None,
                })
    finally:
        db.close()

    result = {
        "status": "success",
        "message": f"Crawl completed: {len(newly_saved)} new items, {len(new_summaries)} summarized",
        "new_items_count": len(newly_saved),
        "new_summaries_count": len(new_summaries),
        "new_summaries": new_summaries,
        "next_crawl": str(job.next_run_time) if job else None
    }
    console_log(f"[TRIGGER CRAWL] Task completed: {result['message']}")
    return result
