__version__ = "0.0.1"

# Automatically activate OOP Legacy Module Resolver (Meta-Path Finder)
from lotus_fin.core.compat.legacy_module_resolver import register_legacy_resolver
register_legacy_resolver()


