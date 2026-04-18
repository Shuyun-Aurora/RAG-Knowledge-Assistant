from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.db import Base

class Comment(Base):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_anonymous = Column(Boolean, default=False)

    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    parent = relationship("Comment", remote_side=[id])

    post = relationship("Post", back_populates="comments")
    user = relationship("User")
