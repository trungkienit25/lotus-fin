from decimal import Decimal
from typing import List
import uuid
from lotus_fin.ai004.domain.models import SimulatedCashEvent, ScenarioParameters, quantize_currency
from lotus_fin.ai004.domain.enums import CashFlowDirection, EventCategory
from .base import IScenarioModifier


class ExpenseModifier(IScenarioModifier):
    """
    Strategy: Modifies OPEX/Payroll recurring outflows and/or injects one-off expense shocks.
    """

    def is_active(self, params: ScenarioParameters) -> bool:
        return (
            params.payroll_change_pct != Decimal("0.00")
            or params.opex_change_pct != Decimal("0.00")
            or params.one_off_expense > Decimal("0.00")
        )

    def apply(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> List[SimulatedCashEvent]:
        payroll_mult = Decimal("1.00") + params.payroll_change_pct
        opex_mult = Decimal("1.00") + params.opex_change_pct

        result: List[SimulatedCashEvent] = []
        for ev in events:
            if ev.direction == CashFlowDirection.OUTFLOW and ev.category == EventCategory.PAYROLL and params.payroll_change_pct != Decimal("0.00"):
                new_amt = quantize_currency(ev.amount * max(Decimal("0.00"), payroll_mult))
                result.append(
                    SimulatedCashEvent(
                        id=ev.id,
                        category=ev.category,
                        direction=ev.direction,
                        amount=new_amt,
                        date=ev.date,
                        description=f"{ev.description} (Payroll {params.payroll_change_pct * 100:+.0f}%)",
                        source_ref=ev.source_ref,
                        original_amount=ev.original_amount or ev.amount,
                        original_date=ev.original_date or ev.date,
                        is_synthetic=ev.is_synthetic
                    )
                )
            elif ev.direction == CashFlowDirection.OUTFLOW and ev.category == EventCategory.OPEX and params.opex_change_pct != Decimal("0.00"):
                new_amt = quantize_currency(ev.amount * max(Decimal("0.00"), opex_mult))
                result.append(
                    SimulatedCashEvent(
                        id=ev.id,
                        category=ev.category,
                        direction=ev.direction,
                        amount=new_amt,
                        date=ev.date,
                        description=f"{ev.description} (OPEX {params.opex_change_pct * 100:+.0f}%)",
                        source_ref=ev.source_ref,
                        original_amount=ev.original_amount or ev.amount,
                        original_date=ev.original_date or ev.date,
                        is_synthetic=ev.is_synthetic
                    )
                )
            else:
                result.append(ev)

        # Inject synthetic one-off expense shock if specified
        if params.one_off_expense > Decimal("0.00"):
            expense_date = params.one_off_expense_date or params.as_of
            result.append(
                SimulatedCashEvent(
                    id=f"SYN-EXP-{uuid.uuid4().hex[:8]}",
                    category=EventCategory.ONE_OFF,
                    direction=CashFlowDirection.OUTFLOW,
                    amount=params.one_off_expense,
                    date=expense_date,
                    description=f"Synthetic One-Off Expense Shock ({params.one_off_expense:,.0f})",
                    source_ref="SIMULATION_INJECTION",
                    original_amount=Decimal("0.00"),
                    original_date=expense_date,
                    is_synthetic=True
                )
            )

        return result

    def get_description(self, params: ScenarioParameters) -> str:
        parts = []
        if params.payroll_change_pct != Decimal("0.00"):
            parts.append(f"Payroll {params.payroll_change_pct * 100:+.1f}%")
        if params.opex_change_pct != Decimal("0.00"):
            parts.append(f"OPEX {params.opex_change_pct * 100:+.1f}%")
        if params.one_off_expense > Decimal("0.00"):
            parts.append(f"One-off Expense {params.one_off_expense:,.0f}")
        return "Expense Modifier: " + ", ".join(parts)
