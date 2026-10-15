# -*- coding: utf-8 -*-
"""
Composite Session Repository implementing Two-Tier Caching:
- L1 Cache: Redis via FrappeCacheSessionRepository (Ultra-fast latency <2ms)
- L2 Persistent Store: MariaDB via FrappeDatabaseSessionRepository (ACID Durable)
"""

import logging
from typing import Any, Dict, List, Optional

from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.repository.i_session_repository import ISessionRepository

_logger = logging.getLogger("lotus_fin.infrastructure.persistence.composite_session_repository")


class CompositeSessionRepository(ISessionRepository):
    """
    Two-Tier Composite Repository combining fast in-memory / Redis cache
    with durable database persistence.
    """

    def __init__(self, l1_cache: ISessionRepository, l2_persistent: ISessionRepository):
        self.l1_cache = l1_cache
        self.l2_persistent = l2_persistent

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        # 1. Attempt L1 Cache
        try:
            session = self.l1_cache.get_session(session_id)
            if session:
                return session
        except Exception as e:
            _logger.warning("L1 Cache read failed for session %s: %s", session_id, e)

        # 2. Cache miss -> Read from L2 Persistent Database
        try:
            session = self.l2_persistent.get_session(session_id)
            if session:
                # Warm up L1 cache
                try:
                    self.l1_cache.save_session(session)
                except Exception:
                    pass
                return session
        except Exception as e:
            _logger.error("L2 Database read failed for session %s: %s", session_id, e)

        return None

    def save_session(self, session: ChatSession) -> None:
        # Save to L1 Cache
        try:
            self.l1_cache.save_session(session)
        except Exception as e:
            _logger.warning("L1 Cache write failed for session %s: %s", session.id, e)

        # Save to L2 Database (durable store)
        try:
            self.l2_persistent.save_session(session)
        except Exception as e:
            _logger.error("L2 Database write failed for session %s: %s", session.id, e)

    def clear_session(self, session_id: str) -> None:
        try:
            self.l1_cache.clear_session(session_id)
        except Exception:
            pass

        try:
            self.l2_persistent.clear_session(session_id)
        except Exception:
            pass

    def list_sessions(self, company: Optional[str] = None, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        # List sessions directly from durable database
        try:
            return self.l2_persistent.list_sessions(company=company, user_id=user_id, limit=limit)
        except Exception as e:
            _logger.warning("Failed to list sessions via composite repo: %s", e)
            return []

