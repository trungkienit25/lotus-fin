"""Adversarial boundary tests: legacy code never imports before denial."""
import importlib
import sys
import types
from unittest.mock import patch
import pytest


def _make_mock_db():
    return types.SimpleNamespace(
        get_value=lambda dt, n, f, **kw: 1,
        sql=lambda *a, **k: [{"status": "Active"}],
    )


@pytest.mark.parametrize('path,cmd', [
    ('/api/method/lotus_fin.api.ai_insights.get_financial_snapshot', ''),
    ('/api/v2/method/lotus_fin.api.ai_insights.get_risk_signal', ''),
    ('/', 'lotus_fin.api.ai_insights.get_financial_snapshot'),
    ('/api/method/lotus_fin.AI001.service.get_financial_health', ''),
])
@pytest.mark.parametrize('user', ['Guest', 'Administrator', 'ordinary@example.test'])
def test_legacy_routes_denied_without_qualified_integration(path, cmd, user):
    fake = types.SimpleNamespace(form_dict={'cmd': cmd}, request=types.SimpleNamespace(path=path),
        session=types.SimpleNamespace(user=user), conf={}, get_installed_apps=lambda: ['frappe', 'lotus_fin'],
        db=_make_mock_db(),
        AuthenticationError=PermissionError, PermissionError=PermissionError,
        throw=lambda message, error: (_ for _ in ()).throw(error(message)))
    with patch.dict(sys.modules, {'frappe': fake}):
        sys.modules.pop('lotus_fin.runtime.boundary', None)
        module = importlib.import_module('lotus_fin.runtime.boundary')
        with pytest.raises(PermissionError):
            module.enforce_request_boundary()


@pytest.mark.parametrize('flag,apps', [(True, ['frappe','lotus_fin']),
    ('true', ['frappe','lotus_fin','erpnext','lotus_erpnext']),
    (False, ['frappe','lotus_fin','erpnext','lotus_erpnext'])])
def test_flag_alone_cannot_enable_legacy(flag, apps):
    fake = types.SimpleNamespace(form_dict={}, request=types.SimpleNamespace(
        path='/api/method/lotus_fin.api.ai_insights.get_financial_snapshot'),
        session=types.SimpleNamespace(user='ordinary@example.test'),
        conf={'lotus_erpnext_integration_qualified': flag}, get_installed_apps=lambda: apps,
        db=_make_mock_db(),
        AuthenticationError=PermissionError, PermissionError=PermissionError,
        throw=lambda message,error: (_ for _ in ()).throw(error(message)))
    with patch.dict(sys.modules, {'frappe': fake}):
        sys.modules.pop('lotus_fin.runtime.boundary', None)
        with pytest.raises(PermissionError):
            importlib.import_module('lotus_fin.runtime.boundary').enforce_request_boundary()


def test_hooks_have_no_erp_bootstrap():
    import lotus_fin.hooks as hooks
    assert hooks.doc_events == {}
    assert hooks.scheduler_events == {}
    assert hooks.fixtures == []
    assert hooks.before_request == ['lotus_fin.runtime.boundary.enforce_request_boundary']
    assert 'erpnext' not in str(hooks.add_to_apps_screen)


@pytest.mark.parametrize('saved,supplied,allowed', [
    (None, None, False), ('', 'random', False), ('session-token', None, False),
    ('session-token', 'wrong-token', False), ('session-token', 'session-token', True),
])
def test_native_post_requires_initialized_matching_framework_csrf(saved, supplied, allowed):
    fake = types.SimpleNamespace(form_dict={}, request=types.SimpleNamespace(
        path='/api/method/lotus_fin.api.invoice_actions_api.get_context', method='POST',
        headers={'X-Frappe-CSRF-Token': supplied}),
        session=types.SimpleNamespace(user='ordinary@example.test'),
        local=types.SimpleNamespace(session=types.SimpleNamespace(data={'csrf_token': saved})),
        db=_make_mock_db(),
        AuthenticationError=PermissionError, CSRFTokenError=PermissionError,
        throw=lambda message,error: (_ for _ in ()).throw(error(message)))
    with patch.dict(sys.modules, {'frappe': fake}):
        sys.modules.pop('lotus_fin.runtime.boundary', None)
        module = importlib.import_module('lotus_fin.runtime.boundary')
        if allowed:
            module.enforce_request_boundary()
        else:
            with pytest.raises(PermissionError):
                module.enforce_request_boundary()
