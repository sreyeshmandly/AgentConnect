from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent import Agent
from app.api.auth import get_current_agent
from app.services.agent_embedding_service import ensure_agent_embedding


router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"]
)


@router.post("/me/embedding")
def generate_my_embedding(
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):
    success = ensure_agent_embedding(db, current_agent)

    if not success:
        raise HTTPException(
            status_code=503,
            detail="Could not generate agent embedding. Check backend logs."
        )

    return {
        "message": "Agent interest embedding is ready.",
        "agent_id": str(current_agent.id),
        "embedding_dimensions": len(current_agent.interest_embedding),
    }