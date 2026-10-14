"""Minimum P1 search/open data shape, without a competing outcome taxonomy."""
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from lotus_fin.domain.schema.invoice_read import InvoiceReadDocument, InvoiceReadPage, InvoiceReadRow


class SearchResponseDataDTO(InvoiceReadPage):
    pass


class OpenResponseDataDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document: Dict[str, Any]
    company_label: str = Field(..., min_length=1, max_length=128)
    navigation: Dict[str, str]

    @field_validator("document")
    @classmethod
    def minimum_document(cls, value):
        if set(value) != {"invoice_type", "invoice_id", "posting_date", "docstatus", "record_version"}:
            raise ValueError("Invalid minimum document projection")
        return InvoiceReadRow(**value).model_dump(exclude={"selection_ref"})

    @field_validator("navigation")
    @classmethod
    def fixed_navigation(cls, value):
        return InvoiceReadDocument.fixed_navigation(value)

    @classmethod
    def from_document(cls, document: InvoiceReadDocument):
        document = InvoiceReadDocument(**document.model_dump())
        return cls(document=document.model_dump(exclude={"company_label", "navigation"}),
            company_label=document.company_label, navigation=document.navigation)
