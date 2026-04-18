from sqlalchemy.orm import Session

from entity.UserAuth import UserAuth
from entity.User import User

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first() # type: ignore

def create_user(db: Session, username: str, role: str):
    user = User(username=username, role=role)
    db.add(user)
    db.flush()  # 获取 user.id 而不 commit
    return user

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_auth_by_user_id(db: Session, user_id: int) -> UserAuth | None:
    return db.query(UserAuth).filter(UserAuth.user_id == user_id).first()

def save_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

def update_user_profile(db: Session, user_id: int, name: str, email: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise Exception("用户不存在")
    user.name = name
    user.email = email
    db.commit()
    db.refresh(user)
