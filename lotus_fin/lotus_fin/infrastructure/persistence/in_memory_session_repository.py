from typing import Dict, Optional
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.repository.i_session_repository import ISessionRepository


class InMemorySessionRepository(ISessionRepository):
    """
    Session repository storing sessions in-memory or thread-safe cache.
    """
    def __init__(self):
        self._store: Dict[str, ChatSession] = {}

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self._store.get(session_id)

    def save_session(self, session: ChatSession) -> None:
        self._store[session.id] = session

    def clear_session(self, session_id: str) -> None:
        if session_id in self._store:
            del self._store[session_id]

