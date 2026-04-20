import logging
import sys
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Source
from app.schemas.source import Source as SourceSchema, SourceCreate, SourceUpdate

router = APIRouter(prefix="/api/sources", tags=["sources"])
logger = logging.getLogger(__name__)

# 存储后台任务状态
_crawl_tasks: Dict[str, Dict[str, Any]] = {}


def console_log(msg: str):
    """输出到控制台并强制刷新"""
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


async def _run_crawl_task(task_id: str):
    """在后台执行爬虫任务"""
    from scheduler.jobs import trigger_crawl_and_reset

    _crawl_tasks[task_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }

    try:
        console_log(f"[CRAWL TASK {task_id}] Starting background crawl...")
        result = await trigger_crawl_and_reset()

        _crawl_tasks[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
        console_log(f"[CRAWL TASK {task_id}] Completed successfully")

    except Exception as e:
        logger.exception(f"[CRAWL TASK {task_id}] Failed: {e}")
        _crawl_tasks[task_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


# ========== 爬虫相关路由（必须在 /{source_id} 之前定义）==========

@router.post("/crawl/trigger")
async def trigger_crawl(background_tasks: BackgroundTasks):
    """
    异步触发爬虫抓取
    立即返回任务ID，任务在后台执行
    """
    task_id = str(uuid.uuid4())[:8]

    console_log("=" * 60)
    console_log(f"[CRAWL API] Manual crawl triggered via API - Task ID: {task_id}")
    logger.info(f"Manual crawl triggered via API - Task ID: {task_id}")

    # 添加后台任务
    background_tasks.add_task(_run_crawl_task, task_id)

    return {
        "status": "success",
        "message": "Crawl job started in background",
        "task_id": task_id,
        "check_status_url": f"/api/sources/crawl/task/{task_id}"
    }


@router.get("/crawl/task/{task_id}")
async def get_crawl_task_status(task_id: str):
    """获取爬虫任务状态"""
    if task_id not in _crawl_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = _crawl_tasks[task_id]
    return {
        "task_id": task_id,
        **task
    }


@router.get("/crawl/tasks")
async def list_crawl_tasks():
    """列出所有爬虫任务"""
    return {
        "tasks": [
            {"task_id": tid, **info}
            for tid, info in _crawl_tasks.items()
        ]
    }


@router.get("/crawl/status")
async def get_crawl_status():
    """
    获取爬虫调度器状态
    """
    from scheduler.jobs import scheduler

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs
    }


@router.post("/crawl/trigger-sync")
async def trigger_crawl_sync():
    """
    同步触发爬虫抓取并等待结果（会阻塞直到完成）
    返回详细抓取结果
    """
    import asyncio
    from datetime import datetime
    from scheduler.jobs import trigger_crawl_and_reset

    logger.info("Manual crawl (sync) triggered via API")

    try:
        start_time = datetime.now()
        result = await trigger_crawl_and_reset()
        duration = (datetime.now() - start_time).total_seconds()

        return {
            "status": "success",
            "duration_seconds": duration,
            "result": result
        }
    except Exception as e:
        logger.exception(f"Crawl failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 基础 CRUD 路由 ==========

@router.get("/", response_model=List[SourceSchema])
async def list_sources(
    platform: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    logger.info(f"[Sources API] Listing sources - platform={platform}, is_active={is_active}")
    query = db.query(Source)
    if platform:
        query = query.filter(Source.platform == platform)
    if is_active is not None:
        query = query.filter(Source.is_active == is_active)
    results = query.order_by(desc(Source.created_at)).all()
    logger.info(f"[Sources API] Returning {len(results)} sources")
    return results


@router.post("/", response_model=SourceSchema)
async def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    logger.info(f"[Sources API] Creating source: platform={source.platform}, url={source.url_pattern}")
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    logger.info(f"[Sources API] Source created with id={db_source.id}")
    return db_source


# ========== 带参数的路由（必须在 /crawl/* 之后定义）==========

@router.get("/{source_id}", response_model=SourceSchema)
async def get_source(source_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Sources API] Getting source id={source_id}")
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        logger.warning(f"[Sources API] Source not found: id={source_id}")
        raise HTTPException(status_code=404, detail="Source not found")
    logger.info(f"[Sources API] Returning source: {source.platform} - {source.url}")
    return source


@router.put("/{source_id}", response_model=SourceSchema)
async def update_source(
    source_id: int,
    source_update: SourceUpdate,
    db: Session = Depends(get_db)
):
    logger.info(f"[Sources API] Updating source id={source_id}")
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        logger.warning(f"[Sources API] Source not found for update: id={source_id}")
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_source, field, value)

    db.commit()
    db.refresh(db_source)
    logger.info(f"[Sources API] Source updated: id={source_id}")
    return db_source


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Sources API] Deleting source id={source_id}")
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        logger.warning(f"[Sources API] Source not found for delete: id={source_id}")
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(db_source)
    db.commit()
    logger.info(f"[Sources API] Source deleted: id={source_id}")
    return {"status": "success", "message": "Source deleted"}


@router.post("/{source_id}/toggle")
async def toggle_source_active(source_id: int, db: Session = Depends(get_db)):
    logger.info(f"[Sources API] Toggling source id={source_id}")
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        logger.warning(f"[Sources API] Source not found for toggle: id={source_id}")
        raise HTTPException(status_code=404, detail="Source not found")

    db_source.is_active = not db_source.is_active
    db.commit()
    logger.info(f"[Sources API] Source toggled: id={source_id}, is_active={db_source.is_active}")
    return {"id": db_source.id, "is_active": db_source.is_active}
