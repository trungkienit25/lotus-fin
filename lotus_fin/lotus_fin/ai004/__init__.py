"""Legacy compatibility alias for F004 (AI-F004 What-if Scenario Agent Package).

`lotus_fin.modules.f004_what_if.*` is the single canonical module identity.
Every `lotus_fin.ai004.*` import resolves to the SAME module object — the
canonical files are never re-executed under the legacy name — so both
spellings share one state and one set of classes, regardless of import order.
"""

import importlib
import pkgutil
import sys

_CANONICAL_PACKAGE = "lotus_fin.modules.f004_what_if"

_canonical_pkg = importlib.import_module(_CANONICAL_PACKAGE)

# Pre-alias every canonical submodule and subpackage under the legacy name
for _mi in pkgutil.walk_packages(_canonical_pkg.__path__, prefix=f"{_CANONICAL_PACKAGE}."):
    _canonical_sub = importlib.import_module(_mi.name)
    _legacy_name = _mi.name.replace(_CANONICAL_PACKAGE, __name__)
    sys.modules[_legacy_name] = _canonical_sub

# Also alias top-level children
for _mi in pkgutil.iter_modules(_canonical_pkg.__path__):
    _canonical_sub = importlib.import_module(f"{_CANONICAL_PACKAGE}.{_mi.name}")
    sys.modules[f"{__name__}.{_mi.name}"] = _canonical_sub
    globals()[_mi.name] = _canonical_sub

# Re-export all canonical public symbols
for _attr in getattr(_canonical_pkg, "__all__", []):
    globals()[_attr] = getattr(_canonical_pkg, _attr)

__all__ = getattr(_canonical_pkg, "__all__", [])
