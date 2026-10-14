"""Direct admission, session revocation, and security boundary tests."""
import importlib
import sys
import types
from unittest.mock import patch
import pytest


def _build_fake_frappe(
    path="/api/method/lotus_fin.runtime.health.readiness",
    method="GET",
    cmd="",
    user="ordinary@example.test",
    sid="valid-session-123",
    csrf_saved="csrf-token-abc",
    csrf_supplied="csrf-token-abc",
    enabled_val=1,
    session_status="Active",
    db_raises=False,
    installed_apps=None,
    conf=None,
):
    """Build a mock frappe module for isolated boundary unit testing."""
    if installed_apps is None:
        installed_apps = ["frappe", "lotus_fin"]
    if conf is None:
        conf = {}

    class AuthenticationError(Exception):
        pass

    class PermissionError(Exception):
        pass

    class CSRFTokenError(Exception):
        pass

    def throw(msg, exc=PermissionError):
        raise exc(msg)

    def db_get_value(doctype, name, fieldname, cache=True):
        if db_raises:
            raise RuntimeError("Database connection lost")
        if doctype == "User" and fieldname == "enabled":
            return enabled_val
        return None

    def db_sql(query, params=None, as_dict=False):
        if db_raises:
            raise RuntimeError("Database connection lost")
        if "tabSessions" in query:
            if session_status:
                return [{"status": session_status}]
            return []
        return []

    flags = types.SimpleNamespace(disable_traceback=False)
    local = types.SimpleNamespace(
        session=types.SimpleNamespace(
            data={"csrf_token": csrf_saved},
            sid=sid,
        ),
        flags=flags,
    )

    db = types.SimpleNamespace(get_value=db_get_value, sql=db_sql)

    request = types.SimpleNamespace(
        path=path,
        method=method,
        headers={"X-Frappe-CSRF-Token": csrf_supplied} if csrf_supplied else {},
    )

    fake = types.SimpleNamespace(
        form_dict={"cmd": cmd},
        request=request,
        session=types.SimpleNamespace(user=user, sid=sid),
        local=local,
        db=db,
        conf=conf,
        flags=flags,
        get_installed_apps=lambda: installed_apps,
        AuthenticationError=AuthenticationError,
        PermissionError=PermissionError,
        CSRFTokenError=CSRFTokenError,
        throw=throw,
    )
    return fake


def _load_boundary(fake):
    with patch.dict(sys.modules, {"frappe": fake}):
        sys.modules.pop("lotus_fin.runtime.boundary", None)
        return importlib.import_module("lotus_fin.runtime.boundary")


# 1. Enabled ordinary actor
def test_enabled_ordinary_actor_allowed():
    fake = _build_fake_frappe(
        path="/api/method/lotus_fin.runtime.health.readiness",
        method="GET",
        user="ordinary@example.test",
        enabled_val=1,
        session_status="Active",
    )
    boundary = _load_boundary(fake)
    # Must not raise
    boundary.enforce_request_boundary()


# 2. Disabled persisted actor with old cookie
@pytest.mark.parametrize("method_path", [
    "/api/method/lotus_fin.runtime.health.readiness",
    "/api/method/lotus_fin.api.invoice_actions_api.get_context",
    "/api/method/lotus_fin.api.invoice_actions_api.search_invoices",
    "/api/method/lotus_fin.api.invoice_actions_api.open_invoice",
])
def test_disabled_persisted_actor_denied_before_dispatch(method_path):
    http_method = "GET" if "readiness" in method_path else "POST"
    fake = _build_fake_frappe(
        path=method_path,
        method=http_method,
        user="disabled@example.test",
        enabled_val=0,
        session_status="Active",
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 3. Revoked cookie (session not found in tabSessions or inactive)
@pytest.mark.parametrize("status", [None, "Expired", "Inactive", "Revoked"])
def test_revoked_cookie_denied(status):
    fake = _build_fake_frappe(
        path="/api/method/lotus_fin.runtime.health.readiness",
        method="GET",
        user="ordinary@example.test",
        enabled_val=1,
        session_status=status,
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 4. Re-enabled actor with explicitly revoked session
def test_reenabled_actor_with_revoked_session_denied():
    fake = _build_fake_frappe(
        path="/api/method/lotus_fin.runtime.health.readiness",
        method="GET",
        user="ordinary@example.test",
        enabled_val=1,  # Re-enabled in DB!
        session_status=None,  # But session is deleted/revoked
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 5. Session rotation: old session revoked, new session active
def test_session_rotation():
    # Old rotated session is inactive/deleted
    old_fake = _build_fake_frappe(
        sid="old-rotated-sid",
        user="ordinary@example.test",
        enabled_val=1,
        session_status=None,
    )
    old_boundary = _load_boundary(old_fake)
    with pytest.raises(old_fake.AuthenticationError):
        old_boundary.enforce_request_boundary()

    # New rotated session is active
    new_fake = _build_fake_frappe(
        sid="new-active-sid",
        user="ordinary@example.test",
        enabled_val=1,
        session_status="Active",
    )
    new_boundary = _load_boundary(new_fake)
    new_boundary.enforce_request_boundary()


# 6. Missing actor (not found in database: get_value returns None)
def test_missing_actor_denied():
    fake = _build_fake_frappe(
        user="nonexistent@example.test",
        enabled_val=None,
        session_status="Active",
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 7. Guest principal denied
@pytest.mark.parametrize("guest_user", ["Guest", "", None])
def test_guest_principal_denied(guest_user):
    fake = _build_fake_frappe(
        user=guest_user,
        enabled_val=1,
        session_status="Active",
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 8. Cache invalidation / Authoritative direct DB check (cache=False must be used)
def test_authoritative_db_read_ignores_stale_cache():
    cache_called_with = []

    def mock_get_value(dt, name, field, cache=True):
        cache_called_with.append(cache)
        return 0  # DB returns disabled

    fake = _build_fake_frappe(
        user="ordinary@example.test",
        session_status="Active",
    )
    fake.db.get_value = mock_get_value
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()

    # Must verify cache=False was requested to bypass stale per-process grant cache
    assert False in cache_called_with, "Authoritative read must pass cache=False"


# 9. Failure to read enabled status (database outage / exception) -> fail closed
def test_failure_to_read_status_fails_closed():
    fake = _build_fake_frappe(
        user="ordinary@example.test",
        db_raises=True,
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 10. Concurrency / TOCTOU: status changed to disabled
def test_toctou_disabled_between_requests():
    fake = _build_fake_frappe(
        user="ordinary@example.test",
        enabled_val=1,
    )
    boundary = _load_boundary(fake)
    # First request: enabled -> OK
    boundary.enforce_request_boundary()

    # Status changes concurrently in DB to disabled
    fake.db.get_value = lambda dt, name, field, **kw: 0
    # Second request must deny immediately without stale caching
    with pytest.raises(fake.AuthenticationError):
        boundary.enforce_request_boundary()


# 11. Correct CSRF for valid sessions
def test_csrf_validation_on_post():
    # Matching CSRF -> passes
    fake_ok = _build_fake_frappe(
        path="/api/method/lotus_fin.api.invoice_actions_api.get_context",
        method="POST",
        csrf_saved="secret-csrf-1",
        csrf_supplied="secret-csrf-1",
        enabled_val=1,
        session_status="Active",
    )
    b_ok = _load_boundary(fake_ok)
    b_ok.enforce_request_boundary()

    # Mismatched CSRF -> raises CSRFTokenError
    fake_bad = _build_fake_frappe(
        path="/api/method/lotus_fin.api.invoice_actions_api.get_context",
        method="POST",
        csrf_saved="secret-csrf-1",
        csrf_supplied="wrong-csrf",
        enabled_val=1,
        session_status="Active",
    )
    b_bad = _load_boundary(fake_bad)
    with pytest.raises(fake_bad.CSRFTokenError):
        b_bad.enforce_request_boundary()


# 12. Method validation for POST-only CORE methods
@pytest.mark.parametrize("method_path", [
    "/api/method/lotus_fin.api.invoice_actions_api.get_context",
    "/api/method/lotus_fin.api.invoice_actions_api.search_invoices",
    "/api/method/lotus_fin.api.invoice_actions_api.open_invoice",
])
def test_get_on_post_only_method_denied_at_boundary(method_path):
    fake = _build_fake_frappe(
        path=method_path,
        method="GET",
        user="ordinary@example.test",
        enabled_val=1,
        session_status="Active",
    )
    boundary = _load_boundary(fake)
    with pytest.raises(fake.PermissionError):
        boundary.enforce_request_boundary()


# 13. Traceback suppression flag initialized
def test_traceback_suppression_flag_set():
    fake = _build_fake_frappe(
        path="/api/method/lotus_fin.runtime.health.readiness",
        method="GET",
        user="ordinary@example.test",
        enabled_val=1,
        session_status="Active",
    )
    fake.local.flags.disable_traceback = False
    boundary = _load_boundary(fake)
    boundary.enforce_request_boundary()
    assert fake.local.flags.disable_traceback is True


# 14. Error boundary sanitizes traceback from response
def test_error_boundary_sanitizes_response():
    import json
    fake = _build_fake_frappe()
    boundary = _load_boundary(fake)

    # V1 response with exc and exception traceback
    v1_body = {
        "_server_messages": "[]",
        "exc": "Traceback (most recent call last):\n  File ...\nDoesNotExistError",
        "exc_type": "DoesNotExistError",
        "exception": "Traceback (most recent call last): ...",
    }
    response = types.SimpleNamespace(
        headers={"Content-Type": "application/json"},
        data=json.dumps(v1_body).encode("utf-8"),
    )
    boundary.sanitize_error_response(response=response)
    cleaned = json.loads(response.data.decode("utf-8"))
    assert "exc" not in cleaned
    assert "exception" not in cleaned
    assert cleaned["exc_type"] == "DoesNotExistError"

    # V2 response with errors list containing exception traceback
    v2_body = {
        "errors": [
            {
                "type": "PermissionError",
                "exception": "Traceback (most recent call last):\n  File ...",
            }
        ]
    }
    response_v2 = types.SimpleNamespace(
        headers={"Content-Type": "application/json"},
        data=json.dumps(v2_body).encode("utf-8"),
    )
    boundary.sanitize_error_response(response=response_v2)
    cleaned_v2 = json.loads(response_v2.data.decode("utf-8"))
    assert "exception" not in cleaned_v2["errors"][0]
    assert cleaned_v2["errors"][0]["type"] == "PermissionError"
