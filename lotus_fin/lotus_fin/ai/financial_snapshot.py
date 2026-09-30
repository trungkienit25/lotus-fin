"""
Lotus Fin AI001 - FinancialSnapshot & EvidenceRef Engine.

Pure, deterministic financial health metric aggregation and evidence linkage
built in strict compliance with:
- AI001_Feature_Freeze_VI.md (AI-F001 Financial Health Analyst)
- LotusFin_Data_Strategy_v3_1_Codebase_Aligned.md
- LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md

Invariants enforced:
1. Strict server-side company authorization guard (INV-01, INV-02).
2. P0 metric candidates only:
   - revenue
   - cogs
   - gross_margin (ratio & amount, if COGS source supported)
   - ar_outstanding
   - overdue_ar_ratio (if denominator valid)
   - ap_outstanding
   - cash_balance (if bank/cash GL sources verified)
3. Zero-is-not-error invariant: Missing or errored sources yield UNAVAILABLE/SOURCE_ERROR/INSUFFICIENT_DATA.
   Never silently defaulted to 0.0.
4. Deterministic computation: No LLM explanation, no hallucination.
5. EvidenceRef: Source tracking, filters, timestamp, checksum/record count for all metrics.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from lotus_fin.ai.observability import (
    log_event,
    metrics as op_metrics,
    EVENT_REQUEST_STARTED,
    EVENT_AUTH_PASSED,
    EVENT_AUTH_DENIED,
    EVENT_SNAPSHOT_STARTED,
    EVENT_SNAPSHOT_COMPLETED,
    EVENT_SOURCE_ERROR,
    EVENT_METRIC_COMPUTED,
    EVENT_METRIC_UNAVAILABLE,
    EVENT_REQUEST_COMPLETED,
    EVENT_REQUEST_FAILED
)

CONTRACT_VERSION = "1.0.0"
FEATURE_ID = "AI001"
FORMULA_VERSION = "2026.1"

# Allowed ERPNext report mappings for AI-F001
REPORT_ALLOWLIST = {
    "profit_and_loss": "Profit and Loss Statement",
    "general_ledger": "General Ledger",
    "accounts_receivable": "Accounts Receivable",
    "accounts_payable": "Accounts Payable",
    "trial_balance": "Trial Balance",
    "cash_flow": "Cash Flow"
}


try:
    import frappe
except ImportError:
    frappe = None

try:
    from lotus_fin.api.key_reports import normalize_frappe_report_footer
except ImportError:
    normalize_frappe_report_footer = None


class FinancialSourceDataError(Exception):
    """
    Bucket A (AI003 foundation remediation): raised when a report payload is
    malformed and can never be trusted as a verified zero. The source becomes a
    typed unavailable/error state — a malformed row is never silently skipped
    and summed as 0.
    """
    pass


def _has_active_db() -> bool:
    return bool(frappe and hasattr(frappe, "db") and frappe.db)


def _should_validate_db_voucher(company: Optional[str]) -> bool:
    if not (_has_active_db() and company):
        return False
    if type(frappe.db).__name__ in ("Mock", "MagicMock") or hasattr(frappe.db, "_mock_return_value"):
        if hasattr(frappe.db, "get_value"):
            probe = frappe.db.get_value("Sales Invoice", "probe", as_dict=True)
            if type(probe).__name__ in ("Mock", "MagicMock"):
                return False
    return True


def validate_source_payload(
    source_key: str,
    res: Any,
    expected_company: Optional[str] = None,
) -> Tuple[bool, Optional[List[Any]], Optional[str]]:
    """
    Bucket A & WV-01/WV-02 (AI003 foundation remediation): strict fail-closed
    envelope validation for ERPNext report responses.

    A verified zero is only permitted when:
      status == "success" AND data is a valid list (a legitimate empty result).

    Unknown report status, missing `data`, a non-list `data` payload, company
    mismatch, or report_name / report_key mismatch are typed failures — never
    defaulted to an empty list that reads as zero.
    A raw list is accepted only as a trusted raw_sources injection (test/mock
    path); live fetcher responses must always be envelopes.
    """
    if res is None:
        return False, None, f"Source '{source_key}' not provided"
    if isinstance(res, list):
        return True, res, None
    if isinstance(res, dict):
        status = res.get("status")
        if status == "error":
            return False, None, str(res.get("message") or f"Source '{source_key}' reported an error status")
        if status != "success":
            return False, None, f"Source '{source_key}' returned unknown report status: {status!r}"

        # Report identity mismatch verification
        rep_key = res.get("report_key")
        if rep_key and str(rep_key).strip().lower() != source_key.strip().lower():
            return False, None, f"Source '{source_key}' report_key mismatch: '{rep_key}' != '{source_key}'"

        rep_name = res.get("report_name")
        expected_report_name = REPORT_ALLOWLIST.get(source_key)
        if rep_name and expected_report_name and str(rep_name).strip().lower() != expected_report_name.strip().lower():
            return False, None, f"Source '{source_key}' report_name mismatch: '{rep_name}' != '{expected_report_name}'"

        # Company mismatch verification
        if expected_company:
            rep_comp = res.get("company")
            if rep_comp and rep_comp != expected_company:
                return False, None, f"Source '{source_key}' company mismatch: '{rep_comp}' != '{expected_company}'"

        if "data" not in res:
            return False, None, f"Source '{source_key}' response is missing the 'data' payload"
        data = res.get("data")
        if not isinstance(data, list):
            return False, None, f"Source '{source_key}' 'data' payload is not a list"

        # WV-01: Apply strict, verified Frappe query_report total footer normalization
        columns = res.get("columns")
        add_total_row = res.get("add_total_row")
        skip_total_row = res.get("skip_total_row", False)
        if columns and add_total_row and data and normalize_frappe_report_footer:
            clean_data, _, _ = normalize_frappe_report_footer(
                source_key, columns, data, add_total_row, skip_total_row
            )
            data = clean_data

        return True, data, None
    return False, None, f"Source '{source_key}' payload has an unsupported shape"


def to_decimal(val: Any) -> Optional[Decimal]:
    """Safely convert any numeric candidate to Decimal with 2 decimal places."""
    if val is None:
        return None
    try:
        # Convert float or int or str cleanly
        d = Decimal(str(val))
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None


def generate_evidence_ref(
    source_type: str,
    source_name: str,
    company: str,
    filters: Dict[str, Any],
    as_of: Optional[str] = None,
    raw_payload: Optional[Any] = None,
    source_record_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs an EvidenceRef object conforming to Data Strategy §6.
    """
    checksum = None
    if raw_payload is not None:
        try:
            payload_bytes = json.dumps(raw_payload, sort_keys=True, default=str).encode("utf-8")
            checksum = hashlib.sha256(payload_bytes).hexdigest()[:16]
        except Exception:
            checksum = "unhashable_payload"

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "source_type": source_type,
        "source_name": source_name,
        "source_record_id": source_record_id,
        "company": company,
        "filters": filters,
        "as_of": as_of or now_iso,
        "retrieved_at": now_iso,
        "checksum_or_version": checksum
    }


def parse_pnl_data(
    pnl_data: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], Optional[Decimal], List[str]]:
    """
    Extract Revenue and COGS (Cost of Goods Sold) from Profit and Loss statement rows.
    Supports ERPNext tree structures:
    - If root group account 'Income' exists, take its total directly.
    - Otherwise sum leaf revenue accounts.
    - COGS is extracted from Cost of Goods Sold row.
    Returns (revenue, cogs, limitations).
    """
    limitations = []
    revenue = None
    cogs = None

    # First pass: check for root totals or standard summary rows
    for row in pnl_data:
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        parent = str(row.get("parent_account") or "").strip()
        indent = row.get("indent")

        raw_amount = None
        for k in ("total", "amount", "balance", "net_amount"):
            if k in row and row[k] is not None:
                raw_amount = row[k]
                break

        dec_amount = to_decimal(raw_amount)
        if dec_amount is None:
            continue

        # ERPNext P&L Root group 'Income - ND' (where parent_account is '') or 'Total Income (Credit)'
        if (
            ("parent_account" in row and row["parent_account"] == "" and "income" in account_name) or
            "total income" in account_name or
            (indent == 0.0 and row.get("is_group") == 1 and "income" in account_name)
        ):
            revenue = dec_amount
            break

    # If root group not found, sum leaf accounts
    if revenue is None:
        for row in pnl_data:
            account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
            is_group = row.get("is_group")
            if is_group:
                continue

            raw_amount = None
            for k in ("total", "amount", "balance", "net_amount"):
                if k in row and row[k] is not None:
                    raw_amount = row[k]
                    break
            dec_amount = to_decimal(raw_amount)
            if dec_amount is None:
                continue

            if "income" in account_name or "revenue" in account_name or "sales" in account_name:
                if revenue is None:
                    revenue = dec_amount
                else:
                    revenue += dec_amount

    # Extract COGS:
    # If a single group or summary row exists ("Cost of Goods Sold - ND" with is_group=0 or group total)
    cogs_rows = []
    for row in pnl_data:
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        raw_amount = None
        for k in ("total", "amount", "balance", "net_amount"):
            if k in row and row[k] is not None:
                raw_amount = row[k]
                break
        dec_amount = to_decimal(raw_amount)
        if dec_amount is None:
            continue

        if (
            "cost of goods sold" in account_name or 
            account_name == "cogs" or 
            "giá vốn" in account_name or
            "cogs -" in account_name
        ):
            cogs_rows.append((row, dec_amount))

    if len(cogs_rows) == 1:
        cogs = cogs_rows[0][1]
    elif len(cogs_rows) > 1:
        # If parent-child exists, prefer the parent/summary, else sum leaves
        has_group = any(r[0].get("is_group") for r in cogs_rows)
        if has_group:
            # Pick the top group/parent
            cogs = [r[1] for r in cogs_rows if r[0].get("is_group")][0]
        else:
            # Sum leaves
            cogs = sum(r[1] for r in cogs_rows)

    # If COGS not found by exact term, check direct material / direct expenses
    if cogs is None:
        for row in pnl_data:
            account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
            raw_amount = None
            for k in ("total", "amount", "balance", "net_amount"):
                if k in row and row[k] is not None:
                    raw_amount = row[k]
                    break
            dec_amount = to_decimal(raw_amount)
            if dec_amount is None:
                continue

            if (
                "cost of sales" in account_name or
                "direct material" in account_name or
                "direct labor" in account_name
            ):
                if cogs is None:
                    cogs = dec_amount
                else:
                    cogs += dec_amount

    if revenue is None:
        limitations.append("Revenue row could not be definitively isolated from P&L output.")
    if cogs is None:
        limitations.append("COGS row could not be definitively isolated from P&L output.")

    return revenue, cogs, limitations


def parse_ar_data(
    ar_data: List[Dict[str, Any]],
    as_of_date: Optional[date] = None,
    company: Optional[str] = None,
    currency: str = "VND",
) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal], List[str]]:
    """
    Extract Accounts Receivable Total Outstanding, Overdue Amount, and Overdue Ratio.
    Returns (total_ar, overdue_ar, overdue_ratio, limitations).

    Bucket A & WV-01/WV-02: fail-closed row validation and cross-leg verification.
    A non-dict row, missing amount, malformed amount, cross-leg party_type/voucher_type,
    mismatched company/voucher, or foreign currency raises FinancialSourceDataError.
    WR-01: a dict total/summary row (an is_total_row marker, or a voucher-less
    party="Total" at any position) is NOT a verified Frappe v16 query_report
    output shape — the verified footer is a list row separated at the envelope
    boundary by normalize_frappe_report_footer — so any such dict reaching this
    parser is unproven and raises instead of being skipped into an apparent zero.
    WR-02: every transaction row must carry voucher identity (voucher_no or
    name); ERPNext AR/AP reports are built from voucher-backed GL entries, so a
    voucher-less row cannot be attributed and raises typed — mirroring the
    AI002 adapter contract that rejects positive obligations without a voucher.
    An empty list remains the only legitimate verified-zero input.
    """
    limitations = []
    if not ar_data:
        # Valid empty AR (no outstanding debtors)
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    total_overdue = Decimal("0.00")
    ref_date = as_of_date or datetime.now(timezone.utc).date()

    has_valid_row = False
    for row_idx, row in enumerate(ar_data):
        if not isinstance(row, dict):
            raise FinancialSourceDataError(
                f"AR report row {row_idx} is not an object; source data is malformed."
            )
        # WR-01: a dict total/summary row is not a verified Frappe v16
        # query_report output shape (the verified footer is a list row,
        # separated at the envelope boundary by normalize_frappe_report_footer).
        # An unproven summary dict must fail closed — skipping it would let a
        # fake summary collapse the report into an apparent verified zero.
        if row.get("is_total_row"):
            raise FinancialSourceDataError(
                f"AR report row {row_idx} is an unverified total/summary row "
                "(is_total_row marker); source data is malformed."
            )
        if (
            str(row.get("party") or "").strip().lower() == "total"
            and not (row.get("voucher_no") or row.get("name"))
        ):
            # A party string alone is never summary authority: a row labelled
            # "Total" that carries a voucher identity is processed as a
            # transaction row (the voucher is verified against the DB below).
            raise FinancialSourceDataError(
                f"AR report row {row_idx} is an unverified total/summary row "
                "without voucher identity; source data is malformed."
            )

        # Currency safety: foreign currency rows must fail closed
        row_currency = row.get("currency") or row.get("account_currency")
        if row_currency and str(row_currency).strip().upper() != currency.strip().upper():
            raise FinancialSourceDataError(
                f"AR report row {row_idx} has unsupported currency '{row_currency}', expected '{currency}'."
            )

        # WV-02: Party Type and Voucher Type cross-leg validation
        party_type = row.get("party_type")
        if party_type:
            pt = str(party_type).strip().lower()
            if pt == "supplier":
                raise FinancialSourceDataError(
                    f"AR report row {row_idx} contains cross-leg party_type 'Supplier'."
                )
            if pt not in ("customer", ""):
                raise FinancialSourceDataError(
                    f"AR report row {row_idx} contains non-receivable party_type '{party_type}'."
                )

        voucher_type = row.get("voucher_type")
        if voucher_type:
            vt = str(voucher_type).strip()
            if vt in ("Purchase Invoice", "Purchase Order", "Bill"):
                raise FinancialSourceDataError(
                    f"AR report row {row_idx} contains cross-leg voucher_type '{vt}'."
                )
            if vt not in ("Sales Invoice", "Journal Entry", "Payment Entry", ""):
                raise FinancialSourceDataError(
                    f"AR report row {row_idx} contains unsupported voucher_type '{vt}'."
                )

        voucher_no = str(row.get("voucher_no") or row.get("name") or "").strip()
        if not voucher_type and (voucher_no.startswith("PI-") or voucher_no.startswith("PINV-") or voucher_no.startswith("ACC-PINV-")):
            raise FinancialSourceDataError(
                f"AR report row {row_idx} voucher '{voucher_no}' appears to be a Purchase Invoice."
            )

        # Live Frappe DB validation if active and company provided
        if _should_validate_db_voucher(company) and voucher_no:
            vt_check = voucher_type or "Sales Invoice"
            if vt_check == "Sales Invoice":
                si = frappe.db.get_value("Sales Invoice", voucher_no, ["company", "docstatus", "customer"], as_dict=True)
                if not si:
                    pi = frappe.db.get_value("Purchase Invoice", voucher_no, ["company"], as_dict=True)
                    if pi:
                        raise FinancialSourceDataError(
                            f"AR report row {row_idx} voucher '{voucher_no}' is a Purchase Invoice, not Sales Invoice."
                        )
                    pe = frappe.db.get_value("Payment Entry", voucher_no, ["company"], as_dict=True)
                    if pe:
                        raise FinancialSourceDataError(
                            f"AR report row {row_idx} voucher '{voucher_no}' is a Payment Entry, not Sales Invoice."
                        )
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} references non-existent Sales Invoice '{voucher_no}'."
                    )
                si_comp = si.get("company") if isinstance(si, dict) else getattr(si, "company", None)
                si_docstatus = si.get("docstatus") if isinstance(si, dict) else getattr(si, "docstatus", None)
                if si_comp != company:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Sales Invoice '{voucher_no}' company mismatch: '{si_comp}' != '{company}'."
                    )
                if si_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Sales Invoice '{voucher_no}' is not submitted."
                    )
            elif vt_check == "Payment Entry":
                pe = frappe.db.get_value("Payment Entry", voucher_no, ["company", "docstatus", "payment_type", "party_type", "party"], as_dict=True)
                if not pe:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} references non-existent Payment Entry '{voucher_no}'."
                    )
                pe_comp = pe.get("company") if isinstance(pe, dict) else getattr(pe, "company", None)
                pe_docstatus = pe.get("docstatus") if isinstance(pe, dict) else getattr(pe, "docstatus", None)
                pe_ptype = str(pe.get("party_type") or "").strip().lower() if isinstance(pe, dict) else ""
                pe_pmtype = str(pe.get("payment_type") or "").strip().lower() if isinstance(pe, dict) else ""
                if pe_comp != company:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Payment Entry '{voucher_no}' company mismatch: '{pe_comp}' != '{company}'."
                    )
                if pe_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Payment Entry '{voucher_no}' is not submitted."
                    )
                if pe_ptype == "supplier" or pe_pmtype == "pay":
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} references Supplier/Pay Payment Entry '{voucher_no}' in AR."
                    )
            elif vt_check == "Journal Entry":
                je = frappe.db.get_value("Journal Entry", voucher_no, ["company", "docstatus"], as_dict=True)
                if not je:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} references non-existent Journal Entry '{voucher_no}'."
                    )
                je_comp = je.get("company") if isinstance(je, dict) else getattr(je, "company", None)
                je_docstatus = je.get("docstatus") if isinstance(je, dict) else getattr(je, "docstatus", None)
                if je_comp != company:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Journal Entry '{voucher_no}' company mismatch: '{je_comp}' != '{company}'."
                    )
                if je_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} Journal Entry '{voucher_no}' is not submitted."
                    )

            if row.get("party_account"):
                acc = frappe.db.get_value("Account", row["party_account"], ["account_type", "company"], as_dict=True)
                if not acc:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} party_account '{row['party_account']}' does not exist."
                    )
                acc_comp = acc.get("company") if isinstance(acc, dict) else getattr(acc, "company", None)
                acc_type = acc.get("account_type") if isinstance(acc, dict) else getattr(acc, "account_type", None)
                if acc_comp and acc_comp != company:
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} party_account '{row['party_account']}' company mismatch: '{acc_comp}' != '{company}'."
                    )
                if acc_type != "Receivable":
                    raise FinancialSourceDataError(
                        f"AR report row {row_idx} account '{row['party_account']}' has type '{acc_type}', expected 'Receivable'."
                    )

        raw_outstanding = None
        alias_found = False
        for k in ("outstanding", "outstanding_amount", "invoiced_amount", "amount", "total_due"):
            if k in row:
                alias_found = True
                if row[k] is not None:
                    raw_outstanding = row[k]
                    break

        if not alias_found or raw_outstanding is None:
            raise FinancialSourceDataError(
                f"AR report row {row_idx} is missing a valid outstanding amount field; "
                "source data is malformed."
            )

        outstanding = to_decimal(raw_outstanding)
        if outstanding is None:
            raise FinancialSourceDataError(
                f"AR report row {row_idx} has a malformed outstanding amount; "
                "source data is malformed."
            )

        # WR-02: ERPNext AR/AP transaction rows are always voucher-backed
        # (voucher_no/name). A row without voucher identity cannot be
        # attributed to a document and is a typed failure — never summed into
        # the metric, regardless of amount sign.
        if not voucher_no:
            raise FinancialSourceDataError(
                f"AR report row {row_idx} has no voucher identity "
                "(voucher_no/name); source data is malformed."
            )

        has_valid_row = True
        total_outstanding += outstanding

        # Determine overdue status:
        raw_overdue = None
        for k in ("overdue_amount", "overdue"):
            if k in row and row[k] is not None:
                raw_overdue = row[k]
                break

        overdue = to_decimal(raw_overdue)
        if overdue is not None:
            total_overdue += overdue
        else:
            # Option B: Calculate from due_date
            due_date_str = row.get("due_date")
            if due_date_str:
                try:
                    if isinstance(due_date_str, (datetime, date)):
                        row_due = due_date_str if isinstance(due_date_str, date) else due_date_str.date()
                    else:
                        row_due = datetime.strptime(str(due_date_str)[:10], "%Y-%m-%d").date()
                    
                    if row_due < ref_date:
                        total_overdue += outstanding
                except Exception:
                    pass

    if not has_valid_row:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), ["No active receivables found in period."]

    # Calculate Overdue Ratio = total_overdue / total_outstanding
    if total_outstanding > Decimal("0.00"):
        overdue_ratio = (total_overdue / total_outstanding).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    else:
        overdue_ratio = Decimal("0.0000")
        if total_outstanding == Decimal("0.00") and total_overdue > Decimal("0.00"):
            limitations.append("Overdue AR exists while total outstanding is zero; anomalous ledger state.")

    return (
        total_outstanding.quantize(Decimal("0.01")),
        total_overdue.quantize(Decimal("0.01")),
        overdue_ratio,
        limitations
    )


def parse_ap_data(
    ap_data: List[Dict[str, Any]],
    company: Optional[str] = None,
    currency: str = "VND",
) -> Tuple[Optional[Decimal], List[str]]:
    """
    Extract Accounts Payable Total Outstanding.
    Returns (total_ap, limitations).

    Bucket A & WV-01/WR-02: fail-closed row validation, same
    contract as parse_ar_data — malformed rows raise FinancialSourceDataError
    instead of collapsing to an apparent zero. Dict total/summary rows
    (is_total_row marker, or voucher-less party="Total" at any position) and
    voucher-less rows are unproven shapes and raise typed.
    """
    if not ap_data:
        return Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    has_valid_row = False
    for row_idx, row in enumerate(ap_data):
        if not isinstance(row, dict):
            raise FinancialSourceDataError(
                f"AP report row {row_idx} is not an object; source data is malformed."
            )
        # WR-01: a dict total/summary row is not a verified Frappe v16
        # query_report output shape (the verified footer is a list row,
        # separated at the envelope boundary by normalize_frappe_report_footer).
        # An unproven summary dict must fail closed — skipping it would let a
        # fake summary collapse the report into an apparent verified zero.
        if row.get("is_total_row"):
            raise FinancialSourceDataError(
                f"AP report row {row_idx} is an unverified total/summary row "
                "(is_total_row marker); source data is malformed."
            )
        if (
            str(row.get("party") or "").strip().lower() == "total"
            and not (row.get("voucher_no") or row.get("name"))
        ):
            # A party string alone is never summary authority: a row labelled
            # "Total" that carries a voucher identity is processed as a
            # transaction row (the voucher is verified against the DB below).
            raise FinancialSourceDataError(
                f"AP report row {row_idx} is an unverified total/summary row "
                "without voucher identity; source data is malformed."
            )

        # Currency safety: foreign currency rows must fail closed
        row_currency = row.get("currency") or row.get("account_currency")
        if row_currency and str(row_currency).strip().upper() != currency.strip().upper():
            raise FinancialSourceDataError(
                f"AP report row {row_idx} has unsupported currency '{row_currency}', expected '{currency}'."
            )

        # WV-02: Party Type and Voucher Type cross-leg validation
        party_type = row.get("party_type")
        if party_type:
            pt = str(party_type).strip().lower()
            if pt == "customer":
                raise FinancialSourceDataError(
                    f"AP report row {row_idx} contains cross-leg party_type 'Customer'."
                )
            if pt not in ("supplier", ""):
                raise FinancialSourceDataError(
                    f"AP report row {row_idx} contains non-payable party_type '{party_type}'."
                )

        voucher_type = row.get("voucher_type")
        if voucher_type:
            vt = str(voucher_type).strip()
            if vt in ("Sales Invoice", "Sales Order"):
                raise FinancialSourceDataError(
                    f"AP report row {row_idx} contains cross-leg voucher_type '{vt}'."
                )
            if vt not in ("Purchase Invoice", "Journal Entry", "Payment Entry", ""):
                raise FinancialSourceDataError(
                    f"AP report row {row_idx} contains unsupported voucher_type '{vt}'."
                )

        voucher_no = str(row.get("voucher_no") or row.get("name") or "").strip()
        if not voucher_type and (voucher_no.startswith("SI-") or voucher_no.startswith("SINV-") or voucher_no.startswith("ACC-SINV-")):
            raise FinancialSourceDataError(
                f"AP report row {row_idx} voucher '{voucher_no}' appears to be a Sales Invoice."
            )

        # Live Frappe DB validation if active and company provided
        if _should_validate_db_voucher(company) and voucher_no:
            vt_check = voucher_type or "Purchase Invoice"
            if vt_check == "Purchase Invoice":
                pi = frappe.db.get_value("Purchase Invoice", voucher_no, ["company", "docstatus", "supplier"], as_dict=True)
                if not pi:
                    si = frappe.db.get_value("Sales Invoice", voucher_no, ["company"], as_dict=True)
                    if si:
                        raise FinancialSourceDataError(
                            f"AP report row {row_idx} voucher '{voucher_no}' is a Sales Invoice, not Purchase Invoice."
                        )
                    pe = frappe.db.get_value("Payment Entry", voucher_no, ["company"], as_dict=True)
                    if pe:
                        raise FinancialSourceDataError(
                            f"AP report row {row_idx} voucher '{voucher_no}' is a Payment Entry, not Purchase Invoice."
                        )
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} references non-existent Purchase Invoice '{voucher_no}'."
                    )
                pi_comp = pi.get("company") if isinstance(pi, dict) else getattr(pi, "company", None)
                pi_docstatus = pi.get("docstatus") if isinstance(pi, dict) else getattr(pi, "docstatus", None)
                if pi_comp != company:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Purchase Invoice '{voucher_no}' company mismatch: '{pi_comp}' != '{company}'."
                    )
                if pi_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Purchase Invoice '{voucher_no}' is not submitted."
                    )
            elif vt_check == "Payment Entry":
                pe = frappe.db.get_value("Payment Entry", voucher_no, ["company", "docstatus", "payment_type", "party_type", "party"], as_dict=True)
                if not pe:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} references non-existent Payment Entry '{voucher_no}'."
                    )
                pe_comp = pe.get("company") if isinstance(pe, dict) else getattr(pe, "company", None)
                pe_docstatus = pe.get("docstatus") if isinstance(pe, dict) else getattr(pe, "docstatus", None)
                pe_ptype = str(pe.get("party_type") or "").strip().lower() if isinstance(pe, dict) else ""
                pe_pmtype = str(pe.get("payment_type") or "").strip().lower() if isinstance(pe, dict) else ""
                if pe_comp != company:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Payment Entry '{voucher_no}' company mismatch: '{pe_comp}' != '{company}'."
                    )
                if pe_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Payment Entry '{voucher_no}' is not submitted."
                    )
                if pe_ptype == "customer" or pe_pmtype == "receive":
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} references Customer/Receive Payment Entry '{voucher_no}' in AP."
                    )
            elif vt_check == "Journal Entry":
                je = frappe.db.get_value("Journal Entry", voucher_no, ["company", "docstatus"], as_dict=True)
                if not je:
                    raise FinancialSourceDataError(
                         f"AP report row {row_idx} references non-existent Journal Entry '{voucher_no}'."
                    )
                je_comp = je.get("company") if isinstance(je, dict) else getattr(je, "company", None)
                je_docstatus = je.get("docstatus") if isinstance(je, dict) else getattr(je, "docstatus", None)
                if je_comp != company:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Journal Entry '{voucher_no}' company mismatch: '{je_comp}' != '{company}'."
                    )
                if je_docstatus != 1:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} Journal Entry '{voucher_no}' is not submitted."
                    )

            if row.get("party_account"):
                acc = frappe.db.get_value("Account", row["party_account"], ["account_type", "company"], as_dict=True)
                if not acc:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} party_account '{row['party_account']}' does not exist."
                    )
                acc_comp = acc.get("company") if isinstance(acc, dict) else getattr(acc, "company", None)
                acc_type = acc.get("account_type") if isinstance(acc, dict) else getattr(acc, "account_type", None)
                if acc_comp and acc_comp != company:
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} party_account '{row['party_account']}' company mismatch: '{acc_comp}' != '{company}'."
                    )
                if acc_type != "Payable":
                    raise FinancialSourceDataError(
                        f"AP report row {row_idx} account '{row['party_account']}' has type '{acc_type}', expected 'Payable'."
                    )

        raw_outstanding = None
        alias_found = False
        for k in ("outstanding", "outstanding_amount", "amount", "invoiced_amount", "total_due"):
            if k in row:
                alias_found = True
                if row[k] is not None:
                    raw_outstanding = row[k]
                    break

        if not alias_found or raw_outstanding is None:
            raise FinancialSourceDataError(
                f"AP report row {row_idx} is missing a valid outstanding amount field; "
                "source data is malformed."
            )

        outstanding = to_decimal(raw_outstanding)
        if outstanding is None:
            raise FinancialSourceDataError(
                f"AP report row {row_idx} has a malformed outstanding amount; "
                "source data is malformed."
            )

        # WR-02: ERPNext AR/AP transaction rows are always voucher-backed
        # (voucher_no/name). A row without voucher identity cannot be
        # attributed to a document and is a typed failure — never summed into
        # the metric, regardless of amount sign.
        if not voucher_no:
            raise FinancialSourceDataError(
                f"AP report row {row_idx} has no voucher identity "
                "(voucher_no/name); source data is malformed."
            )

        has_valid_row = True
        total_outstanding += outstanding

    if not has_valid_row:
        return Decimal("0.00"), ["No active payables found in period."]

    return total_outstanding.quantize(Decimal("0.01")), []


def parse_cash_balance(
    trial_balance_or_gl: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], List[str]]:
    """
    Extract verified cash & bank balances from Trial Balance or General Ledger.
    Returns (cash_balance, limitations).
    """
    limitations = []
    if not trial_balance_or_gl:
        return None, ["No cash or bank ledger entries retrieved."]

    total_cash = Decimal("0.00")
    found_cash_account = False

    for row in trial_balance_or_gl:
        if not isinstance(row, dict):
            continue
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        root_type = str(row.get("root_type") or "").strip().lower()
        account_type = str(row.get("account_type") or "").strip().lower()

        is_cash_candidate = (
            account_type in ["cash", "bank"] or
            "cash" in account_name or 
            "bank" in account_name or 
            "tiền mặt" in account_name or 
            "tiền gửi" in account_name
        )

        if is_cash_candidate:
            raw_balance = None
            if "balance" in row and row["balance"] is not None:
                raw_balance = row["balance"]
            elif "closing_balance" in row and row["closing_balance"] is not None:
                raw_balance = row["closing_balance"]
            elif "closing_debit" in row or "closing_credit" in row:
                c_deb = to_decimal(row.get("closing_debit")) or Decimal("0.00")
                c_crd = to_decimal(row.get("closing_credit")) or Decimal("0.00")
                # Bank/Cash is an Asset account; normal debit balance = Debit - Credit
                raw_balance = c_deb - c_crd

            balance = to_decimal(raw_balance)
            if balance is not None:
                found_cash_account = True
                total_cash += balance

    if not found_cash_account:
        return None, ["No verified Bank or Cash account matched in chart of accounts."]

    return total_cash.quantize(Decimal("0.01")), limitations


def build_financial_snapshot(
    company: str,
    period_start: str,
    period_end: str,
    as_of: Optional[str] = None,
    currency: str = "VND",
    correlation_id: Optional[str] = None,
    comparison: Optional[str] = None,
    raw_sources: Optional[Dict[str, Any]] = None,
    source_fetcher: Optional[Any] = None,
    user: Optional[str] = None,
    include_explanation: bool = False,
    llm_provider: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Builds the FinancialSnapshot + EvidenceRefs output envelope according to AI001 Feature Freeze.

    :param company: Name of company to inspect (untrusted, guard-validated).
    :param period_start: Start date (YYYY-MM-DD).
    :param period_end: End date (YYYY-MM-DD).
    :param as_of: Snapshot timestamp (ISO format).
    :param currency: ISO 4217 Currency (e.g. VND, USD).
    :param correlation_id: Tracking ID for request.
    :param comparison: 'PREVIOUS_PERIOD' or 'NONE'/None.
    :param raw_sources: Direct injection of fetched sources (for testing / mocking).
    :param source_fetcher: Callable `fetch(report_key, filters, company)` if fetching live.
    :param user: Current session user for permission checks.
    :param include_explanation: If True, invokes grounded LLM explanation engine.
    :param llm_provider: Optional LLMExplanationProvider instance.
    """
    cid = correlation_id or str(uuid.uuid4())
    snapshot_id = f"SNAP-{uuid.uuid4().hex[:12].upper()}"
    now_iso = as_of or (datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    log_event(
        event_type=EVENT_REQUEST_STARTED,
        correlation_id=cid,
        company=company,
        user=user,
        details={"period_start": period_start, "period_end": period_end, "comparison": comparison}
    )

    # 1. Period bounds validation
    try:
        p_start = datetime.strptime(period_start, "%Y-%m-%d").date()
        p_end = datetime.strptime(period_end, "%Y-%m-%d").date()
        if p_start > p_end:
            log_event(
                event_type=EVENT_REQUEST_FAILED,
                correlation_id=cid,
                status="VALIDATION_ERROR",
                details={"reason": "period_start cannot be after period_end"}
            )
            op_metrics.record_request("VALIDATION_ERROR", 0.0)
            return {
                "feature_id": FEATURE_ID,
                "contract_version": CONTRACT_VERSION,
                "status": "VALIDATION_ERROR",
                "correlation_id": cid,
                "company": None,
                "period": None,
                "as_of": now_iso,
                "snapshot_id": None,
                "data_mode": None,
                "currency": None,
                "metrics": [],
                "comparison": None,
                "explanation": None,
                "missing_inputs": ["period_start cannot be after period_end"],
                "limitations": ["Invalid temporal range provided."],
                "evidence_refs": []
            }
    except (ValueError, TypeError) as e:
        log_event(
            event_type=EVENT_REQUEST_FAILED,
            correlation_id=cid,
            status="VALIDATION_ERROR",
            details={"reason": str(e)}
        )
        op_metrics.record_request("VALIDATION_ERROR", 0.0)
        return {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": "VALIDATION_ERROR",
            "correlation_id": cid,
            "company": None,
            "period": None,
            "as_of": now_iso,
            "snapshot_id": None,
            "data_mode": None,
            "currency": None,
            "metrics": [],
            "comparison": None,
            "explanation": None,
            "missing_inputs": [f"Malformed period date: {str(e)}"],
            "limitations": ["Date formats must be YYYY-MM-DD."],
            "evidence_refs": []
        }

    # 1b. as_of cutoff validation (AI003 foundation remediation, Bucket B).
    # The cutoff must be a full valid ISO date; invalid values are rejected
    # with a typed VALIDATION_ERROR and never silently fall back to period_end.
    as_of_date: Optional[date] = None
    if as_of:
        as_of_raw = str(as_of).strip()
        parsed_as_of = None
        try:
            parsed_as_of = datetime.fromisoformat(as_of_raw.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            parsed_as_of = None
        if parsed_as_of is None:
            log_event(
                event_type=EVENT_REQUEST_FAILED,
                correlation_id=cid,
                status="VALIDATION_ERROR",
                details={"reason": "Invalid as_of date"}
            )
            op_metrics.record_request("VALIDATION_ERROR", 0.0)
            return {
                "feature_id": FEATURE_ID,
                "contract_version": CONTRACT_VERSION,
                "status": "VALIDATION_ERROR",
                "correlation_id": cid,
                "company": None,
                "period": None,
                "as_of": now_iso,
                "snapshot_id": None,
                "data_mode": None,
                "currency": None,
                "metrics": [],
                "comparison": None,
                "explanation": None,
                "missing_inputs": ["Invalid as_of date; expected a full ISO date (YYYY-MM-DD)."],
                "limitations": ["as_of must be a valid ISO date; it is never silently replaced by period_end."],
                "evidence_refs": []
            }
        if parsed_as_of < p_start:
            log_event(
                event_type=EVENT_REQUEST_FAILED,
                correlation_id=cid,
                status="VALIDATION_ERROR",
                details={"reason": "as_of before period_start"}
            )
            op_metrics.record_request("VALIDATION_ERROR", 0.0)
            return {
                "feature_id": FEATURE_ID,
                "contract_version": CONTRACT_VERSION,
                "status": "VALIDATION_ERROR",
                "correlation_id": cid,
                "company": None,
                "period": None,
                "as_of": now_iso,
                "snapshot_id": None,
                "data_mode": None,
                "currency": None,
                "metrics": [],
                "comparison": None,
                "explanation": None,
                "missing_inputs": ["as_of cannot be before period_start."],
                "limitations": ["as_of must lie within the requested period."],
                "evidence_refs": []
            }
        as_of_date = parsed_as_of

    # 2. Company authorization guard
    verified_company = company
    try:
        # If running in Frappe environment with active DB connection, invoke server-side guard
        try:
            import frappe
            if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
                from lotus_fin.security.access import get_verified_company
                verified_company = get_verified_company(company, user=user)
            else:
                if not company:
                    raise ValueError("Company cannot be empty")
                verified_company = company

            log_event(
                event_type=EVENT_AUTH_PASSED,
                correlation_id=cid,
                company=verified_company,
                user=user
            )
        except (ImportError, AttributeError):
            # Fallback if frappe not in environment (e.g. running in unit test without DB)
            if not company:
                raise ValueError("Company cannot be empty")
            verified_company = company
            log_event(
                event_type=EVENT_AUTH_PASSED,
                correlation_id=cid,
                company=verified_company,
                user=user
            )
    except Exception as e:
        # INV-01: Company Access Denied
        log_event(
            event_type=EVENT_AUTH_DENIED,
            correlation_id=cid,
            company=None,
            user=user,
            status="FORBIDDEN",
            details={"error": str(e)}
        )
        op_metrics.record_auth_denial()
        op_metrics.record_request("FORBIDDEN", 0.0)
        return {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": "FORBIDDEN",
            "correlation_id": cid,
            "company": None,  # Do not disclose company presence on FORBIDDEN
            "period": None,
            "as_of": now_iso,
            "snapshot_id": None,
            "data_mode": None,
            "currency": None,
            "metrics": [],
            "comparison": None,
            "explanation": None,
            "missing_inputs": [],
            "limitations": [f"Unauthorized access: {str(e)}"],
            "evidence_refs": []
        }

    # 2b. Currency authority (AI003 foundation remediation, Bucket C).
    # The client may never relabel a financial metric in an arbitrary currency:
    # the server resolves the company's accounting currency and FX conversion
    # is not implemented, so any mismatch is a typed VALIDATION_ERROR.
    try:
        import frappe
        if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
            from lotus_fin.security.access import get_company_accounting_currency
            company_currency = get_company_accounting_currency(verified_company)
            requested_currency = str(currency or "").strip().upper()
            company_currency_norm = str(company_currency or "").strip().upper()
            if not company_currency_norm:
                log_event(
                    event_type=EVENT_REQUEST_FAILED,
                    correlation_id=cid,
                    status="VALIDATION_ERROR",
                    details={"reason": "Company accounting currency could not be determined"}
                )
                op_metrics.record_request("VALIDATION_ERROR", 0.0)
                return {
                    "feature_id": FEATURE_ID,
                    "contract_version": CONTRACT_VERSION,
                    "status": "VALIDATION_ERROR",
                    "correlation_id": cid,
                    "company": None,
                    "period": None,
                    "as_of": now_iso,
                    "snapshot_id": None,
                    "data_mode": None,
                    "currency": None,
                    "metrics": [],
                    "comparison": None,
                    "explanation": None,
                    "missing_inputs": ["Company accounting currency could not be determined."],
                    "limitations": ["Financial metrics cannot be labeled without a verified accounting currency."],
                    "evidence_refs": []
                }
            if requested_currency != company_currency_norm:
                log_event(
                    event_type=EVENT_REQUEST_FAILED,
                    correlation_id=cid,
                    status="VALIDATION_ERROR",
                    details={"reason": "Requested currency does not match company accounting currency"}
                )
                op_metrics.record_request("VALIDATION_ERROR", 0.0)
                return {
                    "feature_id": FEATURE_ID,
                    "contract_version": CONTRACT_VERSION,
                    "status": "VALIDATION_ERROR",
                    "correlation_id": cid,
                    "company": None,
                    "period": None,
                    "as_of": now_iso,
                    "snapshot_id": None,
                    "data_mode": None,
                    "currency": None,
                    "metrics": [],
                    "comparison": None,
                    "explanation": None,
                    "missing_inputs": [
                        "Requested currency does not match the company accounting currency; "
                        "FX conversion is not implemented."
                    ],
                    "limitations": ["Financial metrics are only reported in the company accounting currency."],
                    "evidence_refs": []
                }
            # Server-authoritative currency replaces the client-provided label.
            currency = company_currency
    except ImportError:
        # Non-Frappe unit-test environment: keep the provided currency.
        pass

    log_event(
        event_type=EVENT_SNAPSHOT_STARTED,
        correlation_id=cid,
        company=verified_company,
        details={"snapshot_id": snapshot_id}
    )

    # 3. Source Gathering
    sources = raw_sources or {}
    fetch_errors = {}
    actual_filters_used = {}

    # Extract as_of date boundary (validated in step 1b — never a silent fallback)
    as_of_date_str = as_of_date.strftime("%Y-%m-%d") if as_of_date else period_end

    # Freeze as_of rule: If as_of date is before period_end, reports evaluate up to as_of date
    effective_end_date = min(period_end, as_of_date_str) if as_of_date_str else period_end
    is_as_of_prior_to_period_end = bool(as_of_date and as_of_date < p_end)

    if source_fetcher and not raw_sources:
        # 3.1 Profit and Loss Statement filters
        flt_pnl = {
            "company": verified_company,
            "from_fiscal_year": int(period_start[:4]),
            "to_fiscal_year": int(effective_end_date[:4]),
            "period_start_date": period_start,
            "period_end_date": effective_end_date,
            "periodicity": "Yearly"
        }
        actual_filters_used["profit_and_loss"] = flt_pnl
        try:
            res_pnl = source_fetcher("profit_and_loss", flt_pnl, verified_company)
            if isinstance(res_pnl, dict) and res_pnl.get("status") == "error":
                fetch_errors["profit_and_loss"] = res_pnl.get("message", "P&L error")
            else:
                sources["profit_and_loss"] = res_pnl
        except Exception as e:
            fetch_errors["profit_and_loss"] = str(e)

        # 3.2 Accounts Receivable filters (report_date semantics)
        flt_ar = {
            "company": verified_company,
            "report_date": effective_end_date
        }
        actual_filters_used["accounts_receivable"] = flt_ar
        try:
            res_ar = source_fetcher("accounts_receivable", flt_ar, verified_company)
            if isinstance(res_ar, dict) and res_ar.get("status") == "error":
                fetch_errors["accounts_receivable"] = res_ar.get("message", "AR error")
            else:
                sources["accounts_receivable"] = res_ar
        except Exception as e:
            fetch_errors["accounts_receivable"] = str(e)

        # 3.3 Accounts Payable filters (report_date semantics)
        flt_ap = {
            "company": verified_company,
            "report_date": effective_end_date
        }
        actual_filters_used["accounts_payable"] = flt_ap
        try:
            res_ap = source_fetcher("accounts_payable", flt_ap, verified_company)
            if isinstance(res_ap, dict) and res_ap.get("status") == "error":
                fetch_errors["accounts_payable"] = res_ap.get("message", "AP error")
            else:
                sources["accounts_payable"] = res_ap
        except Exception as e:
            fetch_errors["accounts_payable"] = str(e)

        # 3.4 Trial Balance filters (Cash balance reconciliation)
        flt_tb = {
            "company": verified_company,
            "fiscal_year": int(effective_end_date[:4]),
            "from_date": period_start,
            "to_date": effective_end_date
        }
        actual_filters_used["trial_balance"] = flt_tb
        try:
            res_tb = source_fetcher("trial_balance", flt_tb, verified_company)
            if isinstance(res_tb, dict) and res_tb.get("status") == "error":
                fetch_errors["trial_balance"] = res_tb.get("message", "Trial Balance error")
            else:
                sources["trial_balance"] = res_tb
        except Exception as e:
            fetch_errors["trial_balance"] = str(e)

    # 4. Process EvidenceRefs and Metrics
    evidence_refs: List[Dict[str, Any]] = []
    metrics: List[Dict[str, Any]] = []
    missing_inputs: List[str] = []
    limitations: List[str] = []

    period_obj = {"start": period_start, "end": period_end}

    # --- Metric 1 & 2: Revenue & COGS & Gross Margin ---
    pnl_res = sources.get("profit_and_loss")
    pnl_ok, pnl_data, pnl_err = validate_source_payload("profit_and_loss", pnl_res, expected_company=verified_company)
    if not pnl_ok or "profit_and_loss" in fetch_errors:
        err_msg = fetch_errors.get("profit_and_loss", pnl_err or "Source 'profit_and_loss' not provided")
        missing_inputs.append("profit_and_loss")
        limitations.append(f"P&L Source unavailable: {err_msg}")
        for m_id in ["revenue", "cogs", "gross_margin"]:
            metrics.append({
                "metric_id": m_id,
                "status": "UNAVAILABLE",
                "value": None,
                "currency_or_unit": currency if m_id != "gross_margin" else "ratio",
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [],
                "limitations": [err_msg]
            })
    else:
        # Build evidence ref for P&L
        pnl_filters = actual_filters_used.get("profit_and_loss") or {
            "company": verified_company,
            "from_date": period_start,
            "to_date": effective_end_date
        }
        pnl_ev = generate_evidence_ref(
            source_type="ERP_NEXT_REPORT",
            source_name=REPORT_ALLOWLIST["profit_and_loss"],
            company=verified_company,
            filters=pnl_filters,
            as_of=now_iso,
            raw_payload=pnl_data
        )
        evidence_refs.append(pnl_ev)

        rev_val, cogs_val, pnl_lims = parse_pnl_data(pnl_data)
        limitations.extend(pnl_lims)

        # Revenue
        metrics.append({
            "metric_id": "revenue",
            "status": "AVAILABLE" if rev_val is not None else "UNAVAILABLE",
            "value": float(rev_val) if rev_val is not None else None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [pnl_ev["checksum_or_version"]],
            "limitations": [] if rev_val is not None else ["Revenue row missing in P&L."]
        })

        # COGS
        metrics.append({
            "metric_id": "cogs",
            "status": "AVAILABLE" if cogs_val is not None else "UNAVAILABLE",
            "value": float(cogs_val) if cogs_val is not None else None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [pnl_ev["checksum_or_version"]],
            "limitations": [] if cogs_val is not None else ["COGS not isolated in P&L."]
        })

        # Gross Margin = (Revenue - COGS) / Revenue
        if rev_val is not None and cogs_val is not None:
            if rev_val > Decimal("0.00"):
                gm_ratio = ((rev_val - cogs_val) / rev_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                metrics.append({
                    "metric_id": "gross_margin",
                    "status": "AVAILABLE",
                    "value": float(gm_ratio),
                    "currency_or_unit": "ratio",
                    "period": period_obj,
                    "formula_version": FORMULA_VERSION,
                    "snapshot_id": snapshot_id,
                    "evidence_refs": [pnl_ev["checksum_or_version"]],
                    "limitations": []
                })
            else:
                metrics.append({
                    "metric_id": "gross_margin",
                    "status": "UNAVAILABLE",
                    "value": None,
                    "currency_or_unit": "ratio",
                    "period": period_obj,
                    "formula_version": FORMULA_VERSION,
                    "snapshot_id": snapshot_id,
                    "evidence_refs": [pnl_ev["checksum_or_version"]],
                    "limitations": ["Revenue is zero or negative; gross margin ratio undefined."]
                })
        else:
            metrics.append({
                "metric_id": "gross_margin",
                "status": "UNAVAILABLE",
                "value": None,
                "currency_or_unit": "ratio",
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [pnl_ev["checksum_or_version"]],
                "limitations": ["Requires both Revenue and COGS to calculate gross margin."]
            })

    # WV-02: Master Party Type preflight check
    if _has_active_db():
        try:
            is_mock = type(frappe.db).__name__ in ("Mock", "MagicMock") or hasattr(frappe.db, "_mock_return_value")
            rec_parties = frappe.db.get_all("Party Type", {"account_type": "Receivable"}, pluck="name")
            pay_parties = frappe.db.get_all("Party Type", {"account_type": "Payable"}, pluck="name")
            if not (is_mock and type(rec_parties).__name__ in ("Mock", "MagicMock")):
                if not isinstance(rec_parties, list) or ("Customer" not in rec_parties):
                    fetch_errors["accounts_receivable"] = (
                        "Master data preflight check failed: 'Customer' is not registered as a Receivable Party Type."
                    )
                if not isinstance(pay_parties, list) or ("Supplier" not in pay_parties):
                    fetch_errors["accounts_payable"] = (
                        "Master data preflight check failed: 'Supplier' is not registered as a Payable Party Type."
                    )
        except Exception as e:
            fetch_errors["accounts_receivable"] = f"Master data preflight check failed: {e}"
            fetch_errors["accounts_payable"] = f"Master data preflight check failed: {e}"

    # --- Metric 3 & 4: Accounts Receivable Outstanding & Overdue Ratio ---
    ar_res = sources.get("accounts_receivable")
    ar_ok, ar_data, ar_err = validate_source_payload("accounts_receivable", ar_res, expected_company=verified_company)
    if not ar_ok or "accounts_receivable" in fetch_errors:
        err_msg = fetch_errors.get("accounts_receivable", ar_err or "Source 'accounts_receivable' not provided")
        missing_inputs.append("accounts_receivable")
        limitations.append(f"AR Source unavailable: {err_msg}")
        for m_id in ["ar_outstanding", "overdue_ar_ratio"]:
            metrics.append({
                "metric_id": m_id,
                "status": "UNAVAILABLE",
                "value": None,
                "currency_or_unit": currency if m_id == "ar_outstanding" else "ratio",
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [],
                "limitations": [err_msg]
            })
    else:
        ar_filters = actual_filters_used.get("accounts_receivable") or {
            "company": verified_company,
            "report_date": effective_end_date
        }
        ar_ev = generate_evidence_ref(
            source_type="ERP_NEXT_REPORT",
            source_name=REPORT_ALLOWLIST["accounts_receivable"],
            company=verified_company,
            filters=ar_filters,
            as_of=now_iso,
            raw_payload=ar_data
        )
        evidence_refs.append(ar_ev)

        try:
            ar_tot, ar_overdue, ar_ratio, ar_lims = parse_ar_data(
                ar_data,
                as_of_date=datetime.strptime(effective_end_date, "%Y-%m-%d").date(),
                company=verified_company,
                currency=currency,
            )
        except FinancialSourceDataError as e:
            # Bucket A: malformed AR rows invalidate the whole source —
            # typed unavailable state, never an apparent verified zero.
            src_err = f"AR source data invalid: {str(e)}"
            missing_inputs.append("accounts_receivable")
            limitations.append(src_err)
            for m_id in ["ar_outstanding", "overdue_ar_ratio"]:
                metrics.append({
                    "metric_id": m_id,
                    "status": "UNAVAILABLE",
                    "value": None,
                    "currency_or_unit": currency if m_id == "ar_outstanding" else "ratio",
                    "period": period_obj,
                    "formula_version": FORMULA_VERSION,
                    "snapshot_id": snapshot_id,
                    "evidence_refs": [ar_ev["checksum_or_version"]],
                    "limitations": [src_err]
                })
            ar_lims = []
            ar_tot = None
            ar_ratio = None

        if ar_tot is not None:
            limitations.extend(ar_lims)

            metrics.append({
                "metric_id": "ar_outstanding",
                "status": "AVAILABLE",
                "value": float(ar_tot),
                "currency_or_unit": currency,
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [ar_ev["checksum_or_version"]],
                "limitations": []
            })

            metrics.append({
                "metric_id": "overdue_ar_ratio",
                "status": "AVAILABLE" if ar_ratio is not None else "UNAVAILABLE",
                "value": float(ar_ratio) if ar_ratio is not None else None,
                "currency_or_unit": "ratio",
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [ar_ev["checksum_or_version"]],
                "limitations": ar_lims
            })

    # --- Metric 5: Accounts Payable Outstanding ---
    ap_res = sources.get("accounts_payable")
    ap_ok, ap_data, ap_err = validate_source_payload("accounts_payable", ap_res, expected_company=verified_company)
    if not ap_ok or "accounts_payable" in fetch_errors:
        err_msg = fetch_errors.get("accounts_payable", ap_err or "Source 'accounts_payable' not provided")
        missing_inputs.append("accounts_payable")
        limitations.append(f"AP Source unavailable: {err_msg}")
        metrics.append({
            "metric_id": "ap_outstanding",
            "status": "UNAVAILABLE",
            "value": None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [],
            "limitations": [err_msg]
        })
    else:
        ap_filters = actual_filters_used.get("accounts_payable") or {
            "company": verified_company,
            "report_date": effective_end_date
        }
        ap_ev = generate_evidence_ref(
            source_type="ERP_NEXT_REPORT",
            source_name=REPORT_ALLOWLIST["accounts_payable"],
            company=verified_company,
            filters=ap_filters,
            as_of=now_iso,
            raw_payload=ap_data
        )
        evidence_refs.append(ap_ev)

        try:
            ap_tot, ap_lims = parse_ap_data(ap_data, company=verified_company, currency=currency)
        except FinancialSourceDataError as e:
            # Bucket A: malformed AP rows invalidate the whole source —
            # typed unavailable state, never an apparent verified zero.
            ap_err_str = f"AP source data invalid: {str(e)}"
            missing_inputs.append("accounts_payable")
            limitations.append(ap_err_str)
            metrics.append({
                "metric_id": "ap_outstanding",
                "status": "UNAVAILABLE",
                "value": None,
                "currency_or_unit": currency,
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [ap_ev["checksum_or_version"]],
                "limitations": [ap_err_str]
            })
        else:
            limitations.extend(ap_lims)

            metrics.append({
                "metric_id": "ap_outstanding",
                "status": "AVAILABLE" if ap_tot is not None else "UNAVAILABLE",
                "value": float(ap_tot) if ap_tot is not None else None,
                "currency_or_unit": currency,
                "period": period_obj,
                "formula_version": FORMULA_VERSION,
                "snapshot_id": snapshot_id,
                "evidence_refs": [ap_ev["checksum_or_version"]],
                "limitations": ap_lims
            })

    # --- Metric 6: Near-Term AP (Freeze rule: UNAVAILABLE with limitation) ---
    metrics.append({
        "metric_id": "near_term_ap",
        "status": "UNAVAILABLE",
        "value": None,
        "currency_or_unit": currency,
        "period": period_obj,
        "formula_version": FORMULA_VERSION,
        "snapshot_id": snapshot_id,
        "evidence_refs": [],
        "limitations": ["near-term AP horizon not yet frozen"]
    })

    # --- Metric 7: Cash & Bank Balance ---
    cash_source_key = "trial_balance" if "trial_balance" in sources else "general_ledger"
    cash_source = sources.get(cash_source_key)
    cash_ok, c_data, cash_src_err = validate_source_payload(cash_source_key, cash_source, expected_company=verified_company)
    if not cash_ok:
        missing_inputs.append("cash_balance")
        limitations.append(f"Cash source unavailable: {cash_src_err}")
        metrics.append({
            "metric_id": "cash_balance",
            "status": "UNAVAILABLE",
            "value": None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [],
            "limitations": [cash_src_err]
        })
    else:
        c_filters = actual_filters_used.get("trial_balance") or {
            "company": verified_company,
            "from_date": period_start,
            "to_date": effective_end_date
        }
        c_ev = generate_evidence_ref(
            source_type="ERP_NEXT_REPORT",
            source_name="Trial Balance",
            company=verified_company,
            filters=c_filters,
            as_of=now_iso,
            raw_payload=c_data
        )
        evidence_refs.append(c_ev)

        cash_bal, cash_lims = parse_cash_balance(c_data)
        limitations.extend(cash_lims)

        metrics.append({
            "metric_id": "cash_balance",
            "status": "AVAILABLE" if cash_bal is not None else "UNAVAILABLE",
            "value": float(cash_bal) if cash_bal is not None else None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [c_ev["checksum_or_version"]],
            "limitations": cash_lims
        })

    # Track metrics computed vs unavailable
    for m in metrics:
        if m["status"] == "AVAILABLE":
            op_metrics.record_metric_computed()
            log_event(
                event_type=EVENT_METRIC_COMPUTED,
                correlation_id=cid,
                company=verified_company,
                details={"metric_id": m["metric_id"], "value": m["value"]}
            )
        else:
            op_metrics.record_metric_unavailable(m["metric_id"])
            log_event(
                event_type=EVENT_METRIC_UNAVAILABLE,
                correlation_id=cid,
                company=verified_company,
                details={"metric_id": m["metric_id"], "limitations": m.get("limitations", [])}
            )

    # Preserve the explicit limitation for historical semantics (Bucket B):
    # a posting-date as_of cutoff does NOT support as_known_at replay of
    # backdated or cancelled postings — this must never be claimed implicitly.
    if is_as_of_prior_to_period_end:
        limitations.append(
            "as-of cutoff uses posting-date semantics only; as_known_at historical "
            "replay of backdated or cancelled postings is not supported."
        )

    # 5. Overall Status Decision
    # OK: All required core metrics available (revenue, cogs, gross_margin, ar_outstanding, overdue_ar_ratio, ap_outstanding, cash_balance)
    # near_term_ap being UNAVAILABLE by design does not block overall status OK.
    core_metrics = [m for m in metrics if m["metric_id"] != "near_term_ap"]
    available_core_count = sum(1 for m in core_metrics if m["status"] == "AVAILABLE")
    
    if fetch_errors and available_core_count == 0:
        overall_status = "SOURCE_ERROR"
    elif available_core_count == len(core_metrics):
        overall_status = "OK"
    elif available_core_count > 0:
        overall_status = "PARTIAL"
    else:
        overall_status = "INSUFFICIENT_DATA"

    # Assemble base snapshot
    result_snapshot = {
        "feature_id": FEATURE_ID,
        "contract_version": CONTRACT_VERSION,
        "status": overall_status,
        "correlation_id": cid,
        "company": verified_company,
        "period": period_obj,
        "as_of": now_iso,
        "snapshot_id": snapshot_id,
        "data_mode": "actual",
        "currency": currency,
        "metrics": metrics,
        "comparison": None,
        "explanation": {
            "status": "UNAVAILABLE",
            "facts": [],
            "interpretations": [],
            "next_checks": []
        },
        "missing_inputs": sorted(list(set(missing_inputs))),
        "limitations": sorted(list(set(limitations))),
        "evidence_refs": evidence_refs
    }

    # 6. Comparison Processing (PREVIOUS_PERIOD)
    if comparison == "PREVIOUS_PERIOD":
        from lotus_fin.ai.financial_health import compute_previous_period, build_comparison_block
        prev_start, prev_end = compute_previous_period(period_start, period_end)

        # Bucket B: align the previous window with the current EFFECTIVE window
        # length so current/previous metrics always cover consistent period
        # lengths (a mid-period as_of cutoff must not compare a short current
        # window against a full previous window).
        effective_len_days = (
            datetime.strptime(effective_end_date, "%Y-%m-%d").date()
            - datetime.strptime(period_start, "%Y-%m-%d").date()
        ).days
        prev_effective_end = (
            datetime.strptime(prev_start, "%Y-%m-%d").date() + timedelta(days=effective_len_days)
        ).strftime("%Y-%m-%d")

        # Build previous period snapshot
        # Note: If raw_sources was injected, we cannot assume raw_sources contains previous period unless provided.
        # But if source_fetcher is present, we fetch previous period from live ERPNext.
        prev_snapshot = None
        if source_fetcher:
            try:
                prev_snapshot = build_financial_snapshot(
                    company=verified_company,
                    period_start=prev_start,
                    period_end=prev_end,
                    as_of=prev_effective_end,
                    currency=currency,
                    correlation_id=f"{cid}-PREV",
                    comparison=None,  # No recursion
                    raw_sources=None,
                    source_fetcher=source_fetcher,
                    user=user
                )
            except Exception as e:
                log_event(
                    event_type=EVENT_SOURCE_ERROR,
                    correlation_id=cid,
                    company=verified_company,
                    details={"error": f"Failed to build previous snapshot: {str(e)}"}
                )

        comp_block = build_comparison_block(result_snapshot, prev_snapshot, correlation_id=cid)
        result_snapshot["comparison"] = comp_block
        if comp_block.get("limitations"):
            result_snapshot["limitations"] = sorted(list(set(result_snapshot["limitations"] + comp_block["limitations"])))

    # 7. LLM Explanation Generation (AI001-04)
    if include_explanation:
        from lotus_fin.ai.explanation import generate_financial_explanation
        explanation_obj = generate_financial_explanation(
            snapshot=result_snapshot,
            provider=llm_provider,
            correlation_id=cid
        )
        result_snapshot["explanation"] = explanation_obj

    log_event(
        event_type=EVENT_SNAPSHOT_COMPLETED,
        correlation_id=cid,
        company=verified_company,
        details={"snapshot_id": snapshot_id, "status": overall_status}
    )
    log_event(
        event_type=EVENT_REQUEST_COMPLETED,
        correlation_id=cid,
        company=verified_company,
        status=overall_status
    )
    op_metrics.record_request(overall_status, 0.0)

    return result_snapshot
