import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database import get_db
from app.models import Summary, RawContent, UserRead, Source

router = APIRouter(prefix="/api/stats", tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/")
async def get_stats(db: Session = Depends(get_db)):
    logger.info("[Stats API] Fetching statistics...")

    total_summaries = db.query(Summary).count()
    total_sources = db.query(Source).count()
    active_sources = db.query(Source).filter(Source.is_active == True).count()
    total_raw_contents = db.query(RawContent).count()

    # 只统计对应 Summary 仍然存在的已读/收藏记录
    read_count = db.query(UserRead).join(Summary).filter(UserRead.is_read == True).count()
    favorite_count = db.query(UserRead).join(Summary).filter(UserRead.is_favorited == True).count()

    platform_stats = db.query(
        RawContent.platform,
        func.count(distinct(RawContent.id)).label("content_count"),
        func.count(Summary.id).label("summary_count")
    ).outerjoin(Summary).group_by(RawContent.platform).all()

    platforms = [
        {
            "platform": p.platform,
            "content_count": p.content_count,
            "summary_count": p.summary_count
        }
        for p in platform_stats
    ]

    result = {
        "total_summaries": total_summaries,
        "total_sources": total_sources,
        "active_sources": active_sources,
        "total_raw_contents": total_raw_contents,
        "read_count": read_count,
        "favorite_count": favorite_count,
        "platforms": platforms
    }
    logger.info(f"[Stats API] Returning stats: summaries={total_summaries}, sources={total_sources}, platforms={len(platforms)}")
    return result


@router.get("/tags")
async def get_trending_tags(limit: int = 10, db: Session = Depends(get_db)):
    """获取热门标签"""
    from sqlalchemy import desc

    logger.info(f"[Stats API] Fetching trending tags with limit={limit}")

    # 获取所有摘要的标签并统计频次
    summaries_with_tags = db.query(Summary.tags).filter(Summary.tags != None).all()

    tag_counts = {}
    for (tags,) in summaries_with_tags:
        if tags:
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # 按频次排序并返回前 N 个
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    trending_tags = [tag for tag, count in sorted_tags[:limit]]

    logger.info(f"[Stats API] Returning {len(trending_tags)} trending tags (total unique: {len(tag_counts)})")

    return {
        "tags": trending_tags,
        "total": len(tag_counts)
    }
