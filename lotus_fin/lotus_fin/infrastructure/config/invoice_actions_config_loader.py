"""Lotus-owned Frappe Configuration Loader for Invoice Actions.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §7.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Any, Dict, Optional, Tuple
import hashlib
import json
from pydantic import ValidationError
from lotus_fin.infrastructure.config.invoice_actions_config import InvoiceActionsConfig


class ConfigurationError(Exception):
    """Strict configuration failure; details never expose secret keys."""
    pass


class InvoiceActionsConfigLoader:
    """Secure, site-isolated configuration loader.
    
    Fails closed when configuration or signing secret is absent or malformed.
    """

    _site_cache: Dict[str, Tuple[str, InvoiceActionsConfig]] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._site_cache.clear()

    @classmethod
    def load_from_dict(cls, raw_config: Any, site_id: str) -> InvoiceActionsConfig:
        """Validate and build InvoiceActionsConfig strictly bound to site_id.
        
        Rejects unapproved extra keys, weak secrets, and invalid schemas.
        """
        if not isinstance(raw_config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        if not isinstance(site_id, str) or not site_id.strip():
            raise ConfigurationError("Site ID is required and must be a string")

        allowed_keys = {
            "enabled", "signing_key_id", "signing_secret", "reference_ttl_seconds",
            "deadline_ms", "page_size_default", "page_size_max", "allowed_capabilities",
            "connections",
        }
        extra_keys = set(raw_config.keys()) - allowed_keys
        if extra_keys:
            raise ConfigurationError("Unapproved configuration keys")

        secret = raw_config.get("signing_secret")
        if not secret or not isinstance(secret, str) or len(secret) < 32:
            raise ConfigurationError("Signing secret is missing, invalid, or shorter than 32 characters")

        weak_secrets = {
            "12345678901234567890123456789012",
            "development_secret_key_change_in_production",
            "default_secret_key_at_least_32_bytes_long",
        }
        if secret in weak_secrets and raw_config.get("enabled") is True:
            raise ConfigurationError("Refusing weak development secret when enabled")

        connections = raw_config.get("connections", {})
        if isinstance(connections, dict):
            for conn_key, conn_val in connections.items():
                if isinstance(conn_val, dict):
                    conn_site = conn_val.get("site_id")
                    if conn_site and conn_site != site_id:
                        raise ConfigurationError(f"Connection site mismatch: expected {site_id}, got {conn_site}")

        try:
            config = InvoiceActionsConfig(**raw_config)
        except ValidationError:
            raise ConfigurationError("Configuration schema validation failed") from None

        return config

    @classmethod
    def load_site_config(
        cls,
        site_id: Optional[str] = None,
        frappe_module: Optional[Any] = None,
        force_reload: bool = False,
    ) -> InvoiceActionsConfig:
        """Load configuration from Frappe site configuration infrastructure.
        
        Fails closed if Frappe is absent or site is not configured.
        """
        f = frappe_module
        if f is None:
            try:
                import frappe as f  # type: ignore
            except ImportError:
                raise ConfigurationError("Frappe framework infrastructure unavailable")

        active_site = getattr(getattr(f, "local", None), "site", None)
        if site_id is not None and active_site is not None and site_id != active_site:
            raise ConfigurationError("Requested site differs from active request site")
        current_site = site_id
        if not current_site:
            current_site = getattr(getattr(f, "local", None), "site", None) if f else None
        if not current_site:
            raise ConfigurationError("Cannot resolve current site from request context")

        site_conf = {}
        if hasattr(f, "get_site_config"):
            try:
                site_conf = f.get_site_config() or {}
            except Exception:
                raise ConfigurationError("Failed to read site config from framework") from None
        elif hasattr(f, "conf"):
            site_conf = dict(f.conf or {})

        if not isinstance(site_conf, dict):
            raise ConfigurationError("Site configuration must be a dictionary")
        raw = site_conf.get("lotus_fin_invoice_actions")
        if raw is None:
            raise ConfigurationError(f"Configuration key 'lotus_fin_invoice_actions' absent for site {current_site}")

        # Validate every request, including secret removal/rotation. Only a private
        # digest is retained; raw key material is never printed or logged.
        cfg = cls.load_from_dict(raw, current_site)
        fp_input = json.dumps(cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(fp_input.encode()).hexdigest()
        if not force_reload and current_site in cls._site_cache:
            cached_fp, cached_cfg = cls._site_cache[current_site]
            cached_input = json.dumps(cached_cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
            if cached_fp == fingerprint and cached_input == fp_input:
                return cached_cfg

        cls._site_cache[current_site] = (fingerprint, cfg)
        return cfg
