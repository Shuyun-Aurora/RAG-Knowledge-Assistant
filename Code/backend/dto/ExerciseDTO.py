import json
from datetime import datetime
from pydantic import BaseModel, parse_obj_as, field_validator
from typing import List, Union, Any, Dict, Optional

class QuestionDTO(BaseModel):
    type: str
    question: str
    options: List[str] = []
    answer: Union[str, List[str]]

class ExerciseSetCreateDTO(BaseModel):
    course_id: int
    title: str
    description: str = ""
    questions: List[QuestionDTO]
    document_id: Optional[str] = None
    document_name: Optional[str] = None

class ExerciseDTO(QuestionDTO):
    id: int
    exercise_set_id: int
    type: str
    question: str
    options: str  # JSON string
    answer: str

    class Config:
        from_attributes = True

class ExerciseSetDTO(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    created_at: datetime
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    exercises: List[ExerciseDTO]

    class Config:
        from_attributes = True
class ExerciseUpdateDTO(BaseModel):
    question: str
    answer: str