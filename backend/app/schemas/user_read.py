from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserReadBase(BaseModel):
    summary_id: int
    is_read: bool = False
    read_at: Optional[datetime] = None
    is_favorited: bool = False
    notes: Optional[str] = None


class UserReadCreate(UserReadBase):
    pass


class UserReadUpdate(BaseModel):
    summary_id: Optional[int] = None
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    is_favorited: Optional[bool] = None
    notes: Optional[str] = None


class UserRead(UserReadBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
