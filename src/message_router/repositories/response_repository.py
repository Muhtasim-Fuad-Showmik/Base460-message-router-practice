from sqlalchemy.orm import Session

from message_router.models import AutomatedResponse


class ResponseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, response: AutomatedResponse) -> AutomatedResponse:
        self._session.add(response)
        self._session.flush()
        return response
