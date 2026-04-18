from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CreatePostRequest(BaseModel):
    title: str
    content: str
    is_anonymous: bool = False

class PostItemDTO(BaseModel):
    id: int
    title: str
    content: str
    is_anonymous: bool
    created_at: datetime
    author: Optional[str] = None  # 可以映射 author.name
    author_role: Optional[str] = None  # teacher/student

class PostListResponse(BaseModel):
    total: int
    posts: List[PostItemDTO]
