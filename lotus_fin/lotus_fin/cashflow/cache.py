import hashlib
import time
from typing import List, Optional, Any, Dict

# Single-flight lock dict and timestamp tracking
_SINGLE_FLIGHT_LOCKS: Dict[str, float] = {}
_CACHE_STORE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300


def compute_cache_key(
    user_id: Optional[str],
    company: str,
    as_of: Any,
    account_scope: List[str],
    coverage_scope: str,
    version: str = "1.2.1",
) -> str:
    """
    CG-SEC-01 & CG-PERF-03: Compute SHA256 compound cache key.
    Includes user_id, company, financial cutoff, account scope, and contract version.
    """
    scope_str = ",".join(sorted(account_scope or []))
    raw = f"{user_id or 'anon'}:{company}:{as_of}:{scope_str}:{coverage_scope}:{version}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_response(cache_key: str) -> Optional[Any]:
    entry = _CACHE_STORE.get(cache_key)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > CACHE_TTL_SECONDS:
        _CACHE_STORE.pop(cache_key, None)
        return None
    return entry["data"]


def set_cached_response(cache_key: str, data: Any) -> None:
    _CACHE_STORE[cache_key] = {
        "timestamp": time.time(),
        "data": data,
    }


def acquire_single_flight(key: str, timeout: float = 10.0) -> bool:
    """
    Basic single-flight lock per company-cutoff key.
    Returns True if lock acquired, False if already inflight.
    """
    now = time.time()
    if key in _SINGLE_FLIGHT_LOCKS:
        if now - _SINGLE_FLIGHT_LOCKS[key] < timeout:
            return False
    _SINGLE_FLIGHT_LOCKS[key] = now
    return True


def release_single_flight(key: str) -> None:
    _SINGLE_FLIGHT_LOCKS.pop(key, None)
