import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from message_router.models.enums import MessageIntent, MessageStatus
from message_router.schemas.common import GuestName, MessageContent
from message_router.schemas.property import PropertyRead
from message_router.schemas.response import AutomatedResponseRead


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: uuid.UUID
    guest_name: GuestName
    guest_email: EmailStr
    content: MessageContent


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    guest_name: str
    guest_email: str
    content: str
    intent: MessageIntent | None
    status: MessageStatus
    created_at: datetime


class MessageDetail(MessageRead):
    property: PropertyRead
    responses: list[AutomatedResponseRead]
