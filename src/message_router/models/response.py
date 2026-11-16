import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from message_router.core.clock import utcnow
from message_router.core.database import Base, UtcDateTime, enum_column
from message_router.models.enums import ResponseType
from message_router.models.message import GuestMessage


class AutomatedResponse(Base):
    __tablename__ = "automated_responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("guest_messages.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    response_type: Mapped[ResponseType] = mapped_column(enum_column(ResponseType))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)

    message: Mapped[GuestMessage] = relationship(back_populates="responses", lazy="raise")
