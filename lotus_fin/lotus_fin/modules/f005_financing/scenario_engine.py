"""
Lotus Fin AI005 - Standardized What-if Scenario Simulation Engine with 9 KPIs Layer.
Strictly deterministic arithmetic (Decimal, ROUND_HALF_UP).
Guarantees: data_mode = 'simulation', zero database mutation, full evidence lineage.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from .models import KPIValue, ScenarioParameters, ScenarioSimulationResult


class WhatIfScenarioEngine:
    """Simulates What-If scenarios producing standardized 9 KPIs."""

    def __init__(self, period_days: int = 90, safety_cash_buffer: Decimal = Decimal("50000000")):
        self.period_days = period_days
        self.safety_cash_buffer = safety_cash_buffer

    def simulate(
        self,
        base_snapshot: Dict[str, Any],
        params: ScenarioParameters,
        scenario_id: str = "sim_001",
        company: str = "Demo SME"
    ) -> ScenarioSimulationResult:
        rev_base = Decimal(str(base_snapshot.get("revenue", "1000000000")))
        cogs_base = Decimal(str(base_snapshot.get("cogs", "600000000")))
        ar_base = Decimal(str(base_snapshot.get("ar_outstanding", "250000000")))
        ap_base = Decimal(str(base_snapshot.get("ap_outstanding", "150000000")))
        inv_base = Decimal(str(base_snapshot.get("inventory_value", "200000000")))
        cash_open = Decimal(str(base_snapshot.get("opening_cash", "300000000")))
        payroll_base = Decimal(str(base_snapshot.get("payroll_expense", "120000000")))
        opex_base = Decimal(str(base_snapshot.get("opex_expense", "80000000")))
        days = Decimal(str(self.period_days))

        # 1. Baseline Calculations
        gp_base = rev_base - cogs_base
        gm_base = (gp_base / rev_base) if rev_base > Decimal("0") else Decimal("0")
        dso_base = (ar_base / rev_base * days) if rev_base > Decimal("0") else Decimal("45")
        dpo_base = (ap_base / cogs_base * days) if cogs_base > Decimal("0") else Decimal("30")
        dio_base = (inv_base / cogs_base * days) if cogs_base > Decimal("0") else Decimal("40")
        ccc_base = dio_base + dso_base - dpo_base
        ncf_base = rev_base - cogs_base - payroll_base - opex_base
        end_cash_base = cash_open + ncf_base
        shortfall_base = max(Decimal("0"), self.safety_cash_buffer - end_cash_base)

        # 2. Simulation Calculations
        sales_factor = Decimal("1.0") + params.sales_change_pct
        rev_sim = max(Decimal("0"), rev_base * sales_factor)
        cogs_sim = max(Decimal("0"), cogs_base * sales_factor)
        gp_sim = rev_sim - cogs_sim
        gm_sim = (gp_sim / rev_sim) if rev_sim > Decimal("0") else Decimal("0")

        dso_sim = max(Decimal("0"), dso_base + Decimal(str(params.collection_delay_days)))
        ar_sim = (rev_sim * dso_sim / days) if days > Decimal("0") else ar_base
        dpo_sim = max(Decimal("0"), dpo_base + Decimal(str(params.supplier_due_shift_days)))
        ap_sim = (cogs_sim * dpo_sim / days) if days > Decimal("0") else ap_base
        ccc_sim = dio_base + dso_sim - dpo_sim

        payroll_sim = payroll_base * (Decimal("1.0") + params.payroll_change_pct)
        opex_sim = opex_base * (Decimal("1.0") + params.opex_change_pct)
        actual_inflow_sim = rev_sim - (ar_sim - ar_base)

        financing_interest = Decimal("0")
        if params.financing_amount > Decimal("0") and params.financing_rate_annual > Decimal("0"):
            financing_interest = (params.financing_amount * (params.financing_rate_annual / Decimal("12")) * (days / Decimal("30"))).quantize(
                Decimal("1.0"), rounding=ROUND_HALF_UP
            )

        actual_outflow_sim = (cogs_sim - (ap_sim - ap_base)) + payroll_sim + opex_sim + params.one_off_expense + financing_interest
        ncf_sim = actual_inflow_sim - actual_outflow_sim
        end_cash_sim = cash_open + ncf_sim + params.financing_amount
        shortfall_sim = max(Decimal("0"), self.safety_cash_buffer - end_cash_sim)

        shortfall_events = []
        if shortfall_sim > Decimal("0"):
            shortfall_events.append({
                "date": "T+45 (Mid-horizon)",
                "projected_cash": float(end_cash_sim.quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)),
                "deficit_amount": float(shortfall_sim.quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)),
                "urgency_level": "CRITICAL" if end_cash_sim < Decimal("0") else "HIGH",
                "recommended_action": "Activate working capital facility or invoice discounting (AI-F005)."
            })

        return ScenarioSimulationResult(
            scenario_id=scenario_id,
            company=company,
            base_snapshot_id=base_snapshot.get("snapshot_id", "snap_base_001"),
            data_mode="simulation",
            parameters={
                "sales_change_pct": float(params.sales_change_pct),
                "collection_delay_days": params.collection_delay_days,
                "supplier_due_shift_days": params.supplier_due_shift_days,
                "financing_amount": float(params.financing_amount)
            },
            revenue=self._create_kpi("revenue", "Revenue", rev_base, rev_sim, "USD"),
            gross_profit=self._create_kpi("gross_profit", "Gross Profit", gp_base, gp_sim, "USD"),
            gross_margin=self._create_kpi("gross_margin", "Gross Margin", gm_base, gm_sim, "%", is_ratio=True),
            ar_outstanding=self._create_kpi("ar_outstanding", "Accounts Receivable", ar_base, ar_sim, "USD"),
            dso=self._create_kpi("dso", "Days Sales Outstanding", dso_base, dso_sim, "days"),
            net_cash_flow=self._create_kpi("net_cash_flow", "Net Cash Flow", ncf_base, ncf_sim, "USD"),
            ending_cash=self._create_kpi("ending_cash", "Ending Cash Balance", end_cash_base, end_cash_sim, "USD"),
            ccc=self._create_kpi("ccc", "Cash Conversion Cycle", ccc_base, ccc_sim, "days"),
            cash_shortfall=self._create_kpi("cash_shortfall", "Cash Shortfall Deficit", shortfall_base, shortfall_sim, "USD"),
            shortfall_events=shortfall_events,
            limitations=[
                "Model assumes fixed and variable operational cost structures remain stable relative to baseline.",
                "Corporate income tax liabilities are not accrued intra-quarter."
            ]
        )

    def _create_kpi(
        self,
        metric_id: str,
        name: str,
        base_val: Decimal,
        sim_val: Decimal,
        unit: str,
        is_ratio: bool = False
    ) -> KPIValue:
        base_f = float(base_val.quantize(Decimal("0.0001" if is_ratio else "1.0"), rounding=ROUND_HALF_UP))
        sim_f = float(sim_val.quantize(Decimal("0.0001" if is_ratio else "1.0"), rounding=ROUND_HALF_UP))
        diff = sim_f - base_f
        rel = (diff / base_f) if base_f != 0 else 0.0

        return KPIValue(
            metric_id=metric_id,
            metric_name=name,
            baseline=base_f,
            simulation=sim_f,
            absolute_change=diff,
            relative_change=rel,
            unit=unit,
            status="AVAILABLE"
        )
