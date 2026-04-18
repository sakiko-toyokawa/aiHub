import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
import os

# Windows 控制台 UTF-8 支持 - 必须在任何其他导入之前设置
if sys.platform == 'win32':
    import io
    import ctypes
    # 设置环境变量强制 UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置 Windows 控制台代码页为 UTF-8
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)  # CP_UTF8 = 65001
    kernel32.SetConsoleOutputCP(65001)
    # 重新包装标准输出/错误流
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
    # 强制设置默认编码
    import locale
    try:
        locale.setlocale(locale.LC_ALL, '.UTF-8')
    except locale.Error:
        pass  # 如果设置失败则忽略

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routers import summaries, sources, stats, config, agent
from app.config import get_settings

# 先获取设置
settings = get_settings()
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

# 创建自定义 StreamHandler 确保 UTF-8 输出
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if sys.platform == 'win32' and hasattr(stream, 'buffer'):
                # Windows: 直接写入二进制缓冲区确保 UTF-8
                stream.buffer.write(msg.encode('utf-8'))
                stream.buffer.write(self.terminator.encode('utf-8'))
                stream.buffer.flush()
            else:
                stream.write(msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)

console_handler = UTF8StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 创建文件处理器
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.handlers = []  # 清除现有处理器
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# 配置 uvicorn 日志
for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error', 'uvicorn.asgi']:
    uvicorn_logger = logging.getLogger(logger_name)
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.setLevel(log_level)
    uvicorn_logger.propagate = False

logger = logging.getLogger(__name__)

# 测试控制台输出是否工作
sys.stdout.write("[STARTUP] Backend starting...\n")
sys.stdout.flush()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sys.stdout.write("[STARTUP] Initializing AI Knowledge Hub...\n")
    sys.stdout.flush()
    logger.info("Starting AI Knowledge Hub...")

    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

        # Migrate: add columns if missing (no Alembic in this project)
        from sqlalchemy import text
        with engine.connect() as conn:
            # content_hash
            try:
                conn.execute(text(
                    "ALTER TABLE raw_contents ADD COLUMN content_hash VARCHAR(32)"
                ))
                conn.commit()
                logger.info("Migrated: added content_hash column to raw_contents")
            except Exception as migrate_err:
                err_msg = str(migrate_err).lower()
                if "duplicate column name" in err_msg or "already exists" in err_msg:
                    logger.debug("content_hash column already exists, skip migration")
                else:
                    logger.warning(f"Migration check for content_hash: {migrate_err}")

            # highlight_sentence
            try:
                conn.execute(text(
                    "ALTER TABLE summaries ADD COLUMN highlight_sentence TEXT"
                ))
                conn.commit()
                logger.info("Migrated: added highlight_sentence column to summaries")
            except Exception as migrate_err:
                err_msg = str(migrate_err).lower()
                if "duplicate column name" in err_msg or "already exists" in err_msg:
                    logger.debug("highlight_sentence column already exists, skip migration")
                else:
                    logger.warning(f"Migration check for highlight_sentence: {migrate_err}")

            # read_progress
            try:
                conn.execute(text(
                    "ALTER TABLE user_reads ADD COLUMN read_progress INTEGER DEFAULT 0"
                ))
                conn.commit()
                logger.info("Migrated: added read_progress column to user_reads")
            except Exception as migrate_err:
                err_msg = str(migrate_err).lower()
                if "duplicate column name" in err_msg or "already exists" in err_msg:
                    logger.debug("read_progress column already exists, skip migration")
                else:
                    logger.warning(f"Migration check for read_progress: {migrate_err}")

        # Initialize sample data (if empty)
        import scripts.init_data as init_data
        init_data.init_sample_data()
        logger.info("Sample data initialized")

        # Initialize scheduler
        from scheduler.jobs import init_scheduler
        init_scheduler()
        logger.info("Scheduler initialized")
    except Exception as e:
        logger.exception("Error during startup: %s", e)
        raise

    yield

    # Shutdown scheduler
    try:
        from scheduler.jobs import scheduler
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
    except Exception as e:
        logger.exception("Error during shutdown: %s", e)


app = FastAPI(title="AI Knowledge Hub", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()

    # 打印请求信息到控制台 - 使用显眼的格式
    log_msg = f"[REQUEST] {request.method} {request.url.path}"
    sys.stdout.write(log_msg + "\n")
    sys.stdout.flush()
    logger.info(log_msg)

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # 打印响应信息
        log_msg = f"[RESPONSE] {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
        sys.stdout.write(log_msg + "\n")
        sys.stdout.flush()
        logger.info(log_msg)

        return response
    except Exception as e:
        duration = time.time() - start_time
        log_msg = f"[ERROR] {request.method} {request.url.path} - {e} - {duration:.3f}s"
        sys.stdout.write(log_msg + "\n")
        sys.stdout.flush()
        logger.exception(log_msg)
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(summaries.router)
app.include_router(sources.router)
app.include_router(stats.router)
app.include_router(config.router)
app.include_router(agent.router)
