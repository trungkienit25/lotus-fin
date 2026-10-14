import json
import logging
import time
import uuid
from typing import Optional
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.repository.i_session_repository import (
    ISessionRepository,
    StorageUnavailable,
    SessionConflictError
)

try:
    import frappe
except ImportError:
    frappe = None

_logger = logging.getLogger("lotus_fin.infrastructure.persistence.frappe_cache_session_repository")


class FrappeCacheSessionRepository(ISessionRepository):
    """
    Session repository leveraging Frappe Redis cache for cross-worker session sharing.
    Configured with a TTL (default: 86400 seconds = 24 hours).
    Scoped by site, user, or session namespace to prevent multi-tenant / multi-site leakage.
    Implements atomic distributed locking and ID-based message merge.
    """

    def __init__(self, ttl_seconds: int = 86400, lock_timeout_sec: float = 10.0):
        self.ttl_seconds = ttl_seconds
        self.lock_timeout_sec = lock_timeout_sec
        self._memory_fallback = {}  # Keyed by (site, session_id)

    def _get_site(self) -> str:
        try:
            if frappe is not None and hasattr(frappe, "local") and hasattr(frappe.local, "site") and frappe.local.site:
                return str(frappe.local.site)
        except Exception:
            pass
        return "default"

    def _get_cache_key(self, session_id: str) -> str:
        site = self._get_site()
        return f"lotus_copilot_session:{site}:{session_id}"

    def _get_lock_key(self, session_id: str) -> str:
        site = self._get_site()
        return f"lotus_copilot_lock:{site}:{session_id}"

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        site = self._get_site()
        cache_key = self._get_cache_key(session_id)

        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
                # Bypass thread-local in-memory cache to ensure fresh read from Redis across workers
                if hasattr(cache, "get_value"):
                    try:
                        raw = cache.get_value(cache_key, use_local_cache=False)
                    except TypeError:
                        raw = cache.get_value(cache_key)
                else:
                    raw = None
                if raw:
                    data = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
                    return ChatSession.model_validate(data)
                return None
            except Exception as e:
                # Storage unavailable: raise StorageUnavailable instead of swallowing as None
                _logger.error("Storage unavailable when retrieving session: %s", e)
                raise StorageUnavailable(f"Storage unavailable: {e}") from e

        # Standalone / non-Frappe fallback scoped by site
        return self._memory_fallback.get((site, session_id))

    def _acquire_lock(self, cache, lock_key: str, token: str, expiry_sec: int = 15) -> bool:
        """Acquires a distributed lock using Redis SETNX or wrapper set_value."""
        real_key = cache.make_key(lock_key) if hasattr(cache, "make_key") else lock_key
        # Check if underlying redis client supports set(..., nx=True)
        if hasattr(cache, "set") and callable(cache.set):
            try:
                res = cache.set(real_key, token, nx=True, ex=expiry_sec)
                return bool(res)
            except Exception:
                pass
        # Fallback to get_value / set_value check
        try:
            current = cache.get_value(lock_key)
            if current is None:
                cache.set_value(lock_key, token, expires_in_sec=expiry_sec)
                return True
        except Exception:
            pass
        return False

    def _release_lock(self, cache, lock_key: str, token: str) -> None:
        """Safely releases the distributed lock if the token matches."""
        real_key = cache.make_key(lock_key) if hasattr(cache, "make_key") else lock_key
        release_script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        if hasattr(cache, "eval") and callable(cache.eval):
            try:
                cache.eval(release_script, 1, real_key, token)
                return
            except Exception:
                pass
        try:
            if cache.get_value(lock_key) == token:
                cache.delete_value(lock_key)
        except Exception:
            pass

    def save_session(self, session: ChatSession) -> None:
        site = self._get_site()
        cache_key = self._get_cache_key(session.id)
        lock_key = self._get_lock_key(session.id)

        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
            except Exception as e:
                _logger.error("Failed to connect to Frappe cache: %s", e)
                raise StorageUnavailable(f"Storage unavailable: {e}") from e

            lock_token = uuid.uuid4().hex
            lock_acquired = False
            start_time = time.monotonic()
            
            # Attempt to acquire distributed lock
            while time.monotonic() - start_time < self.lock_timeout_sec:
                try:
                    if self._acquire_lock(cache, lock_key, lock_token, expiry_sec=15):
                        lock_acquired = True
                        break
                except Exception as e:
                    raise StorageUnavailable(f"Storage error during lock acquisition: {e}") from e
                time.sleep(0.05)

            try:
                # Read latest snapshot inside lock to prevent lost updates (bypass thread-local cache)
                if hasattr(cache, "get_value"):
                    try:
                        existing_raw = cache.get_value(cache_key, use_local_cache=False)
                    except TypeError:
                        existing_raw = cache.get_value(cache_key)
                else:
                    existing_raw = None
                if existing_raw:
                    existing_data = json.loads(existing_raw) if isinstance(existing_raw, (str, bytes)) else existing_raw
                    existing_session = ChatSession.model_validate(existing_data)

                    # Merge messages by stable message_id, retaining ordering
                    existing_msg_ids = {m.message_id for m in existing_session.messages}
                    for msg in session.messages:
                        if msg.message_id not in existing_msg_ids:
                            existing_session.add_message(msg)
                            existing_msg_ids.add(msg.message_id)

                    # Merge tool traces
                    existing_traces = {t.tool_call_id for t in existing_session.tool_traces}
                    for tr in session.tool_traces:
                        if tr.tool_call_id not in existing_traces:
                            existing_session.add_tool_trace(tr)
                            existing_traces.add(tr.tool_call_id)

                    existing_session.version += 1
                    payload = existing_session.model_dump_json()
                else:
                    payload = session.model_dump_json()

                cache.set_value(cache_key, payload, expires_in_sec=self.ttl_seconds)
            except Exception as e:
                _logger.error("Failed to save session to Frappe cache: %s", e)
                raise StorageUnavailable(f"Storage unavailable: {e}") from e
            finally:
                if lock_acquired:
                    self._release_lock(cache, lock_key, lock_token)
            return

        # Standalone in-memory fallback
        mem_key = (site, session.id)
        if mem_key in self._memory_fallback:
            existing = self._memory_fallback[mem_key]
            existing_msg_ids = {m.message_id for m in existing.messages}
            for msg in session.messages:
                if msg.message_id not in existing_msg_ids:
                    existing.add_message(msg)
                    existing_msg_ids.add(msg.message_id)
            existing_traces = {t.tool_call_id for t in existing.tool_traces}
            for tr in session.tool_traces:
                if tr.tool_call_id not in existing_traces:
                    existing.add_tool_trace(tr)
                    existing_traces.add(tr.tool_call_id)
            existing.version += 1
        else:
            self._memory_fallback[mem_key] = session

    def clear_session(self, session_id: str) -> None:
        site = self._get_site()
        cache_key = self._get_cache_key(session_id)

        if frappe is not None and hasattr(frappe, "cache") and callable(frappe.cache):
            try:
                cache = frappe.cache()
                cache.delete_value(cache_key)
            except Exception as e:
                _logger.warning("Failed to delete session from Frappe cache: %s", e)

        mem_key = (site, session_id)
        if mem_key in self._memory_fallback:
            del self._memory_fallback[mem_key]

