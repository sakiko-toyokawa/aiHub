# 后端开发规范

> 适用于 `backend/` 目录下的所有 Python 代码。

---

## 1. API 路由规范

```python
# ✅ 正确：RESTful 路由设计
@app.get("/api/summaries/")
def list_summaries(...)

@app.get("/api/summaries/{id}")
def get_summary(id: int, ...)

@app.post("/api/summaries/{id}/favorite")
def toggle_favorite(id: int, ...)
```

---

## 2. 数据库模型规范

```python
class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    # 字段定义...
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 3. 配置管理规范

所有配置通过 `app/config.py` 的 Pydantic Settings 统一管理：

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/app.db"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
```

---

## 4. 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 正确
logger.info("Operation completed: %s", result)
logger.error("Operation failed: %s", error)
logger.exception("Unexpected error occurred")
```

---

## 5. 错误处理规范

```python
# ✅ 正确
from fastapi import HTTPException

try:
    result = await some_operation()
except SpecificException as e:
    logger.error("Specific error: %s", e)
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 6. 包安装规范

**必须使用清华镜像源安装 Python 包：**

```bash
# ✅ 正确
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests

# 或全局配置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```
