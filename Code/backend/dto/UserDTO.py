from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegisterDTO(BaseModel):
    username: str
    password: str
    role: str

class UserLoginDTO(BaseModel):
    username: str
    password: str

class LoginData(BaseModel):
    userId: int
    token: str

class UserDTO(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: str
    # 你可以根据前端需求继续添加字段，比如email、头像url等
    model_config = {
        "from_attributes": True  # 允许从ORM对象属性读取
    }

class UpdateProfileDTO(BaseModel):
    name: str
    email: EmailStr

