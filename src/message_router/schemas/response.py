import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from message_router.models.enums import ResponseType
from message_router.schemas.common import ResponseBody


class AutomatedResponseCreate(BaseModel):
    """`escalation_notice` is deliberately absent: only `/escalate` creates that type."""

    model_config = ConfigDict(extra="forbid")

    body: ResponseBody
    response_type: Literal[ResponseType.AI_GENERATED, ResponseType.TEMPLATE]


class AutomatedResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    body: str
    response_type: ResponseType
    created_at: datetime
