"""AI003 typed source-provider interfaces (S1).

Domain and evaluation code depend on these protocols and DTOs, never on Frappe
report internals (DIP). Concrete adapters live in sources.py (S2) and bind to
the approved public boundaries:
- AI001 public snapshot: lotus_fin.api.ai_insights.get_financial_snapshot
- AP report boundary:   lotus_fin.api.key_reports.extract_key_report_data
- PI schedule metadata: frappe.get_doc('Purchase Invoice', ...) with explicit
  checked-user permission gate (SSOT §17.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping, Optional, Protocol, Tuple


@dataclass(frozen=True)
class ARSnapshot:
    """Typed view of one AI001 public financial snapshot for one cutoff."""

    status: str  # AI001 envelope status: OK | PARTIAL | ...
    contract_version: str
    formula_version: str
    company: str
    currency: str
    as_of: date
    total_ar: Optional[Decimal]
    overdue_ratio: Optional[Decimal]
    ar_metrics_available: bool
    snapshot_id: Optional[str] = None
    source_hash: str = ""
    limitations: Tuple[str, ...] = ()


@dataclass(frozen=True)
class APRow:
    """One normalized Accounts Payable report transaction row (SSOT §16.5).

    Company is NOT taken from the row — the authorized envelope is the company
    provenance (gold evidence: report rows carry no company field).
    """

    voucher_type: str
    voucher_no: str
    party_account: str
    outstanding_amount: Decimal
    due_date_raw: object  # original typed field, preserved verbatim
    due_date: Optional[date]  # None when missing (coverage decision upstream)
    currency: str
    party_ref: Optional[str] = None
    posting_date: Optional[date] = None


@dataclass(frozen=True)
class APReportSnapshot:
    """Validated envelope + normalized rows for the fixed accounts_payable report."""

    status: str
    report_key: str
    report_name: str
    company: str
    as_of: date
    filters_applied: Mapping  # exact echo from the envelope (server-owned filters)
    rows: Tuple[APRow, ...]
    source_hash: str = ""
    limitations: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduleMetadata:
    """Payment-schedule preflight result for one parent invoice (SSOT §17.4).

    count_basis stays distinct from observation identity; no allocation IDs are
    invented — P0 supports only 0/1 schedules and rejects >1 fail-closed.
    """

    voucher_type: str
    voucher_no: str
    company: str
    docstatus: int
    schedule_count: int
    header_due_date: Optional[date]
    child_due_dates: Tuple[Optional[date], ...] = ()


class ARSnapshotProvider(Protocol):
    """Fetches the AI001 public snapshot for an explicit cutoff, checked-user context."""

    def fetch(self, company: str, cutoff: date) -> ARSnapshot: ...


class APReportProvider(Protocol):
    """Fetches the fixed accounts_payable report through the approved boundary."""

    def fetch(self, company: str, as_of: date) -> APReportSnapshot: ...


class ScheduleMetadataProvider(Protocol):
    """Permission-checked parent-invoice schedule metadata; denial must fail FORBIDDEN."""

    def get(self, voucher_no: str, expected_company: str) -> ScheduleMetadata: ...
