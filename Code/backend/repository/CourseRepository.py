from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from entity.Course import Course
from entity.User import User

def get_all_courses(db: Session, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = False):
    query = db.query(Course).options(joinedload(Course.teacher))
    
    if not include_dissolved:
        query = query.filter(Course.is_deleted == False)

    if keyword:
        query = query.join(Course.teacher).filter(
            or_(
                Course.name.ilike(f'%{keyword}%'),
                User.username.ilike(f'%{keyword}%')
            )
        )

    total = query.count()
    courses = query.offset((page - 1) * page_size).limit(page_size).all()
    return courses, total

def get_course_by_id(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()

def get_joined_courses_by_user_id(db: Session, user_id: int, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = True):
    from entity.User import User  # 避免循环导入
    user = db.query(User).options(joinedload(User.joined_courses).joinedload(Course.teacher)).get(user_id)

    if not user:
        return [], 0

    courses = user.joined_courses
    if not include_dissolved:
        courses = [c for c in courses if c.is_deleted == False]
        
    if keyword:
        courses = [
            c for c in courses
            if keyword.lower() in c.name.lower() or keyword.lower() in c.teacher.username.lower()
        ]

    total = len(courses)
    start = (page - 1) * page_size
    end = start + page_size
    return courses[start:end], total

def get_courses_by_teacher_id(db: Session, teacher_id: int, page: int = 1, page_size: int = 10, keyword: str = '', include_dissolved: bool = True):
    query = db.query(Course).options(joinedload(Course.teacher)).filter(Course.teacher_id == teacher_id)
    
    if not include_dissolved:
        query = query.filter(Course.is_deleted == False)

    if keyword:
        query = query.filter(Course.name.ilike(f'%{keyword}%'))

    total = query.count()
    courses = query.offset((page - 1) * page_size).limit(page_size).all()
    return courses, total

def save_course(db: Session, course: Course) -> Course:
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

def get_course_by_name(db: Session, name: str) -> Optional[Course]:
    return db.query(Course).filter(Course.name == name).first()

def dissolve_course(db: Session, course: Course) -> Course:
    course.is_deleted = True
    db.commit()
    db.refresh(course)
    return course