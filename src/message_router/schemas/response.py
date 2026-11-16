import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from message_router.models.enums import ResponseType


class AutomatedResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    body: str
    response_type: ResponseType
    created_at: datetime
