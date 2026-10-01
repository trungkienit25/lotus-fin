"""
Lotus Fin AI005 - Service Facade and Frappe Whitelisted Endpoints.
Delegates business logic to lotus_fin.modules.f005_financing.service.
"""

import json
from typing import Any, Dict, Optional, Union

try:
    import frappe
    from lotus_fin.security.access import get_verified_company
    HAS_FRAPPE = True
except ImportError:
    HAS_FRAPPE = False

from lotus_fin.modules.f005_financing.service import FinancingService

_service_instance = FinancingService()


def frappe_whitelisted(func):
    if HAS_FRAPPE and hasattr(frappe, "whitelist"):
        return frappe.whitelist()(func)
    return func


@frappe_whitelisted
def ask_copilot(company: str, query: str) -> Dict[str, Any]:
    """Whitelisted Copilot NLU endpoint for Natural Language Financing Requests."""
    if HAS_FRAPPE:
        try:
            company = get_verified_company(company)
        except Exception as e:
            frappe.throw(f"Company access error: {str(e)}")

    return _service_instance.ask_financing_copilot(company=company, user_query=query)


@frappe_whitelisted
def match_financing(
    company: str,
    amount: float,
    term_months: int,
    purpose: str = "WORKING_CAPITAL",
    custom_profile: Optional[Union[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Whitelisted REST endpoint for AI-F005 Financing Matcher."""
    if HAS_FRAPPE:
        try:
            company = get_verified_company(company)
        except Exception as e:
            frappe.throw(f"Company access error: {str(e)}")

    if isinstance(custom_profile, str):
        try:
            custom_profile = json.loads(custom_profile)
        except Exception:
            custom_profile = None

    return _service_instance.match_financing_for_company(
        company=company,
        amount=amount,
        term_months=int(term_months),
        purpose=purpose,
        custom_profile=custom_profile
    )


@frappe_whitelisted
def simulate_what_if(
    company: str,
    sales_change_pct: float = 0.0,
    collection_delay_days: int = 0,
    supplier_due_shift_days: int = 0,
    payroll_change_pct: float = 0.0,
    opex_change_pct: float = 0.0,
    one_off_expense: float = 0.0,
    financing_amount: float = 0.0,
    financing_term_months: int = 0,
    financing_rate_annual: float = 0.0,
    base_snapshot: Optional[Union[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Whitelisted REST endpoint for Standardized What-if Scenario Engine (9 KPIs)."""
    if HAS_FRAPPE:
        try:
            company = get_verified_company(company)
        except Exception as e:
            frappe.throw(f"Company access error: {str(e)}")

    if isinstance(base_snapshot, str):
        try:
            base_snapshot = json.loads(base_snapshot)
        except Exception:
            base_snapshot = None

    return _service_instance.run_scenario_with_9kpis(
        company=company,
        base_snapshot=base_snapshot,
        sales_change_pct=sales_change_pct,
        collection_delay_days=collection_delay_days,
        supplier_due_shift_days=supplier_due_shift_days,
        payroll_change_pct=payroll_change_pct,
        opex_change_pct=opex_change_pct,
        one_off_expense=one_off_expense,
        financing_amount=financing_amount,
        financing_term_months=financing_term_months,
        financing_rate_annual=financing_rate_annual
    )
