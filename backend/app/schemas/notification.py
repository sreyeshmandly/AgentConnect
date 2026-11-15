import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):

    id: uuid.UUID
    post_id: uuid.UUID

    post_title: str
    post_content: str

    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)