from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config.db import SessionLocal
from dto.ResponseDTO import BaseResponse
from dto.UserDTO import UserDTO
from entity.Course import Course
from entity.User import User
from service.UserService import get_current_user
from service.CourseService import fetch_all_courses, join_course, fetch_joined_courses, quit_course, \
    fetch_teached_courses, fetch_course_by_id, create_course, dissolve_course_by_id
from dto.CourseDTO import CourseDTO, CreateCourseDTO, CoursePageDTO
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def to_course_dto(course: Course) -> CourseDTO:
    return CourseDTO(
        id=course.id,
        name=course.name,
        description=course.description,
        teacher_id=course.teacher_id,
        teacher=UserDTO.model_validate(course.teacher),
        student_count=len(course.students),
        is_deleted=course.is_deleted
    )

@router.get("/all", response_model=BaseResponse[CoursePageDTO])
def get_all_courses(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1),
    keyword: str = Query('', alias='keyword'),
    include_dissolved: bool = Query(False, description="是否包含已解散的课程")
):
    courses, total = fetch_all_courses(db, page, page_size, keyword, include_dissolved)
    course_dtos = [to_course_dto(course) for course in courses]
    return BaseResponse(success=True, message="Courses retrieved", data=CoursePageDTO(courses=course_dtos, total=total))

@router.get("/teach", response_model=BaseResponse[CoursePageDTO])
def get_taught_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1),
    keyword: str = Query('', alias='keyword'),
    include_dissolved: bool = Query(True, description="是否包含已解散的课程")
):
    if current_user.role != 'teacher':
        return BaseResponse(success=False, message="Only teachers can view their taught courses")

    courses, total = fetch_teached_courses(db, current_user.id, page, page_size, keyword, include_dissolved)
    course_dtos = [to_course_dto(course) for course in courses]
    return BaseResponse(success=True, message="Courses retrieved", data=CoursePageDTO(courses=course_dtos, total=total))

@router.get("/join", response_model=BaseResponse[CoursePageDTO])
def get_joined_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1),
    keyword: str = Query('', alias='keyword'),
    include_dissolved: bool = Query(True, description="是否包含已解散的课程")
):
    courses, total = fetch_joined_courses(db, current_user.id, page, page_size, keyword, include_dissolved)
    course_dtos = [to_course_dto(course) for course in courses]
    return BaseResponse(success=True, message="Courses retrieved", data=CoursePageDTO(courses=course_dtos, total=total))


@router.get("/{course_id}", response_model=BaseResponse[Optional[CourseDTO]])
def get_course_by_id_endpoint(
    course_id: int,
    db: Session = Depends(get_db)
):
    course = fetch_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course_dto = to_course_dto(course)
    return BaseResponse(success=True, message="Course retrieved", data=course_dto)

@router.post("/join/{course_id}", response_model=BaseResponse[CourseDTO])
def join_course_endpoint(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != 'student':
        return BaseResponse(success=False, message="Only students can join courses")

    course = join_course(db, current_user.id, course_id)
    if not course:
        return BaseResponse(success=False, message="Join course failed")
    course_dto = to_course_dto(course)
    return BaseResponse(success=True, message="Successfully joined the course", data=course_dto)

@router.post("/quit/{course_id}", response_model=BaseResponse[CourseDTO])
def quit_course_endpoint(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != 'student':
        return BaseResponse(success=False, message="Only students can quit courses")

    course = quit_course(db, current_user.id, course_id)
    if not course:
        return BaseResponse(success=False, message="Quit course failed")
    course_dto = to_course_dto(course)
    return BaseResponse(success=True, message="Successfully quit the course", data=course_dto)

@router.post("/create", response_model=BaseResponse[CourseDTO])
def create_course_endpoint(
    data: CreateCourseDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 只有老师能创建课程
    if current_user.role != 'teacher':
        return BaseResponse(success=False, message="Only teachers can create courses")

    new_course = create_course(db, current_user.id, data.name, data.description)
    course_dto = to_course_dto(new_course)
    return BaseResponse(success=True, message="Course created successfully", data=course_dto)

@router.post("/dissolve/{course_id}", response_model=BaseResponse[CourseDTO])
def dissolve_course_endpoint(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'teacher':
        return BaseResponse(success=False, message="Only teachers can dissolve courses")

    course = dissolve_course_by_id(db, course_id, current_user.id)
    if not course:
        return BaseResponse(success=False, message="Dissolve course failed")
    course_dto = to_course_dto(course)
    return BaseResponse(success=True, message="Course dissolved successfully", data=course_dto)
