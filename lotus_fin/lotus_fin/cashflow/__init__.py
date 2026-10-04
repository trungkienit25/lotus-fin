"""Legacy compatibility alias for F002 (AI002 Cash-flow Forecast Copilot).

`lotus_fin.modules.f002_cashflow.*` is the single canonical module identity.
Every `lotus_fin.cashflow.*` import resolves to the SAME module object — the
canonical files are never re-executed under the legacy name — so both
spellings share one state (e.g. the AI002 cache store) and one set of
classes, regardless of import order.
"""

import importlib
import pkgutil
import sys

_CANONICAL_PACKAGE = "lotus_fin.modules.f002_cashflow"

_canonical_pkg = importlib.import_module(_CANONICAL_PACKAGE)

# Pre-alias every canonical submodule under the legacy name BEFORE anything
# can import `lotus_fin.cashflow.<sub>`: without this, the import machinery
# would execute the canonical file again under the legacy module name,
# creating duplicate module objects and duplicate module-level state.
for _mi in pkgutil.iter_modules(_canonical_pkg.__path__):
    _canonical_sub = importlib.import_module(f"{_CANONICAL_PACKAGE}.{_mi.name}")
    sys.modules[f"{__name__}.{_mi.name}"] = _canonical_sub
    globals()[_mi.name] = _canonical_sub
