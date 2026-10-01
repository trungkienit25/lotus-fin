"""
Lotus Fin AI005 - Catalog Facade.
Re-exports catalog repository from lotus_fin.modules.f005_financing.catalog.
"""

from lotus_fin.modules.f005_financing.catalog import (
    get_catalog,
    get_active_catalog,
    get_product_by_id,
    DEFAULT_FINANCING_CATALOG
)

__all__ = [
    "get_catalog",
    "get_active_catalog",
    "get_product_by_id",
    "DEFAULT_FINANCING_CATALOG"
]

