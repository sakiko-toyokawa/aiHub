from sqlalchemy.orm import relationship
from app.models.source import Source
from app.models.raw_content import RawContent
from app.models.summary import Summary
from app.models.user_read import UserRead
Source.raw_contents = relationship("RawContent", back_populates="source")
