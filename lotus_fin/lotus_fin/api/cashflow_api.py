"""
Lotus Fin API - Cash-flow Forecast Copilot (AI-F002) Whitelisted Endpoints.
"""

from datetime import date, datetime, timedelta
import json
import os
from typing import Any, Dict, List, Optional, Union
import frappe
from frappe import _

from lotus_fin.modules.f002_cashflow.adapters import (
    resolve_cash_account_scope,
    ObligationPermissionError,
    ObligationSourceError,
)
from lotus_fin.modules.f002_cashflow.models import (
    ForecastRequest,
    CoverageScope,
    ForecastStatus,
    ReasonCode,
)
from lotus_fin.modules.f002_cashflow.service import (
    get_cash_forecast,
    response_to_dict,
    build_fail_closed_response,
    resolve_request_scope,
)
from lotus_fin.modules.f002_cashflow.source_interface import SyntheticFixtureSource, FailClosedSource
from lotus_fin.security.access import (
    get_verified_company,
    verify_evidence_access,
)


def _typed_fail_closed(
    req: ForecastRequest,
    status: ForecastStatus,
    reason_code: ReasonCode,
    limitation: str,
) -> Dict[str, Any]:
    return response_to_dict(
        build_fail_closed_response(
            request=req,
            status=status,
            reason_code=reason_code,
            limitation=limitation,
            correlation_id=req.correlation_id,
            include_company=False,
        )
    )


@frappe.whitelist()
def get_ai002_cash_account_scope(company: Optional[str] = None) -> Dict[str, Any]:
    """Exposes server-side resolved Cash and Bank account scope for the company."""
    verified_comp = get_verified_company(company)
    try:
        res = resolve_cash_account_scope(verified_comp)
    except ObligationPermissionError:
        frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
    except ObligationSourceError:
        frappe.throw(_("Cash account scope could not be resolved."))
    return {
        "status": res["status"],
        "approval": res["approval"],
        "company": verified_comp,
        "scope": res["scope"],
        "unapproved_excluded": res["unapproved_excluded"],
        "total_cash_bank_accounts": res["total_cash_bank_accounts"],
        "count": res["count"],
    }


@frappe.whitelist(allow_guest=True)
def get_ai002_cash_forecast(
    company: Optional[str] = None,
    financial_as_of: Optional[str] = None,
    forecast_start: Optional[str] = None,
    forecast_end: Optional[str] = None,
    currency: Optional[str] = None,
    correlation_id: Optional[str] = None,
    include_explanation: Union[bool, int, str] = False,
    cash_account_scope: Optional[Union[List[str], str]] = None,
) -> Dict[str, Any]:
    """Deterministic 30-day EOD cash forecast with fail-closed reconciliation."""
    from lotus_fin.security.access import get_company_accounting_currency
    target_currency = currency or get_company_accounting_currency(company) or "USD"
    try:
        as_of_date = datetime.strptime(financial_as_of, "%Y-%m-%d").date() if financial_as_of else (date.today() - timedelta(days=1))
        start_date = datetime.strptime(forecast_start, "%Y-%m-%d").date() if forecast_start else (as_of_date + timedelta(days=1))
        end_date = datetime.strptime(forecast_end, "%Y-%m-%d").date() if forecast_end else (start_date + timedelta(days=29))
    except ValueError:
        dummy_req = ForecastRequest(
            company=company or "",
            financial_as_of=None,
            forecast_start=None,
            forecast_end=None,
            reporting_currency=target_currency,
            correlation_id=correlation_id or "",
        )
        return _typed_fail_closed(
            dummy_req,
            ForecastStatus.VALIDATION_ERROR,
            ReasonCode.HORIZON_MISMATCH,
            "Invalid date format; expected YYYY-MM-DD.",
        )

    want_explanation = False
    if isinstance(include_explanation, bool):
        want_explanation = include_explanation
    elif isinstance(include_explanation, (int, float)):
        want_explanation = bool(include_explanation)
    elif isinstance(include_explanation, str):
        want_explanation = include_explanation.strip().lower() in ["1", "true", "yes"]

    scope_list: List[str] = []
    if isinstance(cash_account_scope, list):
        scope_list = [str(a).strip() for a in cash_account_scope if str(a).strip()]
    elif isinstance(cash_account_scope, str) and cash_account_scope.strip():
        try:
            parsed = json.loads(cash_account_scope)
            scope_list = [str(a).strip() for a in parsed if str(a).strip()] if isinstance(parsed, list) else [cash_account_scope.strip()]
        except Exception:
            scope_list = [cash_account_scope.strip()]

    req = ForecastRequest(
        company=company or "",
        financial_as_of=as_of_date,
        forecast_start=start_date,
        forecast_end=end_date,
        reporting_currency=target_currency,
        cash_account_scope=scope_list,
        coverage_scope=CoverageScope.TRADE_ONLY,
        include_explanation=want_explanation,
        correlation_id=correlation_id or "",
    )

    if not scope_list and company and str(company).strip():
        try:
            scope_res = resolve_request_scope(str(company).strip())
        except ObligationPermissionError:
            return _typed_fail_closed(req, ForecastStatus.FORBIDDEN, ReasonCode.UNAUTHORIZED_ACCESS, "Access Denied")
        except Exception:
            return _typed_fail_closed(req, ForecastStatus.SOURCE_ERROR, ReasonCode.DATA_PIPELINE_ERROR, "Cash account scope could not be resolved.")
        if scope_res.get("status") == "RESOLVED" and scope_res.get("scope"):
            req.cash_account_scope = list(scope_res["scope"])

    future_source = FailClosedSource()
    if getattr(frappe.flags, "in_test", False) or getattr(frappe.flags, "ai002_use_fixture_source", False):
        candidate_paths = [
            frappe.get_app_path("lotus_fin", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json"),
            os.path.abspath(os.path.join(frappe.get_app_path("lotus_fin"), "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
            "/home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json",
        ]
        fixture_path = next((cp for cp in candidate_paths if os.path.exists(cp)), None)
        if fixture_path:
            future_source = SyntheticFixtureSource(fixture_path)

    try:
        response = get_cash_forecast(request=req, user=frappe.session.user, future_event_source=future_source)
    except Exception:
        frappe.log_error("AI002 cash forecast unexpected failure")
        return _typed_fail_closed(req, ForecastStatus.SOURCE_ERROR, ReasonCode.DATA_PIPELINE_ERROR, "Cash forecast could not be computed from underlying sources.")

    return response_to_dict(response)


@frappe.whitelist()
def get_ai002_evidence(evidence_ref: str, company: str) -> Dict[str, Any]:
    """Re-authorizes evidence document access on every drilldown / view action."""
    if not company or not str(company).strip():
        frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

    verified_comp = get_verified_company(company)
    verify_evidence_access(evidence_ref=evidence_ref, user=frappe.session.user, company=verified_comp)

    parts = evidence_ref.split(":", 1)
    doctype, docname = parts[0].strip(), parts[1].strip()
    doc = frappe.get_doc(doctype, docname)
    return {
        "status": "success",
        "evidence_ref": evidence_ref,
        "doctype": doctype,
        "name": docname,
        "company": getattr(doc, "company", None),
        "posting_date": str(getattr(doc, "posting_date", None) or getattr(doc, "transaction_date", None)),
    }

