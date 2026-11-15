import uuid

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PostCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    content: str = Field(min_length=10, max_length=5000)
    industry_tags: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str
    industry_tags: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)