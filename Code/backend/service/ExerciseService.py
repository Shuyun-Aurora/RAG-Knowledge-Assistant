from typing import List, Optional
from sqlalchemy.orm import Session
from dto.ExerciseDTO import QuestionDTO, ExerciseDTO, ExerciseSetDTO, ExerciseSetCreateDTO, ExerciseUpdateDTO
from dto.PageResponseDTO import PageResponse
from entity.Exercise import Exercise
from entity.ExerciseSet import ExerciseSet
from repository.ExerciseRepository import save_exercise_set, save_exercise, search_exercise_sets_with_pagination, \
    get_exercise_set_with_exercises, delete_exercise_set_by_id, find_exercises_by_document_names, update_exercise
import json

def create_exercise_set(db: Session, dto: ExerciseSetCreateDTO) -> ExerciseSet:
    print("create_exercise_set questions types:", [type(q) for q in dto.questions])
    exercise_set = ExerciseSet(
        course_id=dto.course_id,
        title=dto.title,
        description=dto.description,
        document_id=dto.document_id,
        document_name=dto.document_name
    )
    save_exercise_set(db, exercise_set)

    for q in dto.questions:
        print("Processing question:", q)
        exercise = Exercise(
            exercise_set_id=exercise_set.id,
            question=q.question,
            type=q.type,
            options=json.dumps(q.options or []),
            answer=json.dumps(q.answer)
        )
        save_exercise(db, exercise)
        print("Saving exercise entity:", exercise)

    db.refresh(exercise_set)  # 确保 relationship 绑定好
    return exercise_set


def search_exercise_sets_service(db: Session, course_id: int, keyword: Optional[str], page: int, page_size: int) -> PageResponse[ExerciseSetDTO]:
    results, total = search_exercise_sets_with_pagination(db, course_id, keyword, page, page_size)
    # 转成DTO列表（不包含习题详细）
    dto_items = [ExerciseSetDTO.from_orm(r) for r in results]
    return PageResponse[ExerciseSetDTO](total=total, items=dto_items)

def get_exercise_set_detail_service(db: Session, set_id: int) -> ExerciseSetDTO:
    exercise_set = get_exercise_set_with_exercises(db, set_id)
    if not exercise_set:
        raise Exception("ExerciseSet not found")
    # ORM转DTO，自动关联习题列表
    return ExerciseSetDTO.from_orm(exercise_set)

def delete_exercise_set_service(db: Session, set_id: int):
    success = delete_exercise_set_by_id(db, set_id)
    if not success:
        raise Exception("未找到对应的习题集")

def update_exercise_service(db: Session, exercise_id: int, dto: ExerciseUpdateDTO):
    """
    更新习题
    :param db: 数据库会话
    :param exercise_id: 习题ID
    :param dto: 更新数据
    :return: None
    """
    update_exercise(db, exercise_id, dto.question, dto.answer)

def get_exercises_by_document_names(db: Session, document_names: List[str]) -> List[dict]:
    """
    根据文档名称列表获取所有相关的练习题
    :param db: 数据库会话
    :param document_names: 文档名称列表
    :return: 练习题列表
    """
    exercises = find_exercises_by_document_names(db, document_names)
    return [{
        "id": exercise.id,
        "question": exercise.question,
        "type": exercise.type,
        "options": json.loads(exercise.options) if exercise.options else [],
        "answer": json.loads(exercise.answer) if exercise.answer else None,
        "exercise_set_id": exercise.exercise_set_id
    } for exercise in exercises]
