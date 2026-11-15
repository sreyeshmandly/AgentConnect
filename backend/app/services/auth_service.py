import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.schemas.agent import AgentRegister
from app.core.security import hash_password, verify_password
from app.services.agent_embedding_service import ensure_agent_embedding


logger = logging.getLogger(__name__)


def register_agent(db: Session, data: AgentRegister) -> Agent:
    email = str(data.email).lower()

    existing_agent = db.scalar(
        select(Agent).where(Agent.email == email)
    )

    if existing_agent:
        raise ValueError("An agent with this email already exists.")

    agent = Agent(
        agent_name=data.agent_name,
        company_name=data.company_name,
        email=email,
        password_hash=hash_password(data.password),
        industry=data.industry,
        description=data.description,
        interests=data.interests,
        capabilities=data.capabilities,
        excluded_industries=data.excluded_industries,
    )

    try:
        db.add(agent)
        db.commit()
        db.refresh(agent)

    except Exception:
        db.rollback()
        raise

    # Generate embedding automatically after account creation.
    # Registration remains successful if Gemini is temporarily unavailable.
    ensure_agent_embedding(db, agent)

    return agent


def authenticate_agent(
    db: Session,
    email: str,
    password: str
) -> Agent | None:

    agent = db.scalar(
        select(Agent).where(Agent.email == email.lower())
    )

    if not agent or not agent.is_active:
        return None

    if not verify_password(password, agent.password_hash):
        return None

    # Retry embedding generation if it was missing during registration.
    ensure_agent_embedding(db, agent)

    return agent