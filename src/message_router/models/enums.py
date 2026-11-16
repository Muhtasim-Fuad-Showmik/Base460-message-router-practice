from enum import StrEnum


class Channel(StrEnum):
    AIRBNB = "airbnb"
    BOOKING_DOT_COM = "booking_dot_com"
    DIRECT = "direct"


class MessageIntent(StrEnum):
    CHECK_IN = "check_in"
    AMENITY_INQUIRY = "amenity_inquiry"
    MAINTENANCE_REQUEST = "maintenance_request"
    BOOKING_QUESTION = "booking_question"
    OTHER = "other"


class MessageStatus(StrEnum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    RESPONDED = "responded"
    ESCALATED = "escalated"


class ResponseType(StrEnum):
    AI_GENERATED = "ai_generated"
    TEMPLATE = "template"
    ESCALATION_NOTICE = "escalation_notice"
