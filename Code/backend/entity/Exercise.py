from sqlalchemy import Column, Integer, Text, Enum, ForeignKey
from config.db import Base
import enum

class ExerciseType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    blank = "blank"

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    exercise_set_id = Column(Integer, ForeignKey("exercise_sets.id"), nullable=False)
    question = Column(Text, nullable=False)
    type = Column(Enum(ExerciseType), nullable=False)
    options = Column(Text)  # JSON string
    answer = Column(Text)   # JSON string
