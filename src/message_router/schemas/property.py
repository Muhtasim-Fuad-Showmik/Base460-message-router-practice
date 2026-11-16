import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from message_router.models.enums import Channel
from message_router.schemas.common import ExternalListingId, PropertyName


class PropertyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: PropertyName
    channel: Channel
    external_listing_id: ExternalListingId


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    channel: Channel
    external_listing_id: str
    created_at: datetime
