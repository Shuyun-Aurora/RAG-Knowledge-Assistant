from typing import List
from pydantic import BaseModel

from dto.UserDTO import UserDTO

class CourseDTO(BaseModel):
    id: int
    name: str
    description: str | None
    teacher_id: int
    teacher: UserDTO
    student_count: int
    is_deleted: bool

    model_config = {
        "from_attributes": True
    }

class CreateCourseDTO(BaseModel):
    name: str
    description: str

class CoursePageDTO(BaseModel):
    courses: List[CourseDTO]
    total: int