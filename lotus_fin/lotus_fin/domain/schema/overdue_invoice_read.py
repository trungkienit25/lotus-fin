"""Typed DTOs and Schemas for PastFinalDue Invoices.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §3, §4, §5.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OverdueScanCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    complete: bool = Field(...)
    fetched_rows: int = Field(..., ge=0)
    scanned_rows: int = Field(..., ge=0)
    returned_rows: int = Field(..., ge=0)
    missing_required_data: bool = Field(default=False)
    truncated: bool = Field(default=False)
    reason: Optional[str] = Field(default=None, max_length=256)


class PastFinalDueInvoiceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    invoice_id: str = Field(..., min_length=1, max_length=128)
    final_due_date: date = Field(...)
    current_outstanding_decimal: str = Field(..., min_length=1, max_length=32)
    party_account_currency: str = Field(..., min_length=3, max_length=3)
    source_modified: str = Field(..., min_length=1, max_length=64)
    selection_ref: Optional[str] = Field(default=None, max_length=2048)
    overdue_days: int = Field(..., ge=1)
    evidence_ref: Optional[str] = Field(default=None, max_length=128)

    @field_validator("current_outstanding_decimal")
    @classmethod
    def validate_decimal_string(cls, v: str) -> str:
        d = Decimal(v)
        if not d.is_finite() or d <= Decimal("0"):
            raise ValueError(f"Amount {v} must be finite positive Decimal string.")
        return v


class PastFinalDueFilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    party_account_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    invoice_id_prefix: Optional[str] = Field(default=None, max_length=128)
    min_overdue_days: Optional[int] = Field(default=None, ge=1)


class PastFinalDueResponseData(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    capability: Literal["PAST_FINAL_DUE_INVOICES"] = Field("PAST_FINAL_DUE_INVOICES")
    contract_version: Literal["p6.overdue.v1"] = Field("p6.overdue.v1")
    observed_at_utc: str = Field(..., min_length=1, max_length=64)
    site_local_date: date = Field(...)
    site_timezone: str = Field(..., min_length=1, max_length=64)
    authorized_scope: str = Field(..., min_length=1, max_length=128)
    provider_mode: Literal["CORE", "DEMO", "NATIVE"] = Field(...)
    items: List[PastFinalDueInvoiceItem] = Field(default_factory=list)
    coverage: OverdueScanCoverage = Field(...)
    limitations: List[str] = Field(default_factory=list)
    next_cursor: Optional[str] = Field(default=None, max_length=2048)
