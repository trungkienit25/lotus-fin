"""HTTP and Controller DTOs for Past Final Due Invoices."""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams


class PastFinalDueQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    company_id: str = Field(..., min_length=1, max_length=128)
    provider_mode: Literal["CORE", "DEMO", "NATIVE"] = Field(default="CORE")
    filters: Optional[PastFinalDueFilterParams] = Field(default=None)
    page_size: int = Field(default=50, ge=1, le=100)
    cursor: Optional[str] = Field(default=None, max_length=2048)
