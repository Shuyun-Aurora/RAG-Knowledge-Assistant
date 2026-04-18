from sqlalchemy.orm import Session
from passlib.context import CryptContext
from repository.UserRepository import get_user_by_username, create_user
from repository.UserAuthRepository import create_user_auth, get_auth_by_user_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user(db: Session, username: str, password: str, role: str):
    if get_user_by_username(db, username):
        raise ValueError("Username already exists")
    hashed = pwd_context.hash(password)

    user = create_user(db, username, role)
    create_user_auth(db, user.id, hashed)

    db.commit()  # 最后统一提交事务
    return user

def verify_login(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None

    auth = get_auth_by_user_id(db, user.id)
    if not auth or not pwd_context.verify(password, auth.hashed_password):
        return None

    return user
