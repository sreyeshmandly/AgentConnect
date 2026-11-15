import uuid

import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.agent import Agent
from app.schemas.agent import (
    AgentRegister,
    AgentResponse,
    AgentLogin,
    TokenResponse,
)
from app.services.auth_service import (
    register_agent,
    authenticate_agent,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer()


@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: AgentRegister, db: Session = Depends(get_db)):

    try:
        return register_agent(db, data)

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An agent with this email already exists.",
        )


@router.post("/login", response_model=TokenResponse)
def login(data: AgentLogin, db: Session = Depends(get_db)):

    agent = authenticate_agent(
        db,
        str(data.email),
        data.password,
    )

    if not agent:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    token = create_access_token(str(agent.id))

    return {
        "access_token": token,
        "token_type": "bearer",
    }


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):

    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        agent_id = payload.get("sub")

        if not agent_id:
            raise credentials_error

        agent_uuid = uuid.UUID(agent_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    agent = db.scalar(
        select(Agent).where(Agent.id == agent_uuid)
    )

    if not agent or not agent.is_active:
        raise credentials_error

    return agent


@router.get("/me", response_model=AgentResponse)
def get_my_profile(
    current_agent: Agent = Depends(get_current_agent),
):
    return current_agent