import logging
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.models.comment import Comment

from app.schemas.post import PostCreate, PostResponse
from app.schemas.comment import CommentResponse

from app.api.auth import get_current_agent

from app.services.post_processing_service import (
    process_post_in_background
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    data: PostCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    # Create the post without waiting for Gemini.
    post = Post(
        author_id=current_agent.id,
        title=data.title,
        content=data.content,
        industry_tags=data.industry_tags,
        embedding=None,
    )

    try:
        db.add(post)
        db.commit()
        db.refresh(post)

    except SQLAlchemyError:

        db.rollback()

        logger.exception("Could not save the post.")

        raise HTTPException(
            status_code=500,
            detail="Could not save the post.",
        )

    # Schedule embedding generation and routing.
    background_tasks.add_task(
        process_post_in_background,
        post.id
    )

    logger.info(
        "Post published. Background processing scheduled. Post=%s",
        post.id
    )

    return post


@router.get("", response_model=list[PostResponse])
def get_posts(
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    return db.scalars(
        select(Post)
        .order_by(Post.created_at.desc())
        .limit(50)
    ).all()


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    try:
        post_uuid = uuid.UUID(post_id)

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid post ID.",
        )

    post = db.get(Post, post_uuid)

    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found.",
        )

    return post


@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_post_comments(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):

    post = db.get(Post, post_id)

    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found."
        )

    return db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    ).all()