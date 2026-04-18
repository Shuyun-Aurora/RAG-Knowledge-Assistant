from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from config.db import get_db
from dto.CommentDTO import CommentItemDTO, CommentListResponse, CreateCommentRequest
from service.PostService import fetch_course_posts, publish_post, get_post_comments, create_comment, fetch_post_by_id
from dto.ResponseDTO import BaseResponse
from dto.PostDTO import PostItemDTO, PostListResponse, CreatePostRequest
from service.UserService import get_current_user

router = APIRouter(tags=["帖子"])

@router.get("/{course_id}/post", response_model=BaseResponse)
def get_course_posts(
    course_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=50),
    keyword: str = Query("", description="搜索关键词，可为空"),
    db: Session = Depends(get_db)
):
    result = fetch_course_posts(db, course_id, skip, limit, keyword.strip())

    post_dtos = [
        PostItemDTO(
            id=p.id,
            title=p.title,
            content=p.content,
            is_anonymous=p.is_anonymous,
            created_at=p.created_at,
            author=p.user.username if (p.user and not p.is_anonymous) else "匿名",
            author_role=p.user.role if (p.user and not p.is_anonymous) else None
        )
        for p in result["posts"]
    ]

    response_data = PostListResponse(total=result["total"], posts=post_dtos)
    return BaseResponse(success=True, message="", data=response_data)

@router.post("/{course_id}/post/create", response_model=BaseResponse)
def create_post_api(
    course_id: int,
    request: CreatePostRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    new_post = publish_post(
        db=db,
        course_id=course_id,
        user_id=user.id,
        title=request.title,
        content=request.content,
        is_anonymous=request.is_anonymous
    )

    return BaseResponse(
        success=True,
        message="",
        data=PostItemDTO(
            id=new_post.id,
            title=new_post.title,
            content=new_post.content,
            is_anonymous=new_post.is_anonymous,
            created_at=new_post.created_at,
            author="匿名" if new_post.is_anonymous else user.username,
            author_role=None if new_post.is_anonymous else user.role
        )
    )


@router.get("/posts/{post_id}/comments", response_model=BaseResponse)
def get_comments(
        post_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, le=50),
        db: Session = Depends(get_db)
):
    result = get_post_comments(db, post_id, skip, limit)
    comment_dtos = [
        CommentItemDTO(
            id=c.id,
            user=c.user.username if (c.user and not c.is_anonymous) else "匿名",
            content=c.content,
            time=c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            parent_id = c.parent_id,
            is_anonymous=c.is_anonymous,
            user_role=c.user.role if (c.user and not c.is_anonymous) else None
        ) for c in result["comments"]
    ]
    response_data = CommentListResponse(total=result["total"], comments=comment_dtos)
    return BaseResponse(success=True, message="", data=response_data)


@router.post("/posts/{post_id}/comments", response_model=BaseResponse)
def add_comment(
        post_id: int,
        request: CreateCommentRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    new_comment = create_comment(
        db=db,
        post_id=post_id,
        user_id=user.id,
        content=request.content,
        created_at=datetime.utcnow(),
        parent_id = request.parent_id,
        is_anonymous=request.is_anonymous
    )
    comment_dto = CommentItemDTO(
        id=new_comment.id,
        user="匿名" if request.is_anonymous else user.username,
        content=new_comment.content,
        time=new_comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        parent_id = new_comment.parent_id,
        is_anonymous=new_comment.is_anonymous
        ,user_role=None if request.is_anonymous else user.role
    )
    return BaseResponse(success=True, message="评论成功", data=comment_dto)


@router.get("/posts/{post_id}", response_model=BaseResponse)
def get_post_by_id_api(post_id: int, db: Session = Depends(get_db)):
    post = fetch_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    post_dto = PostItemDTO(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=post.is_anonymous,
        created_at=post.created_at,
        author=post.user.username if (post.user and not post.is_anonymous) else "匿名",
        author_role=post.user.role if (post.user and not post.is_anonymous) else None
    )
    return BaseResponse(success=True, message="", data=post_dto)
