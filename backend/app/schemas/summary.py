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

    # AI 标注的最关键一句话
    highlight_sentence: Optional[str] = None


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


class SummaryListItem(BaseModel):
    """列表页摘要项"""
    id: int
    raw_content_id: Optional[int] = None
    platform: str
    title: str
    summary_text: str
    key_points: List[str] = []
    tags: List[str] = []
    ai_model: Optional[str] = None
    ai_provider: Optional[str] = None
    tokens_used: Optional[int] = None
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    author: Optional[str] = None
    url: str
    is_read: bool = False
    read_progress: int = 0
    is_favorited: bool = False
    notes: Optional[str] = None
    highlight_sentence: Optional[str] = None
    is_archived: bool = False

    class Config:
        from_attributes = True


class SummaryDetail(SummaryListItem):
    """详情页摘要（包含原始内容）"""
    content: Optional[str] = None


class SummaryListResponse(BaseModel):
    """列表响应"""
    items: List[SummaryListItem]
    total: int
    page: int
    page_size: int


class SimilarSummaryItem(BaseModel):
    """相似内容项"""
    id: int
    title: str
    platform: str
    summary_text: str
    tags: List[str] = []
    overlap_tags: List[str] = []
    created_at: Optional[datetime] = None
    is_read: bool = False
    is_favorited: bool = False


class SimilarSummaryResponse(BaseModel):
    """相似内容响应"""
    items: List[SimilarSummaryItem]
    total: int


class ReadStatusResponse(BaseModel):
    """阅读状态响应"""
    status: str
    is_read: bool
    read_progress: int


class FavoriteResponse(BaseModel):
    """收藏状态响应"""
    is_favorited: bool


class NotesResponse(BaseModel):
    """笔记更新响应"""
    status: str
    notes: str


class ArchiveResponse(BaseModel):
    """归档状态响应"""
    status: str
    is_archived: bool


class DeleteResponse(BaseModel):
    """删除操作响应"""
    status: str
    message: str
