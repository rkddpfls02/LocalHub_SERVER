from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class PostImage(Base):
    __tablename__ = "post_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="images")
