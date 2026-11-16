import uuid
from datetime import datetime

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from message_router.core.clock import utcnow
from message_router.core.database import Base, UtcDateTime, enum_column
from message_router.models.enums import Channel


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    channel: Mapped[Channel] = mapped_column(enum_column(Channel), index=True)
    external_listing_id: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
