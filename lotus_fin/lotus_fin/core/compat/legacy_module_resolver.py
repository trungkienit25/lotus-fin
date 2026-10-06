"""
Lotus Fin - Legacy Module Virtual Bridge & Meta-Path Resolver.
Implements the Adapter & Bridge Design Patterns via Python PEP 302/451 MetaPathFinder.

Allows legacy namespaces:
- lotus_fin.ai004.*    -> lotus_fin.modules.f004_what_if.*
- lotus_fin.AI005.*    -> lotus_fin.modules.f005_financing.*
- lotus_fin.AI006.*    -> lotus_fin.modules.f006_repayment.*
- lotus_fin.AI007.*    -> lotus_fin.modules.f007_copilot.*
- lotus_fin.modules.f002_cashflow.* -> lotus_fin.modules.f002_cashflow.*
- lotus_fin.modules.f003_risk_signal.* -> lotus_fin.modules.f003_risk_signal.*

to resolve dynamically into canonical module instances in memory, eliminating
all physical duplicate/facade directories from the codebase.
"""

import importlib
import importlib.abc
import importlib.util
import logging
import sys
from typing import Dict, Optional, Sequence

_logger = logging.getLogger("lotus_fin.core.compat.legacy_resolver")

LEGACY_TO_CANONICAL_MAP: Dict[str, str] = {
    "lotus_fin.ai.observability": "lotus_fin.infrastructure.observability.observability",
    "lotus_fin.ai.financial_health": "lotus_fin.modules.f001_health.financial_health",
    "lotus_fin.ai.financial_snapshot": "lotus_fin.modules.f001_health.financial_snapshot",
    "lotus_fin.ai.explanation": "lotus_fin.modules.f001_health.explanation",
    "lotus_fin.ai": "lotus_fin.modules.f001_health",
    "lotus_fin.ai004": "lotus_fin.modules.f004_what_if",
    "lotus_fin.AI005": "lotus_fin.modules.f005_financing",
    "lotus_fin.AI006": "lotus_fin.modules.f006_repayment",
    "lotus_fin.AI007": "lotus_fin.modules.f007_copilot",
    "lotus_fin.cashflow": "lotus_fin.modules.f002_cashflow",
    "lotus_fin.risk_signal": "lotus_fin.modules.f003_risk_signal",
}


class VirtualModuleBridgeLoader(importlib.abc.Loader):
    """
    Bridge Loader (Bridge Pattern).
    Loads the canonical module and bridges it directly into sys.modules under
    the requested legacy fullname, ensuring single-instance identity across spellings.
    """

    def __init__(self, canonical_name: str):
        self.canonical_name = canonical_name

    def create_module(self, spec):
        # Delegate module creation to the canonical import
        return importlib.import_module(self.canonical_name)

    def exec_module(self, module):
        # Already executed when canonical was imported
        pass


class LegacyModuleMetaFinder(importlib.abc.MetaPathFinder):
    """
    Meta-Path Finder (Adapter Pattern).
    Intercepts imports for registered legacy prefixes and bridges them
    to the canonical package without requiring any physical files on disk.
    """

    def __init__(self, mappings: Optional[Dict[str, str]] = None):
        self._mappings = mappings or LEGACY_TO_CANONICAL_MAP

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[object] = None
    ) -> Optional[importlib.machinery.ModuleSpec]:
        for legacy_prefix, canonical_prefix in self._mappings.items():
            if fullname == legacy_prefix or fullname.startswith(legacy_prefix + "."):
                sub_path = fullname[len(legacy_prefix):]
                canonical_fullname = canonical_prefix + sub_path
                try:
                    canonical_mod = importlib.import_module(canonical_fullname)
                    spec = importlib.util.spec_from_loader(
                        fullname,
                        VirtualModuleBridgeLoader(canonical_fullname),
                        origin=getattr(canonical_mod, "__file__", "virtual")
                    )
                    # Support package traversal if canonical is a package
                    if hasattr(canonical_mod, "__path__"):
                        spec.submodule_search_locations = list(canonical_mod.__path__)
                    return spec
                except ModuleNotFoundError:
                    return None
        return None


def register_legacy_resolver() -> None:
    """Registers the Meta-Path finder in sys.meta_path if not already present."""
    for finder in sys.meta_path:
        if isinstance(finder, LegacyModuleMetaFinder):
            return
    sys.meta_path.insert(0, LegacyModuleMetaFinder())
    _logger.debug("Registered LegacyModuleMetaFinder into sys.meta_path")
