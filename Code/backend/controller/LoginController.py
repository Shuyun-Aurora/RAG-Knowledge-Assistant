from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.db import SessionLocal
from dto.ResponseDTO import BaseResponse
from dto.UserDTO import UserRegisterDTO, UserLoginDTO, LoginData
from service.LoginService import register_user, verify_login
from util.jwt_utils import create_access_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(data: UserLoginDTO, db: Session = Depends(get_db)):
    user = verify_login(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return BaseResponse[LoginData](
        success=True,
        message="Login successful",
        data=LoginData(userId=user.id, token=access_token)
    )

@router.post("/register")
def register(data: UserRegisterDTO, db: Session = Depends(get_db)):
    try:
        user = register_user(db, data.username, data.password, data.role)
        return BaseResponse[None](success=True, message="Register successful")
    except ValueError as e:
        return BaseResponse[None](success=False, message=str(e))
