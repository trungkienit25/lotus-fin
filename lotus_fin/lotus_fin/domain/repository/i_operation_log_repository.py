# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Optional
from lotus_fin.domain.model.operation_log import SandboxOperationLogEntry


class IOperationLogRepository(ABC):
    """
    Domain Repository Port for appending and querying audit traces of AI operations.
    """
    @abstractmethod
    def append_log(self, entry: SandboxOperationLogEntry) -> None:
        """Append an audit log entry in append-only fashion."""
        pass

    @abstractmethod
    def query_logs(
        self,
        company: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[SandboxOperationLogEntry]:
        """Retrieve recent audit log entries matching criteria."""
        pass

    @abstractmethod
    def clear_logs(self, company: Optional[str] = None) -> None:
        """Reset logs (e.g. before beginning a clean demo run)."""
        pass

