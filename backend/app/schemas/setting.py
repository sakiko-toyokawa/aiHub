from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class Setting(SettingBase):
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
