import pytest

from message_router.models import MessageIntent
from message_router.services.classifier import classify


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("What time is check-in?", MessageIntent.CHECK_IN),
        ("Can we checkin at noon?", MessageIntent.CHECK_IN),
        ("Our arrival is Friday", MessageIntent.CHECK_IN),
        ("Where do I pick up the keys?", MessageIntent.CHECK_IN),
        ("Is early access possible?", MessageIntent.CHECK_IN),
        ("We will be late", MessageIntent.CHECK_IN),
        ("Is the wifi password the same?", MessageIntent.AMENITY_INQUIRY),
        ("Is the pool heated?", MessageIntent.AMENITY_INQUIRY),
        ("Do you have a gym?", MessageIntent.AMENITY_INQUIRY),
        ("Is there parking?", MessageIntent.AMENITY_INQUIRY),
        ("What amenities are included?", MessageIntent.AMENITY_INQUIRY),
        ("Could we get a towel?", MessageIntent.AMENITY_INQUIRY),
        ("The heater is broken", MessageIntent.MAINTENANCE_REQUEST),
        ("The TV is not working", MessageIntent.MAINTENANCE_REQUEST),
        ("There is a leak in the bathroom", MessageIntent.MAINTENANCE_REQUEST),
        ("Please repair the door", MessageIntent.MAINTENANCE_REQUEST),
        ("Need maintenance for the sink", MessageIntent.MAINTENANCE_REQUEST),
        ("Can someone fix the lock?", MessageIntent.MAINTENANCE_REQUEST),
        ("About my booking", MessageIntent.BOOKING_QUESTION),
        ("Can I change my reservation?", MessageIntent.BOOKING_QUESTION),
        ("I want to cancel", MessageIntent.BOOKING_QUESTION),
        ("When do I get my refund?", MessageIntent.BOOKING_QUESTION),
        ("Can we move the dates?", MessageIntent.BOOKING_QUESTION),
    ],
)
def test_each_listed_keyword_maps_to_its_intent(content: str, expected: MessageIntent) -> None:
    assert classify(content) is expected


@pytest.mark.parametrize("content", ["Hello there", "Thank you so much!", "   "])
def test_no_keyword_maps_to_other(content: str) -> None:
    assert classify(content) is MessageIntent.OTHER


@pytest.mark.parametrize("content", ["WIFI?", "Wifi?", "wiFi?", "CHECK-IN time"])
def test_matching_ignores_case(content: str) -> None:
    assert classify(content) in {MessageIntent.AMENITY_INQUIRY, MessageIntent.CHECK_IN}
    assert classify(content) is not MessageIntent.OTHER


def test_first_category_in_spec_order_wins_regardless_of_text_position() -> None:
    # booking (4th) appears first in the text, check_in (1st) later: check_in wins
    assert classify("My booking: what is the check-in time?") is MessageIntent.CHECK_IN
    # amenity (2nd) beats maintenance (3rd) and booking (4th)
    assert classify("The pool is broken, about my booking") is MessageIntent.AMENITY_INQUIRY
    assert classify("The sink is broken, about my booking") is MessageIntent.MAINTENANCE_REQUEST


@pytest.mark.parametrize(
    "content",
    [
        "I nearly forgot",  # 'early' inside a word
        "Is the template ready?",  # 'late' inside a word
        "What a nice plate",  # 'late' inside a word
        "It is a prefix",  # 'fix' inside a word
        "That is earlier than planned",  # 'early' + extra letters is a different word
        "Nice fixture",  # 'fix' + extra letters is a different word
        "Arrive tomorrow",  # no stemming beyond the suffix rule
    ],
)
def test_keywords_inside_other_words_do_not_match(content: str) -> None:
    assert classify(content) is MessageIntent.OTHER


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("Are towels provided?", MessageIntent.AMENITY_INQUIRY),
        ("It was fixed yesterday", MessageIntent.MAINTENANCE_REQUEST),
        ("Someone is fixing it", MessageIntent.MAINTENANCE_REQUEST),
        ("The roof is leaking", MessageIntent.MAINTENANCE_REQUEST),
        ("Two repairs needed", MessageIntent.MAINTENANCE_REQUEST),
        ("My bookings are wrong", MessageIntent.BOOKING_QUESTION),
        ("I canceled it", MessageIntent.BOOKING_QUESTION),
        ("I cancelled it", MessageIntent.BOOKING_QUESTION),
        ("Please refund me", MessageIntent.BOOKING_QUESTION),
        ("Where is the key?", MessageIntent.CHECK_IN),
        ("Any amenity nearby?", MessageIntent.AMENITY_INQUIRY),
        ("Is wi-fi free?", MessageIntent.AMENITY_INQUIRY),
    ],
)
def test_common_variants_match(content: str, expected: MessageIntent) -> None:
    assert classify(content) is expected


@pytest.mark.parametrize(
    "content",
    ["What time is check in?", "check   in please", "The oven is not  working", "it's NOT-working"],
)
def test_multi_word_keywords_tolerate_hyphen_and_extra_spaces(content: str) -> None:
    assert classify(content) in {MessageIntent.CHECK_IN, MessageIntent.MAINTENANCE_REQUEST}


def test_not_working_requires_both_words() -> None:
    assert classify("It is not great") is MessageIntent.OTHER
    assert classify("Is it working?") is MessageIntent.OTHER


def test_punctuation_next_to_a_keyword_still_matches() -> None:
    assert classify("(wifi),") is MessageIntent.AMENITY_INQUIRY
    assert classify("early!") is MessageIntent.CHECK_IN
