/**
 * Response envelope builders for synthetic DEMO transport.
 * Clean, bounded payloads without production or ERPNext leakage.
 * Complies with ADR001 (< 200 lines).
 */
import type { TransportResult } from "../actions/invoiceActionController.ts";
import type { InvoiceCapability } from "../actions/invoiceActionTypes.ts";
import {
  type DemoInvoiceRow,
  DEMO_CONTEXT_VERSION,
  DEMO_COMPANY_LABEL,
  demoSource,
} from "./demoInvoiceTypes.ts";

export function demoForbidden(capability: InvoiceCapability, correlationId: string, requestId: string): TransportResult {
  return {
    status: 403,
    data: {
      message: {
        contract_version: "p1.invoice.v1",
        status: "FORBIDDEN",
        reason_code: "ACCESS_DENIED",
        correlation_id: correlationId,
        request_id: requestId,
        capability,
        source: null,
        context_version: null,
        data: null,
        user_message: "Demo permission denied scenario",
      },
    },
    headers: { "x-correlation-id": correlationId },
  };
}

export function demoError(
  status: 409 | 422,
  reason: string,
  capability: InvoiceCapability,
  correlationId: string,
  requestId: string,
  userMessage: string
): TransportResult {
  return {
    status,
    data: {
      message: {
        contract_version: "p1.invoice.v1",
        status: "NOT_AVAILABLE",
        reason_code: reason,
        correlation_id: correlationId,
        request_id: requestId,
        capability,
        source: null,
        context_version: null,
        data: null,
        user_message: userMessage,
      },
    },
    headers: { "x-correlation-id": correlationId },
  };
}

export function demoContextOk(
  correlationId: string,
  requestId: string,
  contextRef: string,
  expiresAt: string
): TransportResult {
  return {
    status: 200,
    data: {
      message: {
        contract_version: "p1.invoice.v1",
        status: "OK",
        reason_code: "CONTEXT_READY",
        correlation_id: correlationId,
        request_id: requestId,
        capability: "invoice.context",
        source: demoSource("PAGE_COMPLETE"),
        context_version: DEMO_CONTEXT_VERSION,
        data: {
          context_ref: contextRef,
          context_version: DEMO_CONTEXT_VERSION,
          company_label: DEMO_COMPANY_LABEL,
          allowed_filters: ["invoice_name_prefix", "posting_date", "docstatus"],
          default_posting_from: "2026-07-15",
          default_posting_to: "2026-10-12",
          expires_at: expiresAt,
        },
        user_message: "Demo context ready",
      },
    },
    headers: { "x-correlation-id": correlationId },
  };
}

export function demoSearchOk(
  correlationId: string,
  requestId: string,
  items: DemoInvoiceRow[],
  complete: boolean,
  reason: string,
  limitations: string[] | null = null
): TransportResult {
  const isPartial = !complete && limitations !== null;
  return {
    status: 200,
    data: {
      message: {
        contract_version: "p1.invoice.v1",
        status: isPartial ? "PARTIAL" : "OK",
        reason_code: reason,
        correlation_id: correlationId,
        request_id: requestId,
        capability: "invoice.search",
        source: demoSource(complete ? "PAGE_COMPLETE" : "INCOMPLETE"),
        context_version: DEMO_CONTEXT_VERSION,
        data: {
          items,
          returned_count: items.length,
          total_count: null,
          page_complete: complete,
          has_more: complete ? false : null,
          next_cursor: null,
          selection_required: items.length > 0,
          limitations,
        },
        user_message: "Demo search results",
      },
    },
    headers: { "x-correlation-id": correlationId },
  };
}

export function demoOpenOk(
  correlationId: string,
  requestId: string,
  doc: DemoInvoiceRow
): TransportResult {
  return {
    status: 200,
    data: {
      message: {
        contract_version: "p1.invoice.v1",
        status: "OK",
        reason_code: "DOCUMENT_READY",
        correlation_id: correlationId,
        request_id: requestId,
        capability: "invoice.open",
        source: demoSource("PAGE_COMPLETE"),
        context_version: DEMO_CONTEXT_VERSION,
        data: {
          document: {
            invoice_type: "SALES",
            invoice_id: doc.invoice_id,
            posting_date: doc.posting_date,
            docstatus: doc.docstatus,
            record_version: doc.record_version,
          },
          company_label: DEMO_COMPANY_LABEL,
          navigation: {
            kind: "LOTUS_READ_VIEW",
            view: "sales-invoice-minimal-v1",
          },
        },
        user_message: "Demo document open ready",
      },
    },
    headers: { "x-correlation-id": correlationId },
  };
}
