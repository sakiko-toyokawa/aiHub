from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Integer as SAInteger, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    raw_content_id = Column(Integer, ForeignKey("raw_contents.id", ondelete="CASCADE"))
    summary_text = Column(Text, nullable=False)
    key_points = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    ai_model = Column(String(100))
    ai_provider = Column(String(50))
    tokens_used = Column(SAInteger)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI评分字段 (数据库已存在)
    importance = Column(Integer, default=3)  # 重要性 1-5星

    # AI 标注的最关键的一句话
    highlight_sentence = Column(Text)

    # 归档状态
    is_archived = Column(SAInteger, default=0)  # 0=正常, 1=已归档

    raw_content = relationship("RawContent", back_populates="summaries")
    user_read = relationship("UserRead", back_populates="summary", uselist=False)
