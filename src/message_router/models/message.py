import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from message_router.core.clock import utcnow
from message_router.core.database import Base, UtcDateTime, enum_column
from message_router.models.enums import MessageIntent, MessageStatus
from message_router.models.property import Property

if TYPE_CHECKING:
    from message_router.models.response import AutomatedResponse


class GuestMessage(Base):
    __tablename__ = "guest_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("properties.id"), index=True)
    guest_name: Mapped[str] = mapped_column(String(200))
    guest_email: Mapped[str] = mapped_column(String(320))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[MessageIntent | None] = mapped_column(
        enum_column(MessageIntent), index=True, default=None
    )
    status: Mapped[MessageStatus] = mapped_column(
        enum_column(MessageStatus), index=True, default=MessageStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)

    property: Mapped[Property] = relationship(lazy="raise")
    responses: Mapped[list["AutomatedResponse"]] = relationship(
        back_populates="message",
        order_by="(AutomatedResponse.created_at, AutomatedResponse.id)",
        lazy="raise",
    )
