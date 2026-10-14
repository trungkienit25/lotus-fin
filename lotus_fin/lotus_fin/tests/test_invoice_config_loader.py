"""Tests for InvoiceActionsConfigLoader (Batch B3).

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §7.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from types import SimpleNamespace
import pytest
from lotus_fin.infrastructure.config.invoice_actions_config_loader import (
    ConfigurationError,
    InvoiceActionsConfigLoader,
)


VALID_RAW = {
    "enabled": True,
    "signing_key_id": "key_prod_01",
    "signing_secret": "a" * 32,
    "reference_ttl_seconds": 300,
    "deadline_ms": 5000,
    "page_size_default": 20,
    "page_size_max": 50,
    "allowed_capabilities": ["invoice.context", "invoice.search", "invoice.open"],
    "connections": {
        "site1": {
            "product_id": "lotus_fin",
            "site_id": "site1",
            "connection_id": "site1",
            "connection_version": "v1",
            "allowed_companies": ["Lotus Corp"],
        }
    },
}


def setup_function():
    InvoiceActionsConfigLoader.clear_cache()


def test_valid_approved_config():
    cfg = InvoiceActionsConfigLoader.load_from_dict(VALID_RAW, "site1")
    assert cfg.enabled is True
    assert cfg.signing_key_id == "key_prod_01"
    assert cfg.signing_secret == "a" * 32
    assert "site1" in cfg.connections


def test_missing_config():
    with pytest.raises(ConfigurationError, match="dictionary"):
        InvoiceActionsConfigLoader.load_from_dict(None, "site1")


def test_missing_site():
    with pytest.raises(ConfigurationError, match="Site ID"):
        InvoiceActionsConfigLoader.load_from_dict(VALID_RAW, "")


def test_unknown_keys_rejected():
    raw = {**VALID_RAW, "unapproved_admin_key": "injected"}
    with pytest.raises(ConfigurationError, match="Unapproved"):
        InvoiceActionsConfigLoader.load_from_dict(raw, "site1")


def test_missing_secret():
    raw = {k: v for k, v in VALID_RAW.items() if k != "signing_secret"}
    with pytest.raises(ConfigurationError, match="secret"):
        InvoiceActionsConfigLoader.load_from_dict(raw, "site1")


def test_short_secret():
    raw = {**VALID_RAW, "signing_secret": "too_short"}
    with pytest.raises(ConfigurationError, match="32"):
        InvoiceActionsConfigLoader.load_from_dict(raw, "site1")


def test_weak_development_secret_rejected_when_enabled():
    raw = {**VALID_RAW, "signing_secret": "12345678901234567890123456789012"}
    with pytest.raises(ConfigurationError, match="weak"):
        InvoiceActionsConfigLoader.load_from_dict(raw, "site1")


def test_connection_site_mismatch():
    with pytest.raises(ConfigurationError, match="mismatch"):
        InvoiceActionsConfigLoader.load_from_dict(VALID_RAW, "other_site")


def test_frappe_site_config_loader():
    fake_frappe = SimpleNamespace(
        local=SimpleNamespace(site="site1"),
        get_site_config=lambda: {"lotus_fin_invoice_actions": VALID_RAW},
    )
    cfg = InvoiceActionsConfigLoader.load_site_config(
        site_id="site1", frappe_module=fake_frappe
    )
    assert cfg.enabled is True
    assert cfg.signing_key_id == "key_prod_01"


def test_frappe_site_config_caching_and_rotation():
    fake_frappe = SimpleNamespace(
        local=SimpleNamespace(site="site1"),
        get_site_config=lambda: {"lotus_fin_invoice_actions": VALID_RAW},
    )
    cfg1 = InvoiceActionsConfigLoader.load_site_config(
        site_id="site1", frappe_module=fake_frappe
    )
    cfg2 = InvoiceActionsConfigLoader.load_site_config(
        site_id="site1", frappe_module=fake_frappe
    )
    assert cfg1 is cfg2  # Cached instance returned

    # Rotated config with new key
    rotated_raw = {**VALID_RAW, "signing_key_id": "key_prod_02"}
    fake_frappe.get_site_config = lambda: {"lotus_fin_invoice_actions": rotated_raw}
    cfg3 = InvoiceActionsConfigLoader.load_site_config(
        site_id="site1", frappe_module=fake_frappe
    )
    assert cfg3.signing_key_id == "key_prod_02"
    assert cfg3 is not cfg1


def test_cross_site_cache_isolation():
    fake_frappe = SimpleNamespace(
        local=SimpleNamespace(site="site1"),
        get_site_config=lambda: {"lotus_fin_invoice_actions": VALID_RAW},
    )
    cfg1 = InvoiceActionsConfigLoader.load_site_config(
        site_id="site1", frappe_module=fake_frappe
    )

    raw2 = {
        **VALID_RAW,
        "connections": {
            "site2": {
                "product_id": "lotus_fin",
                "site_id": "site2",
                "connection_id": "site2",
                "connection_version": "v1",
                "allowed_companies": ["Other Corp"],
            }
        },
    }
    fake_frappe2 = SimpleNamespace(
        local=SimpleNamespace(site="site2"),
        get_site_config=lambda: {"lotus_fin_invoice_actions": raw2},
    )
    cfg2 = InvoiceActionsConfigLoader.load_site_config(
        site_id="site2", frappe_module=fake_frappe2
    )
    assert cfg1 is not cfg2
    assert "site1" in cfg1.connections
    assert "site2" in cfg2.connections


def test_missing_lotus_section_fails_closed():
    fake_frappe = SimpleNamespace(
        local=SimpleNamespace(site="site1"),
        get_site_config=lambda: {"unrelated_key": 123},
    )
    with pytest.raises(ConfigurationError, match="absent"):
        InvoiceActionsConfigLoader.load_site_config(
            site_id="site1", frappe_module=fake_frappe
        )


def test_secret_not_leaked_in_exception():
    secret_val = "sensitive_super_secret_value_123456"
    raw = {**VALID_RAW, "signing_secret": secret_val, "deadline_ms": "not_an_int"}
    with pytest.raises(ConfigurationError) as exc_info:
        InvoiceActionsConfigLoader.load_from_dict(raw, "site1")
    assert secret_val not in str(exc_info.value)
