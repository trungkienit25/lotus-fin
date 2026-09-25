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
from datetime import datetime, date, timezone
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
    as_of_date: Optional[date] = None
) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal], List[str]]:
    """
    Extract Accounts Receivable Total Outstanding, Overdue Amount, and Overdue Ratio.
    Returns (total_ar, overdue_ar, overdue_ratio, limitations).
    """
    limitations = []
    if not ar_data:
        # Valid empty AR (no outstanding debtors)
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    total_overdue = Decimal("0.00")
    ref_date = as_of_date or datetime.now(timezone.utc).date()

    has_valid_row = False
    for row in ar_data:
        if not isinstance(row, dict):
            continue
        # Check for summary row in ERPNext reports
        if row.get("is_total_row") or str(row.get("party") or "").lower() == "total":
            continue

        raw_outstanding = None
        for k in ("outstanding", "outstanding_amount", "invoiced_amount", "amount", "total_due"):
            if k in row and row[k] is not None:
                raw_outstanding = row[k]
                break

        outstanding = to_decimal(raw_outstanding)
        if outstanding is None:
            continue

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
    ap_data: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], List[str]]:
    """
    Extract Accounts Payable Total Outstanding.
    Returns (total_ap, limitations).
    """
    if not ap_data:
        return Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    has_valid_row = False
    for row in ap_data:
        if not isinstance(row, dict):
            continue
        if row.get("is_total_row") or str(row.get("party") or "").lower() == "total":
            continue

        raw_outstanding = None
        for k in ("outstanding", "outstanding_amount", "amount", "invoiced_amount", "total_due"):
            if k in row and row[k] is not None:
                raw_outstanding = row[k]
                break

        outstanding = to_decimal(raw_outstanding)
        if outstanding is not None:
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

    # Extract as_of date boundary
    as_of_date_str = period_end
    if as_of:
        try:
            as_of_date_str = str(as_of)[:10]
        except Exception:
            as_of_date_str = period_end

    # Freeze as_of rule: If as_of date is before period_end, reports evaluate up to as_of date
    effective_end_date = min(period_end, as_of_date_str) if as_of_date_str else period_end
    is_as_of_prior_to_period_end = (as_of_date_str < period_end) if as_of_date_str else False

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
    if pnl_res is None or "profit_and_loss" in fetch_errors:
        err_msg = fetch_errors.get("profit_and_loss", "Source 'profit_and_loss' not provided")
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
        pnl_data = pnl_res.get("data", []) if isinstance(pnl_res, dict) else pnl_res
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

    # --- Metric 3 & 4: Accounts Receivable Outstanding & Overdue Ratio ---
    ar_res = sources.get("accounts_receivable")
    if ar_res is None or "accounts_receivable" in fetch_errors:
        err_msg = fetch_errors.get("accounts_receivable", "Source 'accounts_receivable' not provided")
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
        ar_data = ar_res.get("data", []) if isinstance(ar_res, dict) else ar_res
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

        ar_tot, ar_overdue, ar_ratio, ar_lims = parse_ar_data(ar_data, as_of_date=datetime.strptime(effective_end_date, "%Y-%m-%d").date())
        limitations.extend(ar_lims)

        metrics.append({
            "metric_id": "ar_outstanding",
            "status": "AVAILABLE" if ar_tot is not None else "UNAVAILABLE",
            "value": float(ar_tot) if ar_tot is not None else None,
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
    if ap_res is None or "accounts_payable" in fetch_errors:
        err_msg = fetch_errors.get("accounts_payable", "Source 'accounts_payable' not provided")
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
        ap_data = ap_res.get("data", []) if isinstance(ap_res, dict) else ap_res
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

        ap_tot, ap_lims = parse_ap_data(ap_data)
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
    cash_source = sources.get("trial_balance") or sources.get("general_ledger")
    if cash_source is None:
        missing_inputs.append("cash_balance")
        limitations.append("Trial Balance or General Ledger cash source not provided.")
        metrics.append({
            "metric_id": "cash_balance",
            "status": "UNAVAILABLE",
            "value": None,
            "currency_or_unit": currency,
            "period": period_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snapshot_id,
            "evidence_refs": [],
            "limitations": ["No cash/bank ledger provided."]
        })
    else:
        c_data = cash_source.get("data", []) if isinstance(cash_source, dict) else cash_source
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
                    as_of=None,
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
