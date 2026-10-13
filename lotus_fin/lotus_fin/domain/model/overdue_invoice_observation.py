"""Domain model for Authorized Outstanding Invoice Observation.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §3, §4, §5.
Strict Financial Predicate: Option B - PAST_FINAL_DUE_INVOICES.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional
import zoneinfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AuthorizedOutstandingInvoiceObservation(BaseModel):
    """Authoritative snapshot of an invoice observation for overdue evaluation.
    
    Data-source-agnostic contract. Does not assume ERPNext schema.
    Uses strict Decimal validation for monetary amounts and rigorous provenance metadata.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # Identifiers & Provenance
    invoice_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    company_id: str = Field(..., min_length=1, max_length=128)
    source_system: str = Field(..., min_length=1, max_length=64)
    document_version: str = Field(..., min_length=1, max_length=64)
    
    # Financial lifecycle & state
    lifecycle_status: str = Field(..., min_length=1, max_length=32)
    is_return: bool = Field(...)
    is_credit_note: bool = Field(default=False)
    is_write_off: bool = Field(default=False)
    
    # Core Dates & Currency
    posting_date: date = Field(...)
    final_due_date: date = Field(...)
    party_account_currency: str = Field(..., min_length=3, max_length=3)
    invoice_currency: str = Field(..., min_length=3, max_length=3)
    
    # Monetary Outstanding Balance (Exact string representation of finite Decimal)
    outstanding_balance: str = Field(..., min_length=1, max_length=32)
    currency_precision: int = Field(default=2, ge=0, le=6)
    
    # Observational context
    observed_at_utc: str = Field(..., min_length=1, max_length=64)
    site_timezone: str = Field(..., min_length=1, max_length=64)
    
    # Completeness and authorized scope
    source_completeness: Literal["COMPLETE", "PARTIAL", "NOT_AVAILABLE"] = Field("COMPLETE")
    authorized_scope: str = Field(..., min_length=1, max_length=128)
    provenance_hash: Optional[str] = Field(default=None, max_length=128)

    @field_validator("outstanding_balance")
    @classmethod
    def validate_decimal_string(cls, v: str) -> str:
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise ValueError(f"outstanding_balance '{v}' must be a valid decimal string.")
        if not d.is_finite():
            raise ValueError(f"outstanding_balance '{v}' must be a finite decimal.")
        return v

    @field_validator("site_timezone")
    @classmethod
    def validate_tz(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError(f"site_timezone '{v}' must be a valid IANA timezone.")
        return v

    @field_validator("observed_at_utc")
    @classmethod
    def validate_iso_timestamps(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            raise ValueError(f"Timestamp '{v}' must be a valid ISO 8601 string.")
        return v

    @property
    def outstanding_decimal(self) -> Decimal:
        return Decimal(self.outstanding_balance)
