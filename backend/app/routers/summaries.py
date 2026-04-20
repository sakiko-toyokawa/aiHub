import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Summary, RawContent, UserRead
from app.schemas.summary import (
    SummaryListItem, SummaryDetail, SummaryListResponse, SimilarSummaryResponse,
    ReadStatusResponse, FavoriteResponse, NotesResponse, ArchiveResponse, DeleteResponse,
)
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


def get_title(raw_content: RawContent) -> str:
    """获取标题（清理 HTML，无标题时截取内容前50字符），不调用 AI"""
    title = clean_html(raw_content.title)
    if title and len(title.strip()) >= 3:
        return title

    content = clean_html(raw_content.content) or ""
    if not content or len(content.strip()) < 10:
        return "无标题"

    return content[:50] + "..." if len(content) > 50 else content


async def get_title_with_ai(raw_content: RawContent) -> str:
    """获取标题，如果为空则使用 AI 生成（详情页使用）"""
    # 1. 先尝试简单获取
    title = get_title(raw_content)
    if title != "无标题":
        return title

    # 2. 标题为空，使用 AI 生成
    content = clean_html(raw_content.content) or ""
    if not content or len(content.strip()) < 10:
        return "无标题"

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
        return content[:50] + "..." if len(content) > 50 else content


@router.get("/", response_model=SummaryListResponse)
async def list_summaries(
    platform: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_favorited: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching summaries - platform={platform}, is_read={is_read}, is_archived={is_archived}, page={page}")
    try:
        query = db.query(Summary, RawContent).join(RawContent)
        # 默认只显示未归档内容
        if is_archived is not None:
            query = query.filter(Summary.is_archived == (1 if is_archived else 0))
        else:
            query = query.filter(Summary.is_archived == 0)
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
            # 列表页使用简单标题获取（不调用 AI）
            title = get_title(raw_content)
            result = SummaryListItem(
                id=summary.id,
                raw_content_id=summary.raw_content_id,
                summary_text=summary.summary_text,
                key_points=summary.key_points or [],
                tags=summary.tags or [],
                ai_model=summary.ai_model,
                ai_provider=summary.ai_provider,
                tokens_used=summary.tokens_used,
                generated_at=summary.generated_at,
                created_at=summary.created_at,
                platform=raw_content.platform,
                title=title,
                author=raw_content.author,
                url=raw_content.url,
                is_read=summary.user_read.is_read if summary.user_read else False,
                read_progress=summary.user_read.read_progress if summary.user_read else 0,
                is_favorited=summary.user_read.is_favorited if summary.user_read else False,
                notes=summary.user_read.notes if summary.user_read else None,
                highlight_sentence=summary.highlight_sentence,
                is_archived=bool(summary.is_archived),
            )
            results.append(result)
        logger.info(f"Returning {len(results)} summaries (total: {total})")
        return SummaryListResponse(items=results, total=total, page=page, page_size=page_size)
    except Exception as e:
        logger.exception(f"Error fetching summaries: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/search", response_model=SummaryListResponse)
async def search_summaries(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Full-text search across titles, content, summaries, and tags using FTS5"""
    logger.info(f"[Search API] query={q}, page={page}")
    try:
        from sqlalchemy import text

        # FTS5 search with ranking
        offset = (page - 1) * page_size
        fts_sql = text("""
            SELECT si.summary_id
            FROM search_index si
            WHERE search_index MATCH :q
            ORDER BY rank
            LIMIT :limit OFFSET :offset
        """)
        fts_count_sql = text("""
            SELECT COUNT(*) FROM search_index WHERE search_index MATCH :q
        """)

        # Execute FTS5 count query
        total = db.execute(fts_count_sql, {"q": q}).scalar() or 0

        if total == 0:
            return SummaryListResponse(items=[], total=0, page=page, page_size=page_size)

        # Execute FTS5 search
        summary_ids = [row[0] for row in db.execute(fts_sql, {"q": q, "limit": page_size, "offset": offset})]

        if not summary_ids:
            return SummaryListResponse(items=[], total=total, page=page, page_size=page_size)

        # Fetch full summary data
        query = db.query(Summary, RawContent).join(RawContent).filter(Summary.id.in_(summary_ids))
        items = query.all()

        # Preserve FTS result order
        item_map = {summary.id: (summary, raw_content) for summary, raw_content in items}
        results = []
        for sid in summary_ids:
            if sid not in item_map:
                continue
            summary, raw_content = item_map[sid]
            title = get_title(raw_content)
            results.append(SummaryListItem(
                id=summary.id,
                raw_content_id=summary.raw_content_id,
                summary_text=summary.summary_text,
                key_points=summary.key_points or [],
                tags=summary.tags or [],
                ai_model=summary.ai_model,
                ai_provider=summary.ai_provider,
                tokens_used=summary.tokens_used,
                generated_at=summary.generated_at,
                created_at=summary.created_at,
                platform=raw_content.platform,
                title=title,
                author=raw_content.author,
                url=raw_content.url,
                is_read=summary.user_read.is_read if summary.user_read else False,
                read_progress=summary.user_read.read_progress if summary.user_read else 0,
                is_favorited=summary.user_read.is_favorited if summary.user_read else False,
                notes=summary.user_read.notes if summary.user_read else None,
                highlight_sentence=summary.highlight_sentence,
                is_archived=bool(summary.is_archived),
            ))

        logger.info(f"[Search API] Returning {len(results)} results for '{q}' (total: {total})")
        return SummaryListResponse(items=results, total=total, page=page, page_size=page_size)
    except Exception as e:
        logger.exception(f"[Search API] Error searching: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/{summary_id}", response_model=SummaryDetail)
async def get_summary(summary_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Summaries API] Getting summary id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    # 详情页使用 AI 生成标题（如果为空）
    title = await get_title_with_ai(summary.raw_content)
    logger.info(f"[Summaries API] Returning summary: {title[:50]}...")
    return SummaryDetail(
        id=summary.id,
        raw_content_id=summary.raw_content_id,
        summary_text=summary.summary_text,
        key_points=summary.key_points or [],
        tags=summary.tags or [],
        ai_model=summary.ai_model,
        ai_provider=summary.ai_provider,
        tokens_used=summary.tokens_used,
        generated_at=summary.generated_at,
        created_at=summary.created_at,
        platform=summary.raw_content.platform,
        title=title,
        author=summary.raw_content.author,
        url=summary.raw_content.url,
        content=clean_html(summary.raw_content.content),
        is_read=summary.user_read.is_read if summary.user_read else False,
        read_progress=summary.user_read.read_progress if summary.user_read else 0,
        is_favorited=summary.user_read.is_favorited if summary.user_read else False,
        notes=summary.user_read.notes if summary.user_read else None,
        highlight_sentence=summary.highlight_sentence,
    )


@router.post("/{summary_id}/read", response_model=ReadStatusResponse)
async def mark_as_read(summary_id: int, request: dict = None, db: Session = Depends(get_db)):
    """标记为已读，可选传入 progress (0-100) 更新阅读进度"""
    logger.info(f"[Summaries API] Marking summary as read: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for mark as read: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    user_read = summary.user_read
    if not user_read:
        user_read = UserRead(summary_id=summary_id)
        db.add(user_read)

    progress = request.get("progress") if request else None
    now = datetime.now()

    if progress is not None:
        progress = max(0, min(100, int(progress)))
        user_read.read_progress = progress
        if progress >= 100:
            user_read.is_read = True
            user_read.read_at = now
        logger.info(f"[Summaries API] Read progress updated: id={summary_id}, progress={progress}")
    else:
        # 幂等：已经是已读则跳过
        if user_read.is_read:
            logger.info(f"[Summaries API] Summary already read, skipping: id={summary_id}")
            return {"status": "success", "already_read": True}
        user_read.is_read = True
        user_read.read_progress = 100
        user_read.read_at = now
        logger.info(f"[Summaries API] Summary marked as read: id={summary_id}")

    db.commit()
    return {"status": "success", "is_read": user_read.is_read, "read_progress": user_read.read_progress}


@router.post("/{summary_id}/favorite", response_model=FavoriteResponse)
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


@router.post("/{summary_id}/notes", response_model=NotesResponse)
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


@router.delete("/{summary_id}", response_model=DeleteResponse)
async def delete_summary(summary_id: int, db: Session = Depends(get_db)):
    """删除指定摘要及其关联的原始数据（如果没有其他摘要引用）"""
    logger.info(f"[Summaries API] Deleting summary id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for delete: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")

    raw_content_id = summary.raw_content_id

    # 删除 summary（会级联删除 user_reads）
    # Remove from FTS index first
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM search_index WHERE summary_id = :sid"), {"sid": summary_id})
    except Exception as fts_err:
        logger.warning(f"[FTS] Index delete failed for summary {summary_id}: {fts_err}")

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


@router.post("/cleanup", response_model=DeleteResponse)
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


@router.get("/{summary_id}/similar", response_model=SimilarSummaryResponse)
async def get_similar_summaries(summary_id: int, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """获取与指定摘要相似的内容推荐，基于标签重叠度排序"""
    logger.info(f"[Summaries API] Finding similar summaries for id={summary_id}")
    target = db.query(Summary).filter(Summary.id == summary_id).first()
    if not target:
        logger.warning(f"[Summaries API] Summary not found for similar: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")

    target_tags = set(target.tags or [])
    if not target_tags:
        logger.info(f"[Summaries API] Target summary has no tags, returning recent items")
        others = db.query(Summary).filter(Summary.id != summary_id).order_by(desc(Summary.created_at)).limit(limit).all()
    else:
        # 获取所有其他摘要，按标签交集数量降序排列
        others = db.query(Summary).filter(Summary.id != summary_id).all()
        scored = []
        for s in others:
            s_tags = set(s.tags or [])
            overlap = len(target_tags & s_tags)
            if overlap > 0 or len(others) <= limit * 2:
                scored.append((s, overlap))
        scored.sort(key=lambda x: (-x[1], -x[0].created_at.timestamp() if x[0].created_at else 0))
        others = [s for s, _ in scored[:limit]]

    from app.schemas.summary import SimilarSummaryItem
    results = []
    for s in others:
        title = get_title(s.raw_content)
        overlap_tags = list(set(s.tags or []) & target_tags) if target_tags else []
        results.append(SimilarSummaryItem(
            id=s.id,
            title=title,
            platform=s.raw_content.platform,
            summary_text=s.summary_text[:200] + "..." if s.summary_text and len(s.summary_text) > 200 else (s.summary_text or ""),
            tags=s.tags or [],
            overlap_tags=overlap_tags,
            created_at=s.created_at,
            is_read=s.user_read.is_read if s.user_read else False,
            is_favorited=s.user_read.is_favorited if s.user_read else False,
        ))
    logger.info(f"[Summaries API] Returning {len(results)} similar summaries for id={summary_id}")
    return SimilarSummaryResponse(items=results, total=len(results))


@router.post("/{summary_id}/archive", response_model=ArchiveResponse)
async def archive_summary(summary_id: int, db: Session = Depends(get_db)):
    """归档指定摘要（软删除）"""
    logger.info(f"[Summaries API] Archiving summary: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for archive: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    summary.is_archived = 1
    db.commit()
    logger.info(f"[Summaries API] Summary archived: id={summary_id}")
    return {"status": "success", "is_archived": True}


@router.post("/{summary_id}/unarchive", response_model=ArchiveResponse)
async def unarchive_summary(summary_id: int, db: Session = Depends(get_db)):
    """恢复归档的摘要"""
    logger.info(f"[Summaries API] Unarchiving summary: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for unarchive: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    summary.is_archived = 0
    db.commit()
    logger.info(f"[Summaries API] Summary unarchived: id={summary_id}")
    return {"status": "success", "is_archived": False}


@router.delete("/{summary_id}/permanent", response_model=DeleteResponse)
async def permanently_delete_summary(summary_id: int, db: Session = Depends(get_db)):
    """永久删除已归档的摘要及其关联数据"""
    logger.info(f"[Summaries API] Permanently deleting summary: id={summary_id}")
    summary = db.query(Summary).filter(Summary.id == summary_id).first()
    if not summary:
        logger.warning(f"[Summaries API] Summary not found for permanent delete: id={summary_id}")
        raise HTTPException(status_code=404, detail="Summary not found")
    if not summary.is_archived:
        raise HTTPException(status_code=400, detail="Only archived summaries can be permanently deleted")

    raw_content_id = summary.raw_content_id

    # Remove from FTS index
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM search_index WHERE summary_id = :sid"), {"sid": summary_id})
    except Exception as fts_err:
        logger.warning(f"[FTS] Index delete failed for summary {summary_id}: {fts_err}")

    db.delete(summary)
    db.commit()

    # Check if raw_content has other summaries
    remaining = db.query(Summary).filter(Summary.raw_content_id == raw_content_id).count()
    if remaining == 0:
        raw = db.query(RawContent).filter(RawContent.id == raw_content_id).first()
        if raw:
            db.delete(raw)
            db.commit()

    logger.info(f"[Summaries API] Summary permanently deleted: id={summary_id}")
    return {"status": "success", "message": "Summary permanently deleted"}
