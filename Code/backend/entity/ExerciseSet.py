from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from config.db import Base
from datetime import datetime

class ExerciseSet(Base):
    __tablename__ = "exercise_sets"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    document_id = Column(String(255))  # 关联的文档ID
    document_name = Column(String(255)) 

    # 绑定该习题集下的所有题目
    exercises = relationship("Exercise", backref="exercise_set", cascade="all, delete-orphan")
