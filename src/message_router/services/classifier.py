"""Keyword-based intent classification.

Pure and I/O-free. Keywords match as whole words (so "early" is not found in "nearly"),
ignoring case. A multi-word or hyphenated keyword accepts any run of spaces or hyphens
between its words, and the last word accepts a common inflection (`towel` -> `towels`,
`fix` -> `fixed`). The first category in `KEYWORD_RULES` order wins.
"""

import re

from message_router.models.enums import MessageIntent

# Order is significant: the first category with a match wins.
KEYWORD_RULES: tuple[tuple[MessageIntent, tuple[str, ...]], ...] = (
    (
        MessageIntent.CHECK_IN,
        ("check-in", "checkin", "arrival", "keys", "key", "early", "late"),
    ),
    (
        MessageIntent.AMENITY_INQUIRY,
        ("wifi", "wi-fi", "pool", "gym", "parking", "amenities", "amenity", "towel"),
    ),
    (
        MessageIntent.MAINTENANCE_REQUEST,
        ("broken", "not working", "leak", "repair", "maintenance", "fix"),
    ),
    (
        MessageIntent.BOOKING_QUESTION,
        ("booking", "reservation", "cancel", "cancelled", "refund", "dates"),
    ),
)

_WORD_SEPARATOR = r"[\s-]+"
_INFLECTION_SUFFIX = r"(?:s|es|ed|ing)?"


def _keyword_pattern(keyword: str) -> str:
    words = [re.escape(word) for word in re.split(r"[\s-]+", keyword)]
    return _WORD_SEPARATOR.join(words) + _INFLECTION_SUFFIX


def _compile(keywords: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(_keyword_pattern(keyword) for keyword in keywords)
    return re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)


_COMPILED_RULES: tuple[tuple[MessageIntent, re.Pattern[str]], ...] = tuple(
    (intent, _compile(keywords)) for intent, keywords in KEYWORD_RULES
)


def classify(content: str) -> MessageIntent:
    """Return the intent of the first category (in spec order) that matches `content`."""
    for intent, pattern in _COMPILED_RULES:
        if pattern.search(content):
            return intent
    return MessageIntent.OTHER
