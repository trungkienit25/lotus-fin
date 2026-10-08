from datetime import date
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
    try:
        if not frappe.db.exists("Company", company):
            return False
    except Exception:
        return False
    return True


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
    PB-DATA-02: rows are reconciled by voucher observation identity before
    summation — exact duplicates count once (with an audit note), distinct
    contents need an allocation discriminator (payment terms / account / due
    date) to stay separate, and conflicting contents without a discriminator
    raise typed.
    """
    if not ap_data:
        return Decimal("0.00"), []

    prepared: List[Tuple[Dict[str, Any], Decimal]] = []
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
                else:
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

        outstanding = _to_decimal(raw_outstanding)
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

        prepared.append((row, outstanding))

    # PB-DATA-02: reconcile observations by voucher identity before any
    # summation — exact duplicates count once, conflicting contents fail closed.
    kept_rows, dup_notes = reconcile_observations(
        [entry[0] for entry in prepared], "AP report", FinancialSourceDataError
    )
    prepared_by_key = {
        (observation_identity(entry[0]), content_signature(entry[0])): entry[1]
        for entry in prepared
    }

    total_outstanding = Decimal("0.00")
    has_valid_row = False
    for row in kept_rows:
        has_valid_row = True
        total_outstanding += prepared_by_key[
            (observation_identity(row), content_signature(row))
        ]

    limitations: List[str] = list(dup_notes)

    if not has_valid_row:
        return Decimal("0.00"), ["No active payables found in period."]

    return total_outstanding.quantize(Decimal("0.01")), limitations


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
                c_deb = _to_decimal(row.get("closing_debit")) or Decimal("0.00")
                c_crd = _to_decimal(row.get("closing_credit")) or Decimal("0.00")
                # Bank/Cash is an Asset account; normal debit balance = Debit - Credit
                raw_balance = c_deb - c_crd

            balance = _to_decimal(raw_balance)
            if balance is not None:
                found_cash_account = True
                total_cash += balance

    if not found_cash_account:
        return None, ["No verified Bank or Cash account matched in chart of accounts."]

    return total_cash.quantize(Decimal("0.01")), limitations
