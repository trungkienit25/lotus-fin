from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from lotus_fin.core.domain.entities.scenario import (
    KPIValue,
    ScenarioParameters,
    ScenarioSimulationResult
)

ROUND_INT = Decimal("1.0")
ROUND_RATIO = Decimal("0.0001")


class ScenarioCalculator:
    """
    Consolidated 9-KPI What-if simulation calculator.
    Guarantees deterministic math, zero DB mutation, and data_mode = 'simulation'.
    """

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
        # Baseline extraction
        rev_b = Decimal(str(base_snapshot.get("revenue", "1000000000")))
        cogs_b = Decimal(str(base_snapshot.get("cogs", "600000000")))
        ar_b = Decimal(str(base_snapshot.get("ar_outstanding", "250000000")))
        ap_b = Decimal(str(base_snapshot.get("ap_outstanding", "150000000")))
        inv_b = Decimal(str(base_snapshot.get("inventory_value", "200000000")))
        cash_open = Decimal(str(base_snapshot.get("opening_cash", "300000000")))
        pay_b = Decimal(str(base_snapshot.get("payroll_expense", "120000000")))
        op_b = Decimal(str(base_snapshot.get("opex_expense", "80000000")))
        days = Decimal(str(self.period_days))

        # Baseline metrics
        gp_b = rev_b - cogs_b
        gm_b = (gp_b / rev_b) if rev_b > Decimal("0") else Decimal("0")
        dso_b = (ar_b / rev_b * days) if rev_b > Decimal("0") else Decimal("45")
        dpo_b = (ap_b / cogs_b * days) if cogs_b > Decimal("0") else Decimal("30")
        dio_b = (inv_b / cogs_b * days) if cogs_b > Decimal("0") else Decimal("40")
        ccc_b = dio_b + dso_b - dpo_b
        ncf_b = rev_b - cogs_b - pay_b - op_b
        end_cash_b = cash_open + ncf_b
        shortfall_b = max(Decimal("0"), self.safety_cash_buffer - end_cash_b)

        # Simulation metrics
        s_factor = Decimal("1.0") + params.sales_change_pct
        rev_s = max(Decimal("0"), rev_b * s_factor)
        cogs_s = max(Decimal("0"), cogs_b * s_factor)
        gp_s = rev_s - cogs_s
        gm_s = (gp_s / rev_s) if rev_s > Decimal("0") else Decimal("0")

        dso_s = max(Decimal("0"), dso_b + Decimal(str(params.collection_delay_days)))
        ar_s = (rev_s * dso_s / days) if days > Decimal("0") else ar_b

        dpo_s = max(Decimal("0"), dpo_b + Decimal(str(params.supplier_due_shift_days)))
        ap_s = (cogs_s * dpo_s / days) if days > Decimal("0") else ap_b

        ccc_s = dio_b + dso_s - dpo_s
        pay_s = pay_b * (Decimal("1.0") + params.payroll_change_pct)
        op_s = op_b * (Decimal("1.0") + params.opex_change_pct)

        actual_inflow = rev_s - (ar_s - ar_b)
        actual_supplier_paid = cogs_s - (ap_s - ap_b)

        financing_interest = Decimal("0")
        if params.financing_amount > Decimal("0") and params.financing_rate_annual > Decimal("0"):
            financing_interest = (params.financing_amount * (params.financing_rate_annual / Decimal("12")) * (days / Decimal("30"))).quantize(
                ROUND_INT, rounding=ROUND_HALF_UP
            )

        actual_outflow = actual_supplier_paid + pay_s + op_s + params.one_off_expense + financing_interest
        ncf_s = actual_inflow - actual_outflow
        end_cash_s = cash_open + ncf_s + params.financing_amount
        shortfall_s = max(Decimal("0"), self.safety_cash_buffer - end_cash_s)

        # Build events and limitations
        shortfall_events = []
        if shortfall_s > Decimal("0"):
            shortfall_events.append({
                "date": "T+45 (Giữa kỳ)",
                "projected_cash": float(end_cash_s.quantize(ROUND_INT, rounding=ROUND_HALF_UP)),
                "deficit_amount": float(shortfall_s.quantize(ROUND_INT, rounding=ROUND_HALF_UP)),
                "urgency_level": "CRITICAL" if end_cash_s < Decimal("0") else "HIGH",
                "recommended_action": "Kích hoạt gói tài trợ vốn lưu động hoặc chiết khấu hóa đơn (AI-F005)."
            })

        limitations = [
            "Mô hình giả định cấu trúc biến phí / định phí duy trì ổn định theo kỳ cơ sở.",
            "DIO (số ngày tồn kho) được giả định cố định trong mô phỏng cơ sở.",
            "Kết quả tính mang cờ 'data_mode = simulation' và không thay đổi dữ liệu sổ cái ERPNext."
        ]

        return ScenarioSimulationResult(
            scenario_id=scenario_id,
            company=company,
            base_snapshot_id=str(base_snapshot.get("snapshot_id", "snap_base_001")),
            data_mode="simulation",
            parameters={
                "sales_change_pct": float(params.sales_change_pct),
                "collection_delay_days": params.collection_delay_days,
                "supplier_due_shift_days": params.supplier_due_shift_days,
                "payroll_change_pct": float(params.payroll_change_pct),
                "opex_change_pct": float(params.opex_change_pct),
                "one_off_expense": float(params.one_off_expense),
                "financing_amount": float(params.financing_amount),
                "financing_term_months": params.financing_term_months,
                "financing_rate_annual": float(params.financing_rate_annual)
            },
            revenue=self._kpi("revenue", "Revenue", rev_b, rev_s, "VND"),
            gross_profit=self._kpi("gross_profit", "Gross Profit", gp_b, gp_s, "VND"),
            gross_margin=self._kpi("gross_margin", "Gross Margin", gm_b, gm_s, "%", is_ratio=True),
            ar_outstanding=self._kpi("ar_outstanding", "Accounts Receivable", ar_b, ar_s, "VND"),
            dso=self._kpi("dso", "Days Sales Outstanding", dso_b, dso_s, "days"),
            net_cash_flow=self._kpi("net_cash_flow", "Net Cash Flow", ncf_b, ncf_s, "VND"),
            ending_cash=self._kpi("ending_cash", "Ending Cash Balance", end_cash_b, end_cash_s, "VND"),
            ccc=self._kpi("ccc", "Cash Conversion Cycle", ccc_b, ccc_s, "days"),
            cash_shortfall=self._kpi("cash_shortfall", "Cash Shortfall Deficit", shortfall_b, shortfall_s, "VND"),
            shortfall_events=shortfall_events,
            limitations=limitations
        )

    def _kpi(
        self, metric_id: str, name: str, base_val: Decimal, sim_val: Decimal, unit: str, is_ratio: bool = False
    ) -> KPIValue:
        quant = ROUND_RATIO if is_ratio else ROUND_INT
        abs_change = (sim_val - base_val).quantize(quant, rounding=ROUND_HALF_UP)
        rel_change = None
        limitations = []
        if base_val != Decimal("0"):
            rel_change = float(((sim_val - base_val) / abs(base_val)).quantize(ROUND_RATIO, rounding=ROUND_HALF_UP))
        else:
            limitations.append("Giá trị kỳ cơ sở bằng 0; không tính relative_change.")

        return KPIValue(
            metric_id=metric_id,
            metric_name=name,
            baseline=float(base_val.quantize(quant, rounding=ROUND_HALF_UP)),
            simulation=float(sim_val.quantize(quant, rounding=ROUND_HALF_UP)),
            absolute_change=float(abs_change),
            relative_change=rel_change,
            unit=unit,
            status="AVAILABLE",
            limitations=limitations
        )
