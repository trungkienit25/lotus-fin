"""Adversarial config lifecycle tests; synthetic framework, no live authority."""

from types import SimpleNamespace
import pytest
from lotus_fin.infrastructure.config.invoice_actions_config_loader import (
    ConfigurationError, InvoiceActionsConfigLoader as Loader,
)


def raw_config():
    return {"enabled": True, "signing_key_id": "synthetic-key",
            "signing_secret": "synthetic-A-" * 4, "connections": {}}


@pytest.fixture
def framework():
    Loader.clear_cache()
    raw = raw_config()
    f = SimpleNamespace(local=SimpleNamespace(site="test-site"),
                        get_site_config=lambda: {"lotus_fin_invoice_actions": raw})
    yield f, raw
    Loader.clear_cache()


def test_secret_only_rotation_invalidates_cached_key(framework):
    f, raw = framework
    old = Loader.load_site_config(frappe_module=f)
    raw["signing_secret"] = "synthetic-B-" * 4
    new = Loader.load_site_config(frappe_module=f)
    assert new.signing_secret == raw["signing_secret"]
    assert new is not old


def test_removed_secret_cannot_reuse_cached_key(framework):
    f, raw = framework
    Loader.load_site_config(frappe_module=f)
    del raw["signing_secret"]
    with pytest.raises(ConfigurationError):
        Loader.load_site_config(frappe_module=f)


def test_invalid_rotated_secret_cannot_reuse_cached_key(framework):
    f, raw = framework
    Loader.load_site_config(frappe_module=f)
    raw["signing_secret"] = "short"
    with pytest.raises(ConfigurationError):
        Loader.load_site_config(frappe_module=f)


def test_request_site_cannot_be_overridden(framework):
    f, _ = framework
    with pytest.raises(ConfigurationError):
        Loader.load_site_config(site_id="other-site", frappe_module=f)


@pytest.mark.parametrize("raw", [[], "secret-bearing-string", True, 7])
def test_non_object_section_is_safe_configuration_error(raw):
    f = SimpleNamespace(local=SimpleNamespace(site="test-site"),
                        get_site_config=lambda: {"lotus_fin_invoice_actions": raw})
    with pytest.raises(ConfigurationError):
        Loader.load_site_config(frappe_module=f)


def test_framework_exception_does_not_expose_secret():
    def broken():
        raise RuntimeError("private-secret-provider-detail")
    f = SimpleNamespace(local=SimpleNamespace(site="test-site"), get_site_config=broken)
    with pytest.raises(ConfigurationError) as caught:
        Loader.load_site_config(frappe_module=f)
    assert "private-secret-provider-detail" not in str(caught.value)
    assert caught.value.__suppress_context__


def test_configuration_repr_does_not_expose_signing_secret():
    raw = raw_config()
    config = Loader.load_from_dict(raw, "test-site")
    assert raw["signing_secret"] not in repr(config)
    assert raw["signing_secret"] not in str(config)


def test_mutated_cached_nested_policy_is_not_returned(framework):
    f, _ = framework
    first = Loader.load_site_config(frappe_module=f)
    first.allowed_capabilities.append("unauthorized.execute")
    next_config = Loader.load_site_config(frappe_module=f)
    assert "unauthorized.execute" not in next_config.allowed_capabilities


def test_connection_order_does_not_change_cache_identity(framework):
    f, raw = framework
    raw["connections"] = {"test-site": {"product_id": "lotus", "site_id": "test-site",
        "connection_id": "source", "connection_version": "v1", "allowed_companies": ["A"]}}
    first = Loader.load_site_config(frappe_module=f)
    raw["connections"]["test-site"] = dict(reversed(list(raw["connections"]["test-site"].items())))
    assert Loader.load_site_config(frappe_module=f) is first


@pytest.mark.parametrize("site", [True, 12, [], "   "])
def test_invalid_site_id_is_rejected(site):
    with pytest.raises(ConfigurationError):
        Loader.load_from_dict(raw_config(), site)
