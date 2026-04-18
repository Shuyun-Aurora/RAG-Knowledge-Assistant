from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from config.db import Base

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    teacher_id = Column(Integer, ForeignKey("user.id"), nullable=False)  # 外键关联
    teacher = relationship("User", back_populates="courses")  # 反向关联
    is_deleted = Column(Boolean, nullable=False, default=False)  # 软删除标记

    # 加入这部分：课程的学生
    students = relationship(
        "User",
        secondary="user_course",
        back_populates="joined_courses"
    )
