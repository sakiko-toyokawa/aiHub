from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class RawContent(Base):
    __tablename__ = "raw_contents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    platform = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255))
    title = Column(Text)
    content = Column(Text)
    author = Column(String(255))
    author_url = Column(Text)
    url = Column(Text, nullable=False)
    raw_data = Column(JSON)
    content_hash = Column(String(32), index=True, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="raw_contents")
    summaries = relationship("Summary", back_populates="raw_content")

    __table_args__ = (
        UniqueConstraint('platform', 'external_id', name='uix_platform_external_id'),
        Index('ix_raw_content_hash', 'content_hash'),
    )
