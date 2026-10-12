"""Strict P2-A Invoice Read Schemas and Document Models.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §2, §4, §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from datetime import date
from datetime import timedelta
import hashlib
import json
import unicodedata
from enum import Enum
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


class DocStatusFilter(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    BOTH = "BOTH"


CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class InvoiceReadFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    invoice_name_prefix: Optional[str] = Field(default=None, max_length=128)
    posting_from: Optional[date] = Field(default=None)
    posting_to: Optional[date] = Field(default=None)
    docstatus: DocStatusFilter = Field(default=DocStatusFilter.BOTH)

    @field_validator("posting_from", "posting_to", mode="before")
    @classmethod
    def json_date(cls, value):
        if isinstance(value, str):
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError("Noncanonical date")
            return parsed
        return value

    @field_validator("docstatus", mode="before")
    @classmethod
    def json_enum(cls, value):
        return DocStatusFilter(value) if type(value) is str else value

    @field_validator("invoice_name_prefix", mode="before")
    @classmethod
    def normalize_prefix(cls, value):
        return unicodedata.normalize("NFC", value) if type(value) is str else value

    def normalized(self, today):
        values = self.model_dump()
        if self.posting_from is None:
            values.update(posting_from=today - timedelta(days=89), posting_to=today)
        if values["posting_to"] > today:
            raise ValueError("Future date filter")
        return InvoiceReadFilters(**values)

    def fingerprint(self, page_size):
        query = {"filters": self.model_dump(mode="json"), "page_size": page_size, "order": "name ASC"}
        return hashlib.sha256(json.dumps(query, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @model_validator(mode="after")
    def validate_invariants(self) -> "InvoiceReadFilters":
        if self.invoice_name_prefix is not None:
            if len(self.invoice_name_prefix.strip()) == 0:
                raise ValueError("invoice_name_prefix must not be empty or whitespace only")
            if CONTROL_CHAR_REGEX.search(self.invoice_name_prefix):
                raise ValueError("invoice_name_prefix contains prohibited control characters")

        has_from = self.posting_from is not None
        has_to = self.posting_to is not None
        if has_from != has_to:
            raise ValueError("Both posting_from and posting_to must be provided together or both omitted")

        if has_from and has_to:
            if self.posting_to < self.posting_from:
                raise ValueError("posting_to must not be earlier than posting_from")
            window_days = (self.posting_to - self.posting_from).days + 1
            if window_days > 365:
                raise ValueError(f"Date range must not exceed 365 days (got {window_days})")

        return self


class InvoiceReadRow(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    invoice_type: Literal["SALES"] = Field(default="SALES")
    invoice_id: str = Field(..., min_length=1, max_length=128)
    posting_date: date = Field(...)
    docstatus: Literal[0, 1] = Field(...)
    record_version: str = Field(..., min_length=1, max_length=64)
    selection_ref: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("docstatus", mode="before")
    @classmethod
    def exact_docstatus(cls, value):
        if type(value) is not int:
            raise ValueError("docstatus must be integer")
        return value


class InvoiceReadPage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    items: List[InvoiceReadRow] = Field(default_factory=list)
    returned_count: int = Field(..., ge=0)
    total_count: None = Field(default=None)
    page_complete: bool = Field(...)
    has_more: Optional[bool] = Field(default=None)
    next_cursor: Optional[str] = Field(default=None, max_length=2048)
    selection_required: bool = Field(default=True)
    limitations: Optional[List[Literal["COVERAGE_INCOMPLETE", "LIVE_WINDOW"]]] = Field(default=None)

    @model_validator(mode="after")
    def validate_count(self):
        if self.returned_count != len(self.items):
            raise ValueError("Incorrect returned count")
        if len({item.invoice_id for item in self.items}) != len(self.items):
            raise ValueError("Duplicate invoice")
        return self


class InvoiceReadDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    invoice_type: Literal["SALES"] = Field(default="SALES")
    invoice_id: str = Field(..., min_length=1, max_length=128)
    company_label: str = Field(..., min_length=1, max_length=128)
    posting_date: date = Field(...)
    docstatus: Literal[0, 1] = Field(...)
    record_version: str = Field(..., min_length=1, max_length=64)
    navigation: Dict[str, str] = Field(
        default_factory=lambda: {"kind": "LOTUS_READ_VIEW", "view": "sales-invoice-minimal-v1"}
    )

    @field_validator("navigation")
    @classmethod
    def fixed_navigation(cls, value):
        if value != {"kind": "LOTUS_READ_VIEW", "view": "sales-invoice-minimal-v1"}:
            raise ValueError("Unsupported navigation")
        return value

    @field_validator("docstatus", mode="before")
    @classmethod
    def exact_docstatus(cls, value):
        return InvoiceReadRow.exact_docstatus(value)
