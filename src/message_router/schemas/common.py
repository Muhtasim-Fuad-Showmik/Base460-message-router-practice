from typing import Annotated

from pydantic import StringConstraints

# Text inputs: stripped of surrounding whitespace, then non-empty and within the cap.
PropertyName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
ExternalListingId = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
GuestName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
MessageContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]
ResponseBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]
