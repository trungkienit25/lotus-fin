"""Legacy compatibility alias for F003 (AI003 Risk Signal Agent).

`lotus_fin.modules.f003_risk_signal.*` is the single canonical module identity.
Every `lotus_fin.risk_signal.*` import resolves to the SAME module object — the
canonical files are never re-executed under the legacy name — so both
spellings share one state and one set of classes, regardless of import order.
"""

import importlib
import pkgutil
import sys

_CANONICAL_PACKAGE = "lotus_fin.modules.f003_risk_signal"

_canonical_pkg = importlib.import_module(_CANONICAL_PACKAGE)

# Pre-alias every canonical submodule under the legacy name BEFORE anything
# can import `lotus_fin.risk_signal.<sub>`: without this, the import machinery
# would execute the canonical file again under the legacy module name,
# creating duplicate module objects and duplicate module-level state.
for _mi in pkgutil.iter_modules(_canonical_pkg.__path__):
    _canonical_sub = importlib.import_module(f"{_CANONICAL_PACKAGE}.{_mi.name}")
    sys.modules[f"{__name__}.{_mi.name}"] = _canonical_sub
    globals()[_mi.name] = _canonical_sub

# Re-export all canonical public symbols
for _attr in getattr(_canonical_pkg, "__all__", []):
    globals()[_attr] = getattr(_canonical_pkg, _attr)

__all__ = getattr(_canonical_pkg, "__all__", [])
