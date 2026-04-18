import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Summary, RawContent, UserRead
from datetime import datetime

router = APIRouter(prefix="/api/summaries", tags=["summaries"])
logger = logging.getLogger(__name__)


def clean_html(text: Optional[str]) -> str:
    """去除 HTML 标签"""
    if not text:
        return ""
    # 1. 将 <br>, <br/> 替换为空格
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)
    # 2. 将 </p>, </div> 等块级标签替换为空格
    text = re.sub(r'</(p|div|h[1-6]|li|tr)>', ' ', text, flags=re.IGNORECASE)
    # 3. 解码 HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    # 4. 移除所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 5. 清理多余空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


async def get_title_with_ai(raw_content: RawContent) -> str:
    """获取标题，如果为空则使用 AI 生成"""
    # 1. 先清理 HTML 标签
    title = clean_html(raw_content.title)

    # 2. 如果标题有效，直接返回
    if title and len(title.strip()) >= 3:
        return title

    # 3. 标题为空，尝试从内容生成
    content = clean_html(raw_content.content) or ""
    if not content or len(content.strip()) < 10:
        return "无标题"

    # 4. 使用 AI 生成标题
    try:
        from summarizer.llm_client import LLMClient
        from app.config import get_settings

        settings = get_settings()
        provider, model = settings.get_default_provider_and_model()
        llm_client = LLMClient(provider, model)

        title = await llm_client.generate_title(content, max_length=50)
        logger.info(f"[AI生成标题] 为 {raw_content.platform} 内容生成标题: {title}")
        return title
    except Exception as e:
        logger.warning(f"[AI生成标题] 生成失败，使用备用方案: {e}")
        # 备用方案：截取内容前50字符
        return content[:50] + "..." if len(content) > 50 else content


@router.get("/")
async def list_summaries(
    platform: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_favorited: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching summaries - platform={platform}, is_read={is_read}, page={page}")
    try:
        query = db.query(Summary, RawContent).join(RawContent)
        if platform:
            query = query.filter(RawContent.platform == platform)
        if is_read is not None:
            if is_read:
                query = query.join(UserRead).filter(UserRead.is_read == True)
            else:
                query = query.outerjoin(UserRead).filter(
                    (UserRead.is_read == False) | (UserRead.is_read == None)
                )
        if is_favorited is not None:
            if is_favorited:
                query = query.join(UserRead).filter(UserRead.is_favorited == True)
            else:
                query = query.outerjoin(UserRead).filter(
                    (UserRead.is_favorited == False) | (UserRead.is_favorited == None)
                )
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (RawContent.title.ilike(search_filter)) |
                (Summary.summary_text.ilike(search_filter))
            )
        total = query.count()
        items = query.order_by(desc(Summary.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        results = []
        for summary, raw_content in items:
            # 动态处理标题（去HTML，无标题则AI生成）
            title = await get_title_with_ai(raw_content)
            result = {
                "id": summary.id, "raw_content_id": summary.raw_content_id,
                "summary_text": summary.summary_text, "key_points": summary.key_points or [],
                "tags": summary.tags or [], "ai_model": summary.ai_model,
                "ai_provider": summary.ai_provider, "tokens_used": summary.tokens_used,
                "generated_at": summary.generated_at, "created_at": summary.created_at,
                "platform": raw_content.platform, "title": title,
                "author": raw_content.author, "url": raw_content.url,
                "is_read": summary.user_read.is_read if summary.user_read else False,
                "is_favorited": summary.user_read.is_favorited if summary.user_read else False,
                "notes": summary.user_read.notes if summary.user_read else None
            }
            results.append(result)
        logger.info(f"Returning {len(results)} summaries (total: {total})")
        return {"items": results, "total": total, "page": page, "page_size": page_size}
    except Exception as e:
        logger.exception(f"Error fetching summaries: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{summary_id}")
async def get_summary(summary_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Summaries API] Getting summary id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    # 动态处理标题（去HTML，无标题则AI生成）
    title = await get_title_with_ai(summary.raw_content)
    logger.info(f"[Summaries API] Returning summary: {title[:50]}...")
    return {
        "id": summary.id, "raw_content_id": summary.raw_content_id,
        "summary_text": summary.summary_text, "key_points": summary.key_points or [],
        "tags": summary.tags or [], "ai_model": summary.ai_model,
        "ai_provider": summary.ai_provider, "tokens_used": summary.tokens_used,
        "generated_at": summary.generated_at, "created_at": summary.created_at,
        "platform": summary.raw_content.platform, "title": title,
        "author": summary.raw_content.author, "url": summary.raw_content.url,
        "content": summary.raw_content.content,
        "is_read": summary.user_read.is_read if summary.user_read else False,
        "is_favorited": summary.user_read.is_favorited if summary.user_read else False,
        "notes": summary.user_read.notes if summary.user_read else None
    }


@router.post("/{summary_id}/read")
async def mark_as_read(summary_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Summaries API] Marking summary as read: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for mark as read: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    user_read = summary.user_read
    if not user_read:
        user_read = UserRead(summary_id=summary_id)
        db.add(user_read)
    user_read.is_read = True
    user_read.read_at = datetime.now()
    db.commit()
    logger.info(f"[Summaries API] Summary marked as read: id={summary_id}")
    return {"status": "success"}


@router.post("/{summary_id}/favorite")
async def toggle_favorite(summary_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Summaries API] Toggling favorite for summary: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for toggle favorite: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    user_read = summary.user_read
    if not user_read:
        user_read = UserRead(summary_id=summary_id)
        db.add(user_read)
    user_read.is_favorited = not user_read.is_favorited
    db.commit()
    logger.info(f"[Summaries API] Favorite toggled: id={summary_id}, is_favorited={user_read.is_favorited}")
    return {"is_favorited": user_read.is_favorited}


@router.post("/{summary_id}/notes")
async def update_notes(summary_id: int, request: dict, db: Session = Depends(get_db)):
    """更新摘要的个人笔记"""
    logger.info(f"[Summaries API] Updating notes for summary: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for notes update: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    user_read = summary.user_read
    if not user_read:
        user_read = UserRead(summary_id=summary_id)
        db.add(user_read)
    user_read.notes = request.get("notes", "")
    db.commit()
    logger.info(f"[Summaries API] Notes updated for summary: id={summary_id}")
    return {"status": "success", "notes": user_read.notes}


@router.delete("/{summary_id}")
async def delete_summary(summary_id: int, db: Session = Depends(get_db)):
    """删除指定摘要及其关联的原始数据（如果没有其他摘要引用）"""
    logger.info(f"[Summaries API] Deleting summary id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for delete: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")

    raw_content_id = summary.raw_content_id

    # 删除 summary（会级联删除 user_reads）
    db.delete(summary)
    db.commit()

    # 检查该 raw_content 是否还有其他 summaries 引用
    remaining_summaries = db.query(Summary).filter(Summary.raw_content_id == raw_content_id).count()
    if remaining_summaries == 0:
        # 没有其他摘要引用，删除原始数据
        raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
        if raw_content:
            db.delete(raw_content)
            db.commit()
            logger.info(f"[Summaries API] Raw content deleted: id={raw_content_id}")

    logger.info(f"[Summaries API] Summary deleted: id={summary_id}")
    return {"status": "success", "message": "Summary deleted"}


@router.post("/cleanup")
async def cleanup_summaries(keep_count: int = 5, db: Session = Depends(get_db)):
    """清理摘要，只保留最近 N 条（默认5条），删除其余的摘要和原始数据"""
    logger.info(f"[Summaries API] Starting cleanup, keeping {keep_count} most recent summaries")

    # 获取总数量
    total_count = db.query(Summary).count()
    if total_count <= keep_count:
        logger.info(f"[Summaries API] Cleanup skipped: only {total_count} summaries, keep_count={keep_count}")
        return {
            "status": "success",
            "message": "No cleanup needed",
            "deleted_summaries": 0,
            "deleted_raw_contents": 0,
            "remaining": total_count
        }

    # 获取要删除的 summaries（按时间倒序，跳过前 keep_count 条）
    summaries_to_delete = db.query(Summary).order_by(desc(Summary.created_at)).offset(keep_count).all()
    deleted_summary_count = len(summaries_to_delete)

    # 收集这些 summaries 关联的 raw_content_ids
    raw_content_ids = set()
    for summary in summaries_to_delete:
        if summary.raw_content_id:
            raw_content_ids.add(summary.raw_content_id)

    # 删除 summaries（会级联删除 user_reads）
    for summary in summaries_to_delete:
        db.delete(summary)
    db.commit()

    # 删除那些没有其他 summaries 引用的 raw_contents
    deleted_raw_count = 0
    for raw_content_id in raw_content_ids:
        remaining = db.query(Summary).filter(Summary.raw_content_id == raw_content_id).count()
        if remaining == 0:
            raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
            if raw_content:
                db.delete(raw_content)
                deleted_raw_count += 1
    db.commit()

    remaining_count = db.query(Summary).count()
    logger.info(f"[Summaries API] Cleanup completed: deleted {deleted_summary_count} summaries, {deleted_raw_count} raw contents, remaining {remaining_count}")

    return {
        "status": "success",
        "message": f"Cleanup completed: deleted {deleted_summary_count} summaries and {deleted_raw_count} raw contents",
        "deleted_summaries": deleted_summary_count,
        "deleted_raw_contents": deleted_raw_count,
        "remaining": remaining_count
    }
