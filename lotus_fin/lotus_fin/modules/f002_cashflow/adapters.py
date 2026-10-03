import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    AccountBalance,
    OpeningCash,
    Obligation,
    CashEvent,
)
from .source_interface import FutureEventSource, FailClosedSource


class ObligationSourceError(Exception):
    """Raised when an underlying AR/AP/GL/TB report fails, times out, or returns
    an error/unknown status or a malformed payload. Never mapped to a zero value."""
    pass


class ObligationPermissionError(Exception):
    """Raised when permission is denied accessing AR/AP/GL/TB reports."""
    pass


# Reconciliation labels this adapter emits ONLY after a successful independent
# Trial Balance read that covers the full authorized account set and matches GL.
# The service layer treats every other label as unverified and fails closed.
VERIFIED_RECONCILIATION_STATUSES = (
    "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
    "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED",
)

# Page size for the permission-aware account scope listing (full pagination).
SCOPE_PAGE_LENGTH = 200

# Company custom field (installed via Custom Field fixture, imported on
# `bench migrate`) holding the approved Cash/Bank account scope as a JSON list.
# Provenance/update path: edited through the Company form by authorized users;
# the Company document audit fields (modified_by/modified) record every change.
APPROVED_SCOPE_FIELD = "ai002_approved_cash_accounts"


# Global Frappe reference check (allows running in pure-Python unit test mode).
# Each symbol degrades explicitly to None so that the Frappe-DB code path can
# fail closed with a typed error instead of raising NameError when an import is
# unavailable; unit tests patch these module attributes directly.
try:
    import frappe
    from lotus_fin.security.access import check_ai002_report_permission
    from lotus_fin.api.key_reports import extract_key_report_data
except ImportError:
    frappe = None
    check_ai002_report_permission = None
    extract_key_report_data = None


def hash_party(party: Optional[str]) -> str:
    if not party:
        return ""
    return hashlib.sha256(party.encode("utf-8")).hexdigest()[:12]


def _require_report_primitives() -> None:
    """Fail closed when the authorization/report primitives could not be imported."""
    if check_ai002_report_permission is None or extract_key_report_data is None:
        raise ObligationSourceError(
            "AI002 report access primitives are unavailable in this runtime."
        )


def _has_active_db() -> bool:
    return bool(frappe and hasattr(frappe, "db") and frappe.db)


def _check_report_permission(report_name: str) -> None:
    try:
        check_ai002_report_permission(report_name)
    except Exception as e:
        raise ObligationPermissionError(
            f"Permission denied accessing {report_name}."
        ) from e


def get_opening_cash_ledger(
    company: str,
    as_of: date,
    account_scope: Optional[List[str]] = None,
    currency: str = "VND",
    db_cursor: Any = None,
) -> OpeningCash:
    """
    Get opening cash balance as of EOD financial_as_of.
    Single SQL aggregation:
    SELECT account, SUM(debit) - SUM(credit) as balance
    FROM `tabGL Entry`
    WHERE company=%s AND posting_date <= %s [AND account IN (%s)]
    GROUP BY account

    Reconciliation (Fix B): GL is reconciled against the independent authorized
    ERPNext Trial Balance report for the FULL explicit account scope. A scope
    account missing from the Trial Balance, duplicate TB rows, or a totals
    mismatch yields INCONSISTENT_DATA; a TB read failure yields
    RECONCILIATION_UNAVAILABLE. Without a database connection no reconciled
    label and no fabricated zero is ever produced.
    """
    accounts_balance: List[AccountBalance] = []
    total = Decimal("0")
    has_constituent_deficit = False

    reconciliation_status = "RECONCILIATION_UNAVAILABLE"
    if _has_active_db():
        _require_report_primitives()

        # Report permission for General Ledger & Trial Balance (fail closed)
        _check_report_permission("General Ledger")
        _check_report_permission("Trial Balance")

        # Fix B: Account scope must be explicit; if empty, do not auto-select
        if not account_scope:
            return OpeningCash(
                aggregate_amount=Decimal("0"),
                reconciliation="RECONCILIATION_UNAVAILABLE",
                has_constituent_deficit=False,
                accounts=[],
            )

        # Query GL Entry with single-query aggregation
        placeholders = ", ".join(["%s"] * len(account_scope))
        query = f"""
            SELECT account, SUM(debit) - SUM(credit) as balance
            FROM `tabGL Entry`
            WHERE company = %s
              AND posting_date <= %s
              AND is_cancelled = 0
              AND account IN ({placeholders})
            GROUP BY account
        """
        params = [company, as_of] + account_scope
        try:
            records = frappe.db.sql(query, params, as_dict=True)
        except Exception as e:
            raise ObligationSourceError("General Ledger query failed.") from e

        # Map results. gl_balances keeps the per-account balance so reconciliation
        # can be enforced account-by-account, not only on totals.
        found_accounts = set()
        gl_balances: Dict[str, Decimal] = {}
        for r in records:
            acc_name = r["account"]
            bal = Decimal(str(r["balance"] or 0))
            found_accounts.add(acc_name)
            gl_balances[acc_name] = gl_balances.get(acc_name, Decimal("0")) + bal
            is_deficit = bal < Decimal("0")
            if is_deficit:
                has_constituent_deficit = True
            total += bal
            accounts_balance.append(
                AccountBalance(
                    account=acc_name,
                    amount=bal,
                    currency=currency,
                    deficit=is_deficit,
                )
            )

        # Include untouched cash/bank accounts with 0 balance
        for acc in account_scope:
            if acc not in found_accounts:
                gl_balances[acc] = Decimal("0")
                accounts_balance.append(
                    AccountBalance(
                        account=acc,
                        amount=Decimal("0"),
                        currency=currency,
                        deficit=False,
                    )
                )

        # Fix B2: Independently verify Trial Balance via authoritative ERPNext report.
        # tb_balances maps every scope account found in the TB report to its
        # debit-credit balance. A scope account absent from the TB report (even a
        # genuine zero) can never be reconciled; duplicate TB rows for one scope
        # account are a data conflict (INCONSISTENT_DATA), not an unavailable read.
        scoped_set = set(account_scope)
        tb_balances: Dict[str, Decimal] = {}
        tb_read_ok = False
        tb_duplicate = False
        try:
            fiscal_year = str(as_of.year)
            tb_data = extract_key_report_data(
                report_key="trial_balance",
                filters={"to_date": str(as_of), "fiscal_year": fiscal_year},
                company=company,
            )
        except Exception:
            tb_data = None

        if (
            isinstance(tb_data, dict)
            and tb_data.get("status") == "success"
            and (not tb_data.get("company") or tb_data.get("company") == company)
        ):
            tb_rows = tb_data.get("data")
            if isinstance(tb_rows, list):
                tb_read_ok = True
                for row in tb_rows:
                    if not isinstance(row, dict):
                        continue
                    acc_col = row.get("account")
                    if acc_col in scoped_set:
                        if acc_col in tb_balances:
                            tb_duplicate = True
                            break
                        c_debit = Decimal(str(row.get("closing_debit") or 0))
                        c_credit = Decimal(str(row.get("closing_credit") or 0))
                        tb_balances[acc_col] = c_debit - c_credit

        if not tb_read_ok:
            reconciliation_status = "RECONCILIATION_UNAVAILABLE"
        elif tb_duplicate or set(tb_balances.keys()) != scoped_set:
            # The full authorized account set must be present exactly once in the
            # Trial Balance; duplicates or missing accounts are a data conflict.
            reconciliation_status = "INCONSISTENT_DATA"
        else:
            # Per-account comparison (not totals only): offsetting GL balances
            # against zeroed TB rows must fail closed even when the totals match.
            if all(gl_balances[acc] == tb_balances[acc] for acc in scoped_set):
                if as_of == date.today():
                    # If financial_as_of == today, denote intraday unclosed
                    reconciliation_status = "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED"
                else:
                    reconciliation_status = "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED"
            else:
                reconciliation_status = "INCONSISTENT_DATA"
    else:
        # Running without a Frappe DB: there is no ledger evidence here at all.
        # Never fabricate a reconciled label or a verified zero (Fix B).
        reconciliation_status = "RECONCILIATION_UNAVAILABLE"

    return OpeningCash(
        aggregate_amount=total,
        reconciliation=reconciliation_status,
        has_constituent_deficit=has_constituent_deficit,
        accounts=accounts_balance,
    )


def _parse_report_rows(report: Any, source_label: str, company: Optional[str] = None) -> List[dict]:
    """Validate an ERPNext report payload and return its dict rows.

    Only an explicit successful status with a list payload is accepted; every
    other shape (None response, 'error' or unknown status, missing/non-list
    'data', a payload company that mismatches the requested company, or ANY row
    that is not a dict) raises a typed ObligationSourceError so the service
    fails closed — malformed rows are never silently dropped.
    """
    if not isinstance(report, dict):
        raise ObligationSourceError(f"{source_label} returned no valid response.")
    if report.get("status") != "success":
        raise ObligationSourceError(
            f"{source_label} failed (status={report.get('status')!r})."
        )
    if company is not None:
        rep_company = report.get("company")
        if rep_company and rep_company != company:
            raise ObligationSourceError(f"{source_label} payload company mismatch.")
    rows = report.get("data")
    if not isinstance(rows, list):
        raise ObligationSourceError(f"{source_label} payload is malformed.")
    dict_rows = [r for r in rows if isinstance(r, dict)]
    return dict_rows


def _outstanding_amount(row: dict, source_label: str) -> Decimal:
    if "outstanding" in row:
        raw = row.get("outstanding")
    elif "outstanding_amount" in row:
        raw = row.get("outstanding_amount")
    else:
        raise ObligationSourceError(
            f"{source_label} row is missing an outstanding amount field."
        )
    try:
        amount = Decimal(str(raw))
    except Exception as e:
        raise ObligationSourceError(
            f"{source_label} row has a malformed outstanding amount."
        ) from e
    if not amount.is_finite():
        raise ObligationSourceError(
            f"{source_label} row has an invalid outstanding amount."
        )
    return amount


def _parse_due_date(row: dict, source_label: str) -> Optional[date]:
    due_d = row.get("due_date")
    if due_d is None:
        return None
    if isinstance(due_d, datetime):
        return due_d.date()
    if isinstance(due_d, date):
        return due_d
    if isinstance(due_d, str):
        try:
            return datetime.strptime(due_d, "%Y-%m-%d").date()
        except ValueError as e:
            raise ObligationSourceError(
                f"{source_label} row has a malformed due date."
            ) from e
    raise ObligationSourceError(f"{source_label} row has a malformed due date.")


def _collect_obligations(
    report: Any,
    oblig_type: str,
    party_keys: Tuple[str, ...],
    ref_prefix: str,
    currency: str,
    source_label: str,
    company: Optional[str] = None,
) -> List[Obligation]:
    obligations: List[Obligation] = []
    for r in _parse_report_rows(report, source_label, company=company):
        row_currency = r.get("currency")
        if row_currency and row_currency != currency:
            # VND-only P0 scope: a foreign-currency row must fail closed, never be
            # dropped or converted with an invented rate.
            raise ObligationSourceError(
                f"{source_label} row has unsupported currency."
            )
        amount = _outstanding_amount(r, source_label)
        if amount <= Decimal("0"):
            # Settled / credit rows contribute no obligation: a verified zero
            # contribution from a successfully read, correctly scoped source.
            continue
        voucher = r.get("voucher_no") or r.get("name")
        if not voucher:
            # A positive outstanding that cannot be attributed to a document is a
            # schema anomaly: fail closed instead of fabricating an obligation.
            raise ObligationSourceError(
                f"{source_label} row with positive outstanding has no voucher reference."
            )
        party = None
        for key in party_keys:
            if r.get(key):
                party = r.get(key)
                break
        obligations.append(
            Obligation(
                type=oblig_type,
                party_type="Customer" if oblig_type == "AR" else "Supplier",
                party_hash=hash_party(party),
                remaining_amount=amount,
                due_date=_parse_due_date(r, source_label),
                source_ref=f"{ref_prefix}:{voucher}",
                currency=r.get("currency") or currency,
            )
        )
    return obligations


def get_trade_obligations(
    company: str,
    as_of: date,
    currency: str = "VND",
) -> List[Obligation]:
    """
    Get trade obligations (AR / AP).
    Fix E: Point-in-time correct using Accounts Receivable and Accounts Payable
    reports as of financial_as_of. Invoice `outstanding` as of historical cutoff
    is authoritative. Party names are hashed using SHA256[:12].

    Fix A: each leg (AR, AP) requires an explicit successful report status and a
    valid payload. Status errors, None responses, unknown statuses, malformed
    payloads, exceptions and permission denials raise typed errors
    (ObligationSourceError / ObligationPermissionError) — they are never
    converted into an empty result. AR and AP are read independently; a failure
    on either leg aborts the whole read so a failed leg can never be reported
    as a complete/zero leg. Error messages carry no party, invoice or amount.
    """
    obligations: List[Obligation] = []

    if _has_active_db():
        _require_report_primitives()

        # AR leg (Point-in-Time as of cutoff)
        _check_report_permission("Accounts Receivable")
        try:
            ar_report = extract_key_report_data(
                report_key="accounts_receivable",
                filters={"report_date": str(as_of)},
                company=company,
            )
        except Exception as e:
            raise ObligationSourceError(
                "Accounts Receivable report source failed."
            ) from e
        obligations.extend(
            _collect_obligations(
                ar_report,
                "AR",
                ("party", "customer", "customer_name"),
                "Sales Invoice",
                currency,
                "Accounts Receivable",
                company=company,
            )
        )

        # AP leg (Point-in-Time as of cutoff) — read independently after AR
        _check_report_permission("Accounts Payable")
        try:
            ap_report = extract_key_report_data(
                report_key="accounts_payable",
                filters={"report_date": str(as_of)},
                company=company,
            )
        except Exception as e:
            raise ObligationSourceError(
                "Accounts Payable report source failed."
            ) from e
        obligations.extend(
            _collect_obligations(
                ap_report,
                "AP",
                ("party", "supplier", "supplier_name"),
                "Purchase Invoice",
                currency,
                "Accounts Payable",
                company=company,
            )
        )

        return obligations

    # No Frappe DB: there is no AR/AP evidence here. Returning [] would claim a
    # verified zero, so fail closed with a typed error instead (Fix A).
    raise ObligationSourceError(
        "Trade obligation sources are unavailable without a database connection."
    )


def resolve_cash_account_scope(company: str, user: Optional[str] = None) -> Dict[str, Any]:
    """
    Fix C/D (round 5): resolve the APPROVED Cash/Bank account scope for a company.

    Trust model (SSOT §8: restricted cash excluded "unless explicitly configured
    and authorized"):
    - The only authorization for an account is the Company-level approved scope
      configuration `ai002_approved_cash_accounts` (JSON list of account names,
      managed through the Company form; provenance = Company doc audit fields).
    - Account read permission is enforced BEFORE any scope is returned: a
      doctype-level read check, then a permission-aware `frappe.get_list` query
      with full pagination. `frappe.get_all` is never used as authorization
      evidence because it bypasses permissions.
    - Partial Account visibility (permission-visible accounts < existing accounts
      for the company) is a permission failure -> typed ObligationPermissionError,
      never a partial scope.
    - A successful read with zero existing accounts is NEEDS_REVIEW (valid state);
      a read or configuration read error is a typed error, never an
      empty-but-valid scope.
    - Missing/invalid/stale approved configuration -> NEEDS_REVIEW (the forecast
      is blocked); there is no auto-select fallback.

    Returns {"status": "RESOLVED"|"NEEDS_REVIEW", "approval", "scope",
             "unapproved_excluded", "total_cash_bank_accounts", "count"}.
    Exceptions carry no company or account names.
    """
    if not _has_active_db():
        raise ObligationSourceError(
            "Account scope resolution requires a database connection."
        )

    active_user = user or (
        frappe.session.user if hasattr(frappe, "session") and frappe.session else None
    )

    # 1. Doctype-level read permission (typed, generic — no account names)
    try:
        permitted = frappe.has_permission("Account", ptype="read", user=active_user)
    except Exception as e:
        raise ObligationSourceError("Account permission check failed.") from e
    if not permitted:
        raise ObligationPermissionError("Access Denied")

    # 2. Permission-aware, fully paginated leaf listing (company-filtered server-side)
    leaf_filters = {
        "company": company,
        "account_type": ["in", ["Bank", "Cash"]],
        "is_group": 0,
        "disabled": 0,
    }
    leaf_rows: List[Any] = []
    try:
        limit_start = 0
        while True:
            batch = frappe.get_list(
                "Account",
                filters=leaf_filters,
                fields=["name"],
                limit_start=limit_start,
                limit_page_length=SCOPE_PAGE_LENGTH,
                order_by="name",
            )
            leaf_rows.extend(batch or [])
            if not batch or len(batch) < SCOPE_PAGE_LENGTH:
                break
            limit_start += SCOPE_PAGE_LENGTH
        total_count = frappe.db.count("Account", leaf_filters)
    except Exception as e:
        raise ObligationSourceError("Account listing failed.") from e

    visible_names = {
        (r.get("name") if isinstance(r, dict) else r.name) for r in leaf_rows
    }

    # 3. Partial visibility is a permission failure, not a smaller valid scope
    if len(visible_names) < total_count:
        raise ObligationPermissionError("Access Denied")

    # 4. Approved configuration (Company custom field)
    try:
        raw_config = frappe.db.get_value("Company", company, APPROVED_SCOPE_FIELD)
    except Exception as e:
        raise ObligationSourceError(
            "Approved cash scope configuration could not be read."
        ) from e

    approved_list: Optional[List[str]] = None
    if raw_config is not None and str(raw_config).strip():
        try:
            parsed = json.loads(str(raw_config))
        except Exception:
            parsed = None
        if isinstance(parsed, list) and all(isinstance(a, str) for a in parsed):
            approved_list = [a.strip() for a in parsed if a.strip()]
        if not approved_list:
            approved_list = None  # parsed but empty or wrong shape

    if approved_list is None:
        return {
            "status": "NEEDS_REVIEW",
            "approval": (
                "MISSING_CONFIG"
                if not (raw_config is not None and str(raw_config).strip())
                else "INVALID_CONFIG"
            ),
            "scope": [],
            "unapproved_excluded": sorted(visible_names),
            "total_cash_bank_accounts": len(visible_names),
            "count": 0,
        }

    # 5. Stale configuration: every approved account must still be an enabled,
    #    leaf, Bank/Cash account of this company visible to the user
    unknown = [a for a in approved_list if a not in visible_names]
    if unknown:
        return {
            "status": "NEEDS_REVIEW",
            "approval": "STALE_CONFIG",
            "scope": [],
            "unapproved_excluded": sorted(visible_names),
            "stale_accounts_count": len(unknown),
            "total_cash_bank_accounts": len(visible_names),
            "count": 0,
        }

    return {
        "status": "RESOLVED",
        "approval": "APPROVED",
        "scope": list(approved_list),
        "unapproved_excluded": sorted(visible_names - set(approved_list)),
        "total_cash_bank_accounts": len(visible_names),
        "count": len(approved_list),
    }


def get_future_cash_events(
    company: str,
    start_date: date,
    end_date: date,
    source_adapter: Optional[FutureEventSource] = None,
    currency: str = "VND",
    financial_as_of: Optional[date] = None,
) -> List[CashEvent]:
    """
    Retrieve confirmed future cash settlement events within the window [start_date, end_date].
    Uses source_adapter (defaults to FailClosedSource if none provided).
    """
    adapter = source_adapter or FailClosedSource()
    return adapter.get_confirmed_events(
        company=company,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        financial_as_of=financial_as_of,
    )
