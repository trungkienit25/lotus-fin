"""
Compatibility facade for ERPNextGateway.
Delegates directly to canonical lotus_fin.infrastructure.erpnext.erpnext_gateway.
"""

from lotus_fin.infrastructure.erpnext.erpnext_gateway import ERPNextGateway

__all__ = ["ERPNextGateway"]
