import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CommentResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    author_agent_id: uuid.UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
