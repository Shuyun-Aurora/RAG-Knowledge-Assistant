from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from repository.UserAuthRepository import get_auth_by_user_id, save_user_auth
from repository.UserRepository import get_user_by_id, update_user_profile
from service.LoginService import pwd_context
from util.jwt_utils import decode_access_token
from config.db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def change_password_service(db: Session, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    auth = get_auth_by_user_id(db, user_id)
    if not auth:
        return False, "用户认证信息不存在"
    if not verify_password(old_password, auth.hashed_password):
        return False, "旧密码错误"
    new_hashed = hash_password(new_password)
    auth.hashed_password = new_hashed
    save_user_auth(db, auth)
    return True, "修改成功"

def update_profile_service(db: Session, user_id: int, name: str, email: str) -> tuple[bool, str]:
    try:
        update_user_profile(db, user_id, name, email)
        return True, "资料更新成功"
    except Exception as e:
        return False, str(e)