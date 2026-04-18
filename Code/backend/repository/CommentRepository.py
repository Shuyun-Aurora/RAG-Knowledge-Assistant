from sqlalchemy.orm import Session
from entity.Comment import Comment
from typing import List, Dict

def get_comments_by_post(db: Session, post_id: int, skip: int, limit: int) -> Dict:
    query = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc())
    total = query.count()
    comments = query.offset(skip).limit(limit).all()
    return {"total": total, "comments": comments}

def add_comment(db: Session, post_id: int, user_id: int, content: str, created_at, parent_id=None, is_anonymous: bool = False) -> Comment:
    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=content,
        created_at=created_at,
        parent_id=parent_id,
        is_anonymous=is_anonymous
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
