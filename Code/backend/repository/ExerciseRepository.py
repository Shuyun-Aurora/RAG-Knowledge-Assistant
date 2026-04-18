from typing import Optional, Tuple, List

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from entity.Exercise import Exercise
from entity.ExerciseSet import ExerciseSet

def save_exercise_set(db: Session, exercise_set: ExerciseSet):
    print("save_exercise_set got:", type(exercise_set))
    db.add(exercise_set)
    db.commit()
    db.refresh(exercise_set)
    return exercise_set

def save_exercise(db: Session, exercise: Exercise):
    print("save_exercise got:", type(exercise))
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise

def search_exercise_sets_with_pagination(db: Session, course_id: int, keyword: Optional[str], page: int, page_size: int) -> Tuple[List[ExerciseSet], int]:
    query = db.query(ExerciseSet).filter(ExerciseSet.course_id == course_id)
    if keyword:
        query = query.filter(ExerciseSet.title.ilike(f"%{keyword}%"))
    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    return results, total

def get_exercise_set_with_exercises(db: Session, set_id: int) -> Optional[ExerciseSet]:
    return db.query(ExerciseSet).options(joinedload(ExerciseSet.exercises)).filter(ExerciseSet.id == set_id).first()

def delete_exercise_set_by_id(db: Session, set_id: int) -> bool:
    exercise_set = db.query(ExerciseSet).filter(ExerciseSet.id == set_id).first()
    if not exercise_set:
        return False

    db.delete(exercise_set)
    db.commit()
    return True

def find_exercises_by_document_names(db: Session, document_names: List[str]) -> List[Exercise]:
    """
    根据文档名称列表查找所有相关的练习题
    :param db: 数据库会话
    :param document_names: 文档名称列表
    :return: 练习题列表
    """
    return (
        db.query(Exercise)
        .join(ExerciseSet)
        .filter(ExerciseSet.document_name.in_(document_names))
        .all()
    )

def update_exercise(db: Session, exercise_id: int, question: str, answer: str):
    """
    更新习题
    :param db: 数据库会话
    :param exercise_id: 习题ID
    :param question: 新的题目内容
    :param answer: 新的答案
    :return: None
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise Exception("习题不存在")
    
    exercise.question = question
    exercise.answer = answer
    db.commit()
    db.refresh(exercise)
    return exercise
