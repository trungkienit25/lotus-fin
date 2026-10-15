from abc import ABC, abstractmethod
from typing import Optional
from lotus_fin.domain.model.chat_session import ChatSession


class StorageUnavailable(RuntimeError):
    """Raised when underlying session storage is unreachable or fails."""
    pass


class SessionConflictError(RuntimeError):
    """Raised when concurrent session updates conflict."""
    pass


class ISessionRepository(ABC):
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        pass

    @abstractmethod
    def save_session(self, session: ChatSession) -> None:
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        pass

    def list_sessions(self, company: Optional[str] = None, user_id: Optional[str] = None, limit: int = 20):
        """Returns summary list of chat sessions."""
        return []

