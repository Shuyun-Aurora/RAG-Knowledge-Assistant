from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from config.db import Base

user_course_table = Table(
    "user_course",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("course.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String)
    email = Column(String, unique=True, index=True)  # 添加邮箱字段
    name = Column(String)  # 添加真实姓名字段

    # 老师所教的课程
    courses = relationship("Course", back_populates="teacher")

    # 学生加入的课程（多对多）
    joined_courses = relationship(
        "Course",
        secondary="user_course",
        back_populates="students"
    )

    @property
    def course_count(self):
        """获取用户的课程总数（教师为教授的课程数，学生为加入的课程数）"""
        if self.role == 'teacher':
            return len([c for c in self.courses if not c.is_deleted])
        else:
            return len([c for c in self.joined_courses if not c.is_deleted])
