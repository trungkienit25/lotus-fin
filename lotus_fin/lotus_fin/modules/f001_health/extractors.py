"""
Module F001 - Financial Health Ledger Extractors.
Extracts verified facts from P&L, AR, AP, and Trial Balance reports.
"""

from typing import Any, Dict, List, Optional
from lotus_fin.core.domain.calculators.pnl_extractor import extract_revenue_and_cogs
from lotus_fin.core.domain.calculators.ar_extractor import extract_ar_metrics
from lotus_fin.core.domain.calculators.ap_cash_extractor import extract_ap_and_cash


class HealthDataExtractor:
    """Consolidated extractor for F001 financial health ledger data."""

    @staticmethod
    def extract_pnl(pnl_data: Optional[List[Dict[str, Any]]]):
        return extract_revenue_and_cogs(pnl_data)

    @staticmethod
    def extract_ar(ar_data: Optional[List[Dict[str, Any]]]):
        return extract_ar_metrics(ar_data)

    @staticmethod
    def extract_ap_cash(
        ap_data: Optional[List[Dict[str, Any]]],
        tb_data: Optional[List[Dict[str, Any]]]
    ):
        return extract_ap_and_cash(ap_data, tb_data)
