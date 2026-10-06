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
    default_company = company
    if not default_company and frappe is not None:
        default_company = (
            frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
        )
    if not default_company:
        default_company = "Lotus-fin"

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

    service = ScenarioService()
    result = service.run_scenario(params)

    return {
        "status": "success",
        "data": result.to_dict()
    }


if frappe is not None:
    simulate_what_if = frappe.whitelist()(simulate_what_if)
