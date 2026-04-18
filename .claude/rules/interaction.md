# 前后端交互规范

> 适用于 API 设计、请求响应格式及跨域配置。

---

## 1. 响应格式规范

### 列表响应

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 操作响应

```json
{
  "status": "success",
  "message": "Operation completed"
}
```

### 错误响应

```json
{
  "detail": "Error message"
}
```

---

## 2. CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## 3. 前端类型对齐

前端 `src/types/index.ts` 中的接口必须与后端 Schema / API 返回保持一致。修改任意一方时，需同步检查另一方。
