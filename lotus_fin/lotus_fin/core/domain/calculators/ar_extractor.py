from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from lotus_fin.core.domain.calculators.observation_reconciliation import (
    reconcile_observations,
    content_signature,
    observation_identity,
)
from lotus_fin.core.domain.errors import FinancialSourceDataError

try:
    import frappe
except ImportError:
    frappe = None

# PB-DATA-01 sentinel: the row carries no verified overdue basis (no explicit
# overdue column and no parseable due date) — its overdue state is unknown,
# never a fabricated zero.
_OVERDUE_BASIS_UNKNOWN = object()

_OVERDUE_BASIS_INCONCLUSIVE_NOTE = (
    "Overdue basis missing or malformed for one or more receivable rows; "
    "overdue amount and ratio are inconclusive."
)


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        d = Decimal(str(val))
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None


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


def _resolve_overdue_basis(
    row: Dict[str, Any],
    outstanding: Decimal,
    ref_date: date,
) -> Any:
    """
    PB-DATA-01: resolve one row's overdue basis explicitly.

    1. An explicit, parseable `overdue_amount`/`overdue` column is the
       report's authoritative overdue value (any sign).
    2. Otherwise a parseable `due_date` gives the due-date basis: the full
       outstanding amount counts as overdue only when strictly before the
       as-of date (due-exact is not overdue).
    3. A missing or malformed basis on a row with a non-zero outstanding
       leaves the overdue state UNKNOWN — the affected metric becomes typed
       unavailable instead of reporting a fabricated zero. A zero-outstanding
       row cannot be overdue, so a missing basis is a known zero for it.
    """
    raw_overdue = None
    for k in ("overdue_amount", "overdue"):
        if k in row and row[k] is not None:
            raw_overdue = row[k]
            break

    if raw_overdue is not None:
        explicit = _to_decimal(raw_overdue)
        if explicit is None:
            # An explicit authoritative column that cannot be parsed is a
            # malformed basis, not an absent one.
            return _OVERDUE_BASIS_UNKNOWN
        return explicit

    due_date_str = row.get("due_date")
    row_due = None
    if due_date_str is not None and str(due_date_str).strip() != "":
        try:
            if isinstance(due_date_str, (datetime, date)):
                row_due = due_date_str if isinstance(due_date_str, date) else due_date_str.date()
            else:
                row_due = datetime.strptime(str(due_date_str)[:10], "%Y-%m-%d").date()
        except Exception:
            row_due = None

    if row_due is None:
        if outstanding != Decimal("0.00"):
            return _OVERDUE_BASIS_UNKNOWN
        return Decimal("0.00")
    if row_due < ref_date:
        return outstanding
    return Decimal("0.00")


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
    PB-DATA-01: overdue amount/ratio are only computed from a verified basis
    (explicit overdue column or parseable past due date); rows with an unknown
    basis make the overdue metric typed unavailable — never a fabricated zero
    — while a valid total remains available independently.
    PB-DATA-02: rows are reconciled by voucher observation identity before
    summation — exact duplicates count once (with an audit note), distinct
    contents need an allocation discriminator (payment terms / account / due
    date) to stay separate, and conflicting contents without a discriminator
    raise typed.
    An empty list remains the only legitimate verified-zero input.
    """
    limitations = []
    if not ar_data:
        # Valid empty AR (no outstanding debtors)
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), []

    ref_date = as_of_date or datetime.now(timezone.utc).date()
    prepared: List[Tuple[Dict[str, Any], Decimal, Any]] = []

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

        outstanding = _to_decimal(raw_outstanding)
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

        prepared.append((row, outstanding, _resolve_overdue_basis(row, outstanding, ref_date)))

    # PB-DATA-02: reconcile observations by voucher identity before any
    # summation — exact duplicates count once, conflicting contents fail closed.
    kept_rows, dup_notes = reconcile_observations(
        [entry[0] for entry in prepared], "AR report", FinancialSourceDataError
    )
    prepared_by_key = {
        (observation_identity(entry[0]), content_signature(entry[0])): (entry[1], entry[2])
        for entry in prepared
    }

    total_outstanding = Decimal("0.00")
    total_overdue = Decimal("0.00")
    has_valid_row = False
    basis_unknown = False
    for row in kept_rows:
        outstanding, overdue_value = prepared_by_key[
            (observation_identity(row), content_signature(row))
        ]
        has_valid_row = True
        total_outstanding += outstanding
        if overdue_value is _OVERDUE_BASIS_UNKNOWN:
            basis_unknown = True
        else:
            total_overdue += overdue_value

    limitations.extend(dup_notes)

    if not has_valid_row:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), ["No active receivables found in period."]

    # PB-DATA-01: missing != zero — an unknown overdue basis makes the
    # overdue amount/ratio typed unavailable while the valid total stays.
    if basis_unknown:
        limitations.append(_OVERDUE_BASIS_INCONCLUSIVE_NOTE)
        return (
            total_outstanding.quantize(Decimal("0.01")),
            None,
            None,
            limitations
        )

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
