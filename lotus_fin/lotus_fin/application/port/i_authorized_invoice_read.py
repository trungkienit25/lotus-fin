"""Port interface for authorized invoice read operations.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §1, §4, §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.invoice_read import (
    InvoiceReadDocument,
    InvoiceReadFilters,
    InvoiceReadPage,
)


class IAuthorizedInvoiceReadPort(ABC):
    """Port interface for permission-aware invoice search and document read."""

    @abstractmethod
    def search_invoices(
        self,
        context: AuthorizedReadContext,
        filters: InvoiceReadFilters,
        page_size: int,
        cursor: Optional[str] = None,
        budget=None,
    ) -> Tuple[Optional[InvoiceReadPage], Optional[SourceEvidence], ActionStatus, ActionReasonCode]:
        """Fresh Company/DocType/doc/field policy; count all I/O before execution in budget.

        Query/document grants differ. No full forms, children, permission bypass,
        user switching, mutation or unbounded I/O. Budget must reach every call.
        """
        pass

    @abstractmethod
    def open_invoice(
        self,
        context: AuthorizedReadContext,
        doc_id: str,
        expected_record_version: str,
        budget=None,
    ) -> Tuple[Optional[InvoiceReadDocument], Optional[SourceEvidence], ActionStatus, ActionReasonCode]:
        """Fresh Company/DocType/doc/field rights before exact projected read/version.

        Count metadata, lazy parent hydration, bytes/SQL, doc checks and detail I/O;
        never reuse search permission or treat selection as a permission grant.
        """
        pass
