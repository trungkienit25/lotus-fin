"""
Lotus Fin AI001 - FinancialSnapshot & EvidenceRef Engine (Facade).
Decoupled facade delegating to Core Clean Architecture use cases and calculators.
"""

from typing import Any, Callable, Dict, List, Optional
from lotus_fin.core.domain.calculators.pnl_extractor import parse_pnl_data, _to_decimal as to_decimal
from lotus_fin.core.domain.calculators.ar_extractor import parse_ar_data
from lotus_fin.core.domain.calculators.ap_cash_extractor import parse_ap_data, parse_cash_balance
from lotus_fin.core.domain.entities.evidence import EvidenceRef
from lotus_fin.core.use_cases.snapshot_coordinator import SnapshotCoordinator

CONTRACT_VERSION = "1.0.0"
FEATURE_ID = "AI001"
FORMULA_VERSION = "2026.1"

REPORT_ALLOWLIST = {
    "profit_and_loss": "Profit and Loss Statement",
    "general_ledger": "General Ledger",
    "accounts_receivable": "Accounts Receivable",
    "accounts_payable": "Accounts Payable",
    "trial_balance": "Trial Balance",
    "cash_flow": "Cash Flow"
}


def generate_evidence_ref(
    source_type: str,
    source_name: str,
    company: str,
    filters: Dict[str, Any],
    as_of: Optional[str] = None,
    raw_payload: Optional[Any] = None,
    source_record_id: Optional[str] = None,
    record_count: Optional[int] = None
) -> Dict[str, Any]:
    """Constructs EvidenceRef dictionary conforming to Data Strategy §6."""
    return EvidenceRef.create(
        source_type=source_type,
        source_name=source_name,
        company=company,
        filters=filters,
        as_of=as_of,
        raw_payload=raw_payload,
        source_record_id=source_record_id,
        record_count=record_count
    ).to_dict()


def build_financial_snapshot(
    company: str,
    period_start: str,
    period_end: str,
    as_of: Optional[str] = None,
    currency: str = "VND",
    correlation_id: Optional[str] = None,
    comparison: Optional[str] = None,
    raw_sources: Optional[Dict[str, Any]] = None,
    source_fetcher: Optional[Callable[..., Any]] = None,
    user: Optional[str] = None,
    include_explanation: bool = False,
    llm_provider: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Builds the FinancialSnapshot + EvidenceRefs output envelope according to AI001 Feature Freeze.
    Delegates to SnapshotCoordinator in Clean Core architecture.
    """
    coordinator = SnapshotCoordinator()
    return coordinator.build_snapshot(
        company=company,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of,
        currency=currency,
        correlation_id=correlation_id,
        comparison=comparison,
        raw_sources=raw_sources,
        source_fetcher=source_fetcher,
        user=user,
        include_explanation=include_explanation,
        llm_provider=llm_provider
    )
