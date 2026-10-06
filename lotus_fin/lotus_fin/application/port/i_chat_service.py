from abc import ABC, abstractmethod
from typing import Any, Dict
from lotus_fin.domain.model.user_context import UserPrincipal


class IChatService(ABC):
    @abstractmethod
    def process_message(
        self,
        session_id: str,
        message: str,
        user: UserPrincipal
    ) -> Dict[str, Any]:
        """Orchestrates message processing and returns chat response payload."""
        pass

