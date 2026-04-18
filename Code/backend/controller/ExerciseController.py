from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from config.db import get_db
from dto.ExerciseDTO import ExerciseSetCreateDTO, ExerciseSetDTO, ExerciseDTO, ExerciseUpdateDTO
from dto.PageResponseDTO import PageResponse
from service.ExerciseService import create_exercise_set, search_exercise_sets_service, get_exercise_set_detail_service, update_exercise_service
from dto.ResponseDTO import BaseResponse
from typing import Optional
from service.UserService import get_current_user
from entity.User import User

router = APIRouter(prefix="/api/exercise", tags=["Exercise"])

@router.post("/upload", response_model=BaseResponse)
def upload_exercise_set(data: ExerciseSetCreateDTO, db: Session = Depends(get_db)):
    print("upload_exercise_set received data:", data)
    try:
        exercise_set = create_exercise_set(db, data)
        print("Created exercise_set type:", type(exercise_set))
        return BaseResponse(success=True, message="Exercise set created")
    except Exception as e:
        print("Exception in upload_exercise_set:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=BaseResponse[PageResponse[ExerciseSetDTO]])
def search_exercise_sets(
    course_id: int,
    keyword: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    page_data = search_exercise_sets_service(db, course_id, keyword, page, page_size)
    return BaseResponse(success=True, message="查询成功", data=page_data)

@router.get("/{set_id}", response_model=BaseResponse[ExerciseSetDTO])
def get_exercise_set_detail(set_id: int, db: Session = Depends(get_db)):
    try:
        exercise_set_dto = get_exercise_set_detail_service(db, set_id)
        return BaseResponse(success=True, message="查询成功", data=exercise_set_dto)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{set_id}", response_model=BaseResponse)
def delete_exercise_set(set_id: int, db: Session = Depends(get_db)):
    try:
        from service.ExerciseService import delete_exercise_set_service
        delete_exercise_set_service(db, set_id)
        return BaseResponse(success=True, message="删除成功", data=None)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{exercise_id}", response_model=BaseResponse)
def update_exercise(
    exercise_id: int,
    data: ExerciseUpdateDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 只有教师可以更新习题
    if current_user.role != 'teacher':
        raise HTTPException(status_code=403, detail="Only teachers can update exercises")
    
    try:
        update_exercise_service(db, exercise_id, data)
        return BaseResponse(success=True, message="Exercise updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

