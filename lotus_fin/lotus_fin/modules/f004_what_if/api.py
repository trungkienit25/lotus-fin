from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    import frappe
    from frappe import _
except ImportError:
    frappe = None
    _ = lambda x: x

from lotus_fin.modules.f004_what_if.domain.models import ScenarioParameters, quantize_currency
from lotus_fin.modules.f004_what_if.domain.enums import ScenarioType
from lotus_fin.modules.f004_what_if.service import ScenarioService


def simulate_what_if(
    company: Optional[str] = None,
    as_of: Optional[str] = None,
    horizon_days: int = 30,
    scenario_name: str = "Custom What-If",
    sales_change_pct: float = 0.0,
    collection_delay_days: int = 0,
    supplier_due_shift_days: int = 0,
    payroll_change_pct: float = 0.0,
    opex_change_pct: float = 0.0,
    one_off_expense: float = 0.0,
    one_off_expense_date: Optional[str] = None,
    financing_amount: float = 0.0,
    financing_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Whitelisted REST API endpoint for executing What-If Financial Scenarios.
    Strictly marked data_mode = 'simulation' (Zero DB Mutation).
    """
    checked_user = None
    if frappe is not None:
        from lotus_fin.security.access import get_verified_company, check_report_permission
        checked_user = frappe.session.user if hasattr(frappe, "session") and frappe.session else None
        default_company = get_verified_company(company, user=checked_user)
        check_report_permission("General Ledger", user=checked_user, module_id="f004")
        check_report_permission("Accounts Receivable", user=checked_user, module_id="f004")
        check_report_permission("Accounts Payable", user=checked_user, module_id="f004")
    else:
        default_company = company or "Lotus-fin"

    as_of_date = date.fromisoformat(as_of) if as_of else date.today()
    exp_date = date.fromisoformat(one_off_expense_date) if one_off_expense_date else None
    fin_date = date.fromisoformat(financing_date) if financing_date else None

    params = ScenarioParameters(
        company=default_company,
        as_of=as_of_date,
        horizon_days=int(horizon_days),
        scenario_name=scenario_name,
        scenario_type=ScenarioType.CUSTOM,
        sales_change_pct=quantize_currency(sales_change_pct),
        collection_delay_days=int(collection_delay_days),
        supplier_due_shift_days=int(supplier_due_shift_days),
        payroll_change_pct=quantize_currency(payroll_change_pct),
        opex_change_pct=quantize_currency(opex_change_pct),
        one_off_expense=quantize_currency(one_off_expense),
        one_off_expense_date=exp_date,
        financing_amount=quantize_currency(financing_amount),
        financing_date=fin_date
    )

    from lotus_fin.modules.f004_what_if.adapters.baseline_adapter import BaselineSourceAdapter
    baseline_adapter = BaselineSourceAdapter(checked_user=checked_user)
    service = ScenarioService(baseline_adapter=baseline_adapter)
    result = service.run_scenario(params)

    return {
        "status": "success" if result.status.value in ["SUCCESS", "INSUFFICIENT_DATA"] else "error",
        "data": result.to_dict()
    }


if frappe is not None:
    simulate_what_if = frappe.whitelist()(simulate_what_if)
