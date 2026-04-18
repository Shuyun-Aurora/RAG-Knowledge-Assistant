from fastapi import HTTPException
from sqlalchemy.orm import Session
from entity.Course import Course
from repository.CourseRepository import get_all_courses, get_course_by_id, get_courses_by_teacher_id, save_course, \
    get_joined_courses_by_user_id, get_course_by_name, dissolve_course
from repository.UserRepository import get_user_by_id, save_user
from service.rag_service import rag_service

def fetch_all_courses(db: Session, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = False):
    return get_all_courses(db, page, page_size, keyword, include_dissolved)

def fetch_course_by_id(db: Session, course_id: int):
    return get_course_by_id(db, course_id)

def fetch_teached_courses(db: Session, teacher_id: int, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = True):
    return get_courses_by_teacher_id(db, teacher_id, page, page_size, keyword, include_dissolved)

def fetch_joined_courses(db: Session, user_id: int, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = True):
    return get_joined_courses_by_user_id(db, user_id, page, page_size, keyword, include_dissolved)

def join_course(db: Session, user_id: int, course_id: int):
    user = get_user_by_id(db, user_id)
    course = get_course_by_id(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    if course.is_deleted:
        raise HTTPException(status_code=400, detail="课程已解散，无法加入")

    if course in user.joined_courses:
        raise HTTPException(status_code=400, detail="已经加入该课程")

    user.joined_courses.append(course)
    save_user(db, user)
    return course

def quit_course(db: Session, user_id: int, course_id: int):
    user = get_user_by_id(db, user_id)
    course = get_course_by_id(db, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    if course not in user.joined_courses:
        raise HTTPException(status_code=400, detail="未加入该课程")

    user.joined_courses.remove(course)
    save_user(db, user)
    return course

def create_course(db: Session, teacher_id: int, name: str, description: str) -> Course:
    # 课程名称重复校验
    existing = get_course_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail="课程名称已存在")

    course = Course(
        name=name,
        description=description,
        teacher_id=teacher_id
    )
    saved_course = save_course(db, course)
    # 自动生成知识图谱根节点
    try:
        rag_service.create_course_knowledge_graph_root_node(name)
    except Exception as e:
        print(f"自动生成知识图谱根节点失败: {e}")
    return saved_course

def dissolve_course_by_id(db: Session, course_id: int, teacher_id: int) -> Course:
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    
    if course.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="只有课程教师可以解散课程")
    
    if course.is_deleted:
        raise HTTPException(status_code=400, detail="课程已经被解散")
    
    return dissolve_course(db, course)
