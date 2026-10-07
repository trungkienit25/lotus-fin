"""
Frappe Cache Session Repository.
Persists ChatSession state into Redis / Frappe Cache with TTL for multi-worker support.
Falls back to in-memory dictionary when running without Frappe.
"""

import json
import logging
from typing import Optional
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.repository.i_session_repository import ISessionRepository

try:
    import frappe
except ImportError:
    frappe = None

_logger = logging.getLogger("lotus_fin.infrastructure.persistence.frappe_cache_session_repository")


class FrappeCacheSessionRepository(ISessionRepository):
    """
    Session repository leveraging Frappe Redis cache for cross-worker session sharing.
    Configured with a TTL (default: 86400 seconds = 24 hours).
    """

    def __init__(self, ttl_seconds: int = 86400):
        self.ttl_seconds = ttl_seconds
        self._memory_fallback = {}

    def _get_cache_key(self, session_id: str) -> str:
        return f"lotus_copilot_session:{session_id}"

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
                raw = cache.get_value(self._get_cache_key(session_id))
                if raw:
                    data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
                    return ChatSession.model_validate(data)
                return None
            except Exception as e:
                _logger.warning("Failed to retrieve session from Frappe cache, using memory fallback: %s", e)

        return self._memory_fallback.get(session_id)

    def save_session(self, session: ChatSession) -> None:
        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
                payload = session.model_dump_json()
                cache.set_value(self._get_cache_key(session.id), payload, expires_in_sec=self.ttl_seconds)
                return
            except Exception as e:
                _logger.warning("Failed to save session to Frappe cache, using memory fallback: %s", e)

        self._memory_fallback[session.id] = session

    def clear_session(self, session_id: str) -> None:
        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
                cache.delete_value(self._get_cache_key(session_id))
            except Exception as e:
                _logger.warning("Failed to delete session from Frappe cache: %s", e)

        if session_id in self._memory_fallback:
            del self._memory_fallback[session_id]
