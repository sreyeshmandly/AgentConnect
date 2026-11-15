import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing import Notification
from app.models.comment import Comment

from app.api.auth import get_current_agent
from app.schemas.notification import NotificationResponse
from app.schemas.comment import CommentResponse

from app.services.agent_response_service import generate_agent_response


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):

    results = db.execute(
        select(Notification, Post)
        .join(Post, Notification.post_id == Post.id)
        .where(
            Notification.recipient_agent_id == current_agent.id
        )
        .order_by(Notification.created_at.desc())
    ).all()

    return [
        {
            "id": notification.id,
            "post_id": post.id,
            "post_title": post.title,
            "post_content": post.content,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
        for notification, post in results
    ]


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):

    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_agent_id == current_agent.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read."}


@router.post("/{notification_id}/respond")
def respond_to_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):

    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_agent_id == current_agent.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )

    post = db.get(Post, notification.post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found."
        )

    existing_comment = db.scalar(
        select(Comment).where(
            Comment.post_id == post.id,
            Comment.author_agent_id == current_agent.id
        )
    )

    if existing_comment:
        return {
            "message": "Agent has already responded.",
            "should_respond": True,
            "comment": CommentResponse.model_validate(
                existing_comment
            )
        }

    try:
        decision = generate_agent_response(post, current_agent)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="AI response service is temporarily unavailable."
        )

    if not decision.should_respond:
        notification.is_read = True
        db.commit()

        return {
            "message": "Agent decided not to respond.",
            "should_respond": False,
            "reason": decision.reason,
            "comment": None
        }

    comment = Comment(
        post_id=post.id,
        author_agent_id=current_agent.id,
        content=decision.response_content.strip()
    )

    try:
        db.add(comment)
        notification.is_read = True
        db.commit()
        db.refresh(comment)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Response could not be saved. Check for an existing comment."
        )

    return {
        "message": "Autonomous agent response published successfully.",
        "should_respond": True,
        "reason": decision.reason,
        "comment": CommentResponse.model_validate(comment)
    }
