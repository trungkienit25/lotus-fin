"""
Lotus Fin F006 - Repayment Contracts.
Type-safe Pydantic v2 schemas for input validation and output serialization.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RepaymentInputContract(BaseModel):
    principal: float = Field(..., gt=0, description="Loan principal amount in VND")
    annual_rate: float = Field(..., ge=0, le=1.0, description="Annual nominal interest rate as decimal (e.g. 0.085)")
    term_months: int = Field(..., gt=0, description="Repayment tenure in months")
    amortization_method: str = Field(default="EQUAL_INSTALLMENT", description="EQUAL_INSTALLMENT, EQUAL_PRINCIPAL, FLAT_RATE, BULLET")
    payment_frequency: str = Field(default="MONTHLY", description="MONTHLY or QUARTERLY")
    grace_period_months: int = Field(default=0, ge=0, description="Grace period months")
    processing_fee_pct: float = Field(default=0.01, ge=0, le=0.10, description="Processing fee percentage")
    scenario_id: Optional[str] = Field(default="", description="Correlating scenario identifier")


class PeriodRecordContract(BaseModel):
    period: int
    payment_date: str
    opening_balance: float
    principal_payment: float
    interest_payment: float
    total_payment: float
    closing_balance: float
    cumulative_principal: float
    cumulative_interest: float


class ScheduleSummaryContract(BaseModel):
    principal: float
    total_interest: float
    total_fees: float
    total_repayment: float
    total_periods: int
    average_monthly_payment: float
    first_payment: float
    last_payment: float
    interest_to_principal_ratio: float
    currency: str = "VND"


class RepaymentScheduleOutputContract(BaseModel):
    schedule_id: str
    scenario_id: str = ""
    data_mode: str = "simulation"
    loan_terms: Dict[str, Any]
    payment_schedule: List[PeriodRecordContract]
    summary: ScheduleSummaryContract
    cashflow_impact: Dict[str, Any]
    fees: Dict[str, Any]
    assumptions: List[str]
    limitations: List[str]

