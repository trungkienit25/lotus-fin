"""AI003 source adapters (S2) — the ONLY Frappe-touching layer of the engine.

Approved public boundaries (SSOT §17.4):
- AR: lotus_fin.api.ai_insights.get_financial_snapshot — called twice with
  explicit dates (current + baseline cutoff), contract 1.0.0 / formula 2026.1
  pinned, Decimal(str(published_value)). AI001 endpoint defaults (FY2020) are
  bypassed with explicit periods; the comparison block is never used.
- AP: lotus_fin.api.key_reports.extract_key_report_data(report_key=
  "accounts_payable", filters=<pinned §16.5 recipe>, company=<verified>).
  The client can never choose report, filters, DocType, SQL, currency or
  Finance Book; the server owns them all.
- Schedule metadata: frappe.get_doc('Purchase Invoice', ...) with an explicit
  checked-user permission gate (get_doc alone is NOT authorization).

All failures are typed SourceFailure(status, reason_code, sanitized_message).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Mapping, Optional, Tuple

from lotus_fin.modules.f003_risk_signal.contracts import (
    ReasonCode,
    Status,
)
from lotus_fin.modules.f003_risk_signal.interfaces import (
    APReportSnapshot,
    APRow,
    ARSnapshot,
    ScheduleMetadata,
)
from lotus_fin.modules.f003_risk_signal.provenance import (
    SourceFailure,
    canonical_payload_hash,
    parse_amount,
    sanitize_reason,
)

# --- Approved public boundary pins -------------------------------------------

AR_CONTRACT_VERSION = "1.0.0"
AR_FORMULA_VERSION = "2026.1"
AR_METRIC_TOTAL = "ar_outstanding"
AR_METRIC_RATIO = "overdue_ar_ratio"

AP_REPORT_KEY = "accounts_payable"
AP_REPORT_NAME = "Accounts Payable"
AP_PINNED_FILTERS: Dict[str, Any] = {
    "based_on_payment_terms": 0,
    "in_party_currency": 0,
    "show_future_payments": 0,
    "ageing_based_on": "Due Date",
    "age_as_on": "Report Date",
}

SUPPORTED_AP_SOURCE_DOC_TYPES = ("Purchase Invoice",)


def _ai001_snapshot_callable():
    from lotus_fin.api.ai_insights import get_financial_snapshot

    return get_financial_snapshot


def _ap_report_callable():
    from lotus_fin.api.key_reports import extract_key_report_data

    return extract_key_report_data


def _frappe_module():
    import frappe

    return frappe


# --- AR provider --------------------------------------------------------------


class AI001PublicARProvider:
    """ARSnapshotProvider over the AI001 public snapshot for one explicit cutoff."""

    def fetch(self, company: str, cutoff: date) -> ARSnapshot:
        snapshot_callable = _ai001_snapshot_callable()
        try:
            envelope = snapshot_callable(
                company=company,
                period_start="%04d-01-01" % cutoff.year,
                period_end=cutoff.isoformat(),
                as_of=cutoff.isoformat(),
                currency="VND",
                comparison=None,
                include_explanation=False,
            )
        except SourceFailure:
            raise
        except Exception as exc:  # boundary-level failure -> sanitized typed error
            raise SourceFailure(
                Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, sanitize_reason(exc)
            ) from exc
        return _parse_ai001_envelope(envelope, cutoff)


def _parse_ai001_envelope(envelope: Mapping, cutoff: date) -> ARSnapshot:
    if not isinstance(envelope, Mapping):
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "AI001 envelope not a mapping")
    status = envelope.get("status")
    company = envelope.get("company")
    currency = envelope.get("currency")
    if status == Status.FORBIDDEN.value:
        raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "snapshot denied")
    if status == Status.SOURCE_ERROR.value:
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, "snapshot source error")
    if status not in (Status.OK.value, "PARTIAL"):
        # INSUFFICIENT_DATA / anything else: no valid observation from this source.
        raise SourceFailure(Status.INCONCLUSIVE, ReasonCode.SOURCE_UNAVAILABLE, "snapshot not available")
    version = envelope.get("contract_version")
    if version != AR_CONTRACT_VERSION:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.UNSUPPORTED_SOURCE_VERSION,
            "AI001 contract version mismatch",
        )
    metrics = _metric_map(envelope.get("metrics"))
    total_entry = metrics.get(AR_METRIC_TOTAL)
    ratio_entry = metrics.get(AR_METRIC_RATIO)
    formula = (total_entry or {}).get("formula_version") or envelope.get("formula_version")
    if formula != AR_FORMULA_VERSION:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.UNSUPPORTED_SOURCE_VERSION,
            "AI001 formula version mismatch",
        )
    total_available = bool(total_entry and total_entry.get("status") == "AVAILABLE")
    ratio_available = bool(ratio_entry and ratio_entry.get("status") == "AVAILABLE")
    total = _published_decimal(total_entry.get("value")) if total_available else None
    ratio = _published_decimal(ratio_entry.get("value")) if ratio_available else None
    limitations = tuple(str(item) for item in (envelope.get("limitations") or ()))
    return ARSnapshot(
        status=str(status),
        contract_version=str(version),
        formula_version=str(formula),
        company=str(company) if company else "",
        currency=str(currency) if currency else "",
        as_of=cutoff,
        total_ar=total,
        overdue_ratio=ratio,
        ar_metrics_available=total_available and ratio_available,
        snapshot_id=envelope.get("snapshot_id"),
        source_hash=canonical_payload_hash(
            {
                "kind": "AI001_METRIC",
                "company": company,
                "cutoff": cutoff.isoformat(),
                "snapshot_id": envelope.get("snapshot_id"),
                "total": str(total) if total is not None else None,
                "ratio": str(ratio) if ratio is not None else None,
            }
        ),
        limitations=limitations,
    )


def _metric_map(metrics) -> Dict[str, Mapping]:
    result: Dict[str, Mapping] = {}
    if isinstance(metrics, list):
        for entry in metrics:
            if isinstance(entry, Mapping) and entry.get("metric_id"):
                result[str(entry["metric_id"])] = entry
    return result


def _published_decimal(raw) -> Optional[Decimal]:
    """Decimal(str(published_value)); nonfinite/None -> None (caller decides)."""
    if raw is None:
        return None
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "non-numeric published metric"
        ) from exc
    if not value.is_finite():
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "non-finite published metric"
        )
    return value


def fetch_ar_pair(
    provider, company: str, current_cutoff: date, baseline_cutoff: Optional[date] = None
) -> Tuple[ARSnapshot, Optional[ARSnapshot]]:
    """Fetch current + baseline AI001 snapshots with typed, role-aware failures.

    Gold-pinned role semantics:
    - baseline envelope unavailable -> INCONCLUSIVE/HISTORY_INSUFFICIENT
      (absence of a valid prior observation);
    - baseline verified zero denominator -> INCONCLUSIVE/BASELINE_DENOMINATOR_INVALID;
    - current verified zero denominator -> INCONCLUSIVE/CURRENT_DENOMINATOR_INVALID;
    - genuine source failure -> SOURCE_ERROR (never masked as history).
    """
    current = _fetch_validated(provider, company, current_cutoff, role="current")
    if baseline_cutoff is None:
        return current, None
    baseline = _fetch_validated(provider, company, baseline_cutoff, role="baseline")
    return current, baseline


def _fetch_validated(provider, company: str, cutoff: date, role: str) -> ARSnapshot:
    try:
        snapshot = provider.fetch(company, cutoff)
    except SourceFailure as failure:
        if role == "baseline" and failure.status is Status.INCONCLUSIVE:
            # Source reports no usable observation for the prior cutoff.
            raise SourceFailure(
                Status.INCONCLUSIVE, ReasonCode.HISTORY_INSUFFICIENT, "no valid baseline observation"
            ) from failure
        raise
    if snapshot.company and snapshot.company != company:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "snapshot company mismatch"
        )
    if snapshot.currency and snapshot.currency not in ["VND", "USD"]:
        raise SourceFailure(
            Status.VALIDATION_ERROR,
            ReasonCode.UNSUPPORTED_COMPANY_CURRENCY,
            f"company accounting currency '{snapshot.currency}' is not supported (expected USD or VND)",
        )
    if not snapshot.ar_metrics_available:
        if role == "baseline":
            raise SourceFailure(
                Status.INCONCLUSIVE, ReasonCode.HISTORY_INSUFFICIENT, "baseline AR metrics unavailable"
            )
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, "current AR metrics unavailable"
        )
    if snapshot.total_ar is None or snapshot.overdue_ratio is None:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "AR metric values missing"
        )
    if snapshot.total_ar == 0:
        reason = (
            ReasonCode.CURRENT_DENOMINATOR_INVALID
            if role == "current"
            else ReasonCode.BASELINE_DENOMINATOR_INVALID
        )
        raise SourceFailure(Status.INCONCLUSIVE, reason, "verified zero AR denominator")
    return snapshot


# --- AP provider --------------------------------------------------------------


class APReportAdapter:
    """APReportProvider over the fixed accounts_payable key-report boundary."""

    def fetch(self, company: str, as_of: date) -> APReportSnapshot:
        report_callable = _ap_report_callable()
        filters = {**AP_PINNED_FILTERS, "report_date": as_of.isoformat()}
        try:
            envelope = report_callable(report_key=AP_REPORT_KEY, filters=filters, company=company)
        except SourceFailure:
            raise
        except Exception as exc:
            frappe = _frappe_module()
            perm_err = getattr(frappe, "PermissionError", PermissionError)
            if isinstance(exc, (perm_err, PermissionError)) or type(exc).__name__ in ("PermissionError", "_PermissionError"):
                raise SourceFailure(
                    Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, sanitize_reason(exc)
                ) from exc
            raise SourceFailure(
                Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, sanitize_reason(exc)
            ) from exc
        return _parse_ap_envelope(envelope, company, as_of)


def _parse_ap_envelope(envelope: Mapping, company: str, as_of: date) -> APReportSnapshot:
    if not isinstance(envelope, Mapping):
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "AP envelope not a mapping")
    status = envelope.get("status")
    if status == Status.FORBIDDEN.value:
        raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "report denied")
    if status != "success":
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, "report not available")
    envelope_company = envelope.get("company")
    if envelope_company != company:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "report company mismatch"
        )
    report_name = envelope.get("report_name")
    if report_name != AP_REPORT_NAME:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.UNSUPPORTED_SOURCE_VERSION, "unexpected report identity"
        )
    applied = envelope.get("filters_applied") or {}
    if applied.get("company") != company:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "envelope company filter mismatch"
        )
    for key, value in AP_PINNED_FILTERS.items():
        if applied.get(key) != value:
            raise SourceFailure(
                Status.SOURCE_ERROR,
                ReasonCode.INCONSISTENT_DATA,
                "report filter drift on %s" % key,
            )
    if applied.get("report_date") != as_of.isoformat():
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "report cutoff mismatch"
        )
    rows = envelope.get("data")
    if not isinstance(rows, list):
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "report data missing")
    normalized = tuple(_normalize_ap_row(raw, index) for index, raw in enumerate(rows))
    source_hash = canonical_payload_hash(
        {
            "kind": "ERP_AP_REPORT",
            "report_key": AP_REPORT_KEY,
            "company": company,
            "cutoff": as_of.isoformat(),
            "filters": {k: applied.get(k) for k in sorted(set(AP_PINNED_FILTERS) | {"report_date"})},
            "row_digest": canonical_payload_hash(
                [
                    {
                        "voucher_type": getattr(r, "voucher_type", None),
                        "voucher_no": getattr(r, "voucher_no", None),
                        "party_account": getattr(r, "party_account", None),
                        "amount": str(getattr(r, "outstanding_amount", "")),
                        "due": str(getattr(r, "due_date_raw", "")),
                    }
                    for r in normalized
                ]
            ),
        }
    )
    return APReportSnapshot(
        status=str(status),
        report_key=AP_REPORT_KEY,
        report_name=str(report_name),
        company=company,
        as_of=as_of,
        filters_applied=dict(applied),
        rows=normalized,
        source_hash=source_hash,
    )


def _normalize_ap_row(raw: Mapping, index: int) -> APRow:
    if not isinstance(raw, Mapping):
        raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "report row not a mapping")
    row_label = "row %d" % index
    voucher_type = raw.get("voucher_type")
    voucher_no = raw.get("voucher_no") or raw.get("name")
    party_account = raw.get("party_account") or raw.get("account")
    if not voucher_type or not voucher_no or not party_account:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.SOURCE_INVALID,
            "AP %s lacks voucher/account identity" % row_label,
        )
    amount = parse_amount(raw.get("outstanding"), row_label)
    currency = raw.get("currency")  # may be absent; envelope company currency is the provenance
    due_raw = raw.get("due_date")
    due_date = _parse_due_date(due_raw, row_label)
    posting_raw = raw.get("posting_date")
    posting = _parse_due_date(posting_raw, row_label, required=False) if posting_raw else None
    return APRow(
        voucher_type=str(voucher_type),
        voucher_no=str(voucher_no),
        party_account=str(party_account),
        outstanding_amount=amount,
        due_date_raw=due_raw,
        due_date=due_date,
        currency=str(currency) if currency else "",
        party_ref=str(raw["party"]) if raw.get("party") else None,
        posting_date=posting,
    )


def _parse_due_date(raw, row_label: str, required: bool = True) -> Optional[date]:
    """Missing (None/'') -> None coverage decision; malformed -> SOURCE_ERROR.

    Datetime values are normalized to their date part (PB-DATA-01-DATETIME
    convention: compare against the accounting cutoff on a date-only basis).
    """
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if required:
            return None  # missing: coverage decision upstream (positive rows only)
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise SourceFailure(
            Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "malformed due date on %s" % row_label
        ) from exc


# --- Schedule metadata provider ------------------------------------------------


class FrappeScheduleMetadataProvider:
    """Permission-checked Purchase Invoice parent metadata (SSOT §17.4).

    get_doc alone is NOT authorization: an explicit checked-user read-permission
    gate runs first, then company verification. Denial, nonexistence and
    cross-company references all collapse to the same generic FORBIDDEN.
    """

    def __init__(self, checked_user: str) -> None:
        if not checked_user:
            raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "no authenticated user")
        self.checked_user = checked_user

    def get(self, voucher_no: str, expected_company: str) -> ScheduleMetadata:
        frappe = _frappe_module()
        try:
            doc = frappe.get_doc("Purchase Invoice", voucher_no)
        except Exception as exc:  # missing and denied are indistinguishable by design
            raise SourceFailure(
                Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, sanitize_reason(exc)
            ) from exc
        try:
            permitted = doc.has_permission("read", user=self.checked_user)
        except Exception as exc:
            raise SourceFailure(
                Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, sanitize_reason(exc)
            ) from exc
        if not permitted:
            raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "metadata read denied")
        company = getattr(doc, "company", None)
        if company != expected_company:
            raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "metadata company mismatch")
        if getattr(doc, "docstatus", 0) != 1:
            raise SourceFailure(
                Status.SOURCE_ERROR, ReasonCode.SOURCE_INVALID, "parent invoice not submitted"
            )
        schedule = doc.get("payment_schedule") or []
        children = []
        for child in schedule:
            child_due = getattr(child, "due_date", None)
            if isinstance(child_due, datetime):
                child_due = child_due.date()
            children.append(child_due)
        header_due = getattr(doc, "due_date", None)
        if isinstance(header_due, datetime):
            header_due = header_due.date()
        return ScheduleMetadata(
            voucher_type="Purchase Invoice",
            voucher_no=voucher_no,
            company=str(company),
            docstatus=int(doc.docstatus),
            schedule_count=len(schedule),
            header_due_date=header_due,
            child_due_dates=tuple(children),
        )
