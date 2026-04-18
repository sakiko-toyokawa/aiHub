from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SummaryBase(BaseModel):
    raw_content_id: int
    summary_text: str
    key_points: List[str] = []
    tags: List[str] = []
    ai_model: Optional[str] = None
    ai_provider: Optional[str] = None
    tokens_used: Optional[int] = None

    # AI评分字段
    importance: Optional[int] = None  # 重要性 1-5星


class SummaryCreate(SummaryBase):
    pass


class SummaryUpdate(BaseModel):
    raw_content_id: Optional[int] = None
    summary_text: Optional[str] = None
    key_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    ai_model: Optional[str] = None
    ai_provider: Optional[str] = None
    tokens_used: Optional[int] = None


class Summary(SummaryBase):
    id: int
    generated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
