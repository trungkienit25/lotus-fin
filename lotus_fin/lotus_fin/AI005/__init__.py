"""Legacy compatibility alias for F005 (AI-F005 Financing Decision Support Module).

`lotus_fin.modules.f005_financing.*` is the single canonical module identity.
Every `lotus_fin.AI005.*` import resolves to the SAME module object — the
canonical files are never re-executed under the legacy name — so both
spellings share one state and one set of classes, regardless of import order.
"""

import importlib
import pkgutil
import sys

_CANONICAL_PACKAGE = "lotus_fin.modules.f005_financing"

_canonical_pkg = importlib.import_module(_CANONICAL_PACKAGE)

# Pre-alias every canonical submodule under the legacy name
for _mi in pkgutil.iter_modules(_canonical_pkg.__path__):
    _canonical_sub = importlib.import_module(f"{_CANONICAL_PACKAGE}.{_mi.name}")
    sys.modules[f"{__name__}.{_mi.name}"] = _canonical_sub
    globals()[_mi.name] = _canonical_sub

# Re-export all canonical public symbols
for _attr in getattr(_canonical_pkg, "__all__", []):
    globals()[_attr] = getattr(_canonical_pkg, _attr)

# Also explicitly expose key legacy classes on AI005 module directly
_models = sys.modules.get(f"{_CANONICAL_PACKAGE}.models")
if _models:
    for _m_name in getattr(_models, "__all__", []):
        globals()[_m_name] = getattr(_models, _m_name)

_matcher = sys.modules.get(f"{_CANONICAL_PACKAGE}.matcher")
if _matcher:
    globals()["FinancingDecisionEngine"] = getattr(_matcher, "FinancingDecisionEngine", None)

_catalog = sys.modules.get(f"{_CANONICAL_PACKAGE}.catalog")
if _catalog:
    globals()["get_active_catalog"] = getattr(_catalog, "get_active_catalog", None)
    globals()["get_catalog"] = getattr(_catalog, "get_catalog", None)

__all__ = getattr(_canonical_pkg, "__all__", [])
