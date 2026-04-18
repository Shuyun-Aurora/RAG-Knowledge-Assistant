from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.db import get_db
from entity import User
from service.UserService import get_current_user, change_password_service, update_profile_service
from dto.ResponseDTO import BaseResponse
from dto.UserDTO import UserDTO, UpdateProfileDTO

router = APIRouter()

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    user_dto = UserDTO.model_validate(current_user)
    return BaseResponse(success=True, message="User info retrieved", data=user_dto)

from pydantic import BaseModel
class ChangePasswordDTO(BaseModel):
    oldPassword: str
    newPassword: str

@router.put("/password")
def change_password(
    dto: ChangePasswordDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, message = change_password_service(db, current_user.id, dto.oldPassword, dto.newPassword)
    if not success:
        return BaseResponse(success=False, message=message, data=None)
    return BaseResponse(success=True, message="密码修改成功", data=None)

@router.put("/profile")
def update_profile(
    dto: UpdateProfileDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, message = update_profile_service(db, current_user.id, dto.name, dto.email)
    return BaseResponse(success=success, message=message, data=None)

@router.get("/course/count")
def get_course_count(current_user: User = Depends(get_current_user)):
    return BaseResponse(success=True, message="Course count retrieved", data=current_user.course_count) 
    