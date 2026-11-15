import logging

from app.db.session import SessionLocal
from app.models.post import Post
from app.services.embedding_service import generate_embedding
from app.services.routing_service import route_post


logger = logging.getLogger(__name__)


def process_post_in_background(post_id):

    db = SessionLocal()

    try:
        logger.info(
            "Background processing started. Post=%s",
            post_id
        )

        post = db.get(Post, post_id)

        if not post:
            logger.error(
                "Post not found for background processing. Post=%s",
                post_id
            )
            return

        embedding_text = (
            f"Title: {post.title}\n"
            f"Content: {post.content}\n"
            f"Industries: {', '.join(post.industry_tags or [])}"
        )

        # Stage 1: Generate embedding
        embedding = generate_embedding(embedding_text)

        post.embedding = embedding

        db.commit()
        db.refresh(post)

        logger.info(
            "Post embedding generated. Post=%s",
            post_id
        )

        # Stages 2-5: Semantic search, relevance evaluation,
        # routing logs and notification creation
        routing_result = route_post(db, post)

        logger.info(
            "Background routing completed. Post=%s Result=%s",
            post_id,
            routing_result
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Background post processing failed. Post=%s",
            post_id
        )

    finally:
        db.close()