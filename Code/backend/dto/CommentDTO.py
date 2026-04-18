from pydantic import BaseModel
from typing import List, Optional

class CommentItemDTO(BaseModel):
    id: int
    user: str
    content: str
    time: str
    parent_id: Optional[int] = None
    is_anonymous: bool
    user_role: Optional[str] = None  # teacher/student

class CommentListResponse(BaseModel):
    total: int
    comments: List[CommentItemDTO]

class CreateCommentRequest(BaseModel):
    content: str
    parent_id: Optional[int] = None
    is_anonymous: bool = False