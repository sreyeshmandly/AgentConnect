import logging

from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.services.embedding_service import generate_embedding


logger = logging.getLogger(__name__)


def ensure_agent_embedding(db: Session, agent: Agent) -> bool:
    """
    Generate and save an agent interest embedding when missing.

    Returns True if an embedding is available.
    Returns False if generation or database saving fails.
    """

    if agent.interest_embedding is not None:
        return True

    profile_text = (
        f"Company: {agent.company_name}\n"
        f"Industry: {agent.industry}\n"
        f"Description: {agent.description}\n"
        f"Interests: {', '.join(agent.interests or [])}\n"
        f"Capabilities: {', '.join(agent.capabilities or [])}"
    )

    try:
        embedding = generate_embedding(profile_text)

        agent.interest_embedding = embedding

        db.commit()
        db.refresh(agent)

        logger.info(
            "Agent embedding generated successfully. Agent=%s",
            agent.id
        )

        return True

    except Exception:
        db.rollback()

        logger.exception(
            "Agent embedding generation failed. Agent=%s",
            agent.id
        )

        return False
