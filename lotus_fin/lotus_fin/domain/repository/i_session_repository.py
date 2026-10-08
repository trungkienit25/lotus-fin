from abc import ABC, abstractmethod
from typing import Optional
from lotus_fin.domain.model.chat_session import ChatSession


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

