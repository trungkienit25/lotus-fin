/**
 * Isolated Synthetic Demo Provider for Lotus Fin Chatbot.
 *
 * Implements a strictly separate, fictional DEMO profile for the complete
 * Search -> Select -> Open lifecycle without touching any production data or ERPNext.
 * Per-instance bounded capability enforcing context, version, TTL, and instance selection.
 * Complies with ADR001 (< 200 lines).
 */
import type { InvoiceActionTransport, TransportResult } from "../actions/invoiceActionController.ts";
import type { InvoiceCapability } from "../actions/invoiceActionTypes.ts";
import {
  type DemoScenario,
  type DemoInvoiceRow,
  DEMO_CONTEXT_VERSION,
  DEMO_COMPANY_LABEL,
  DEMO_RECORDS,
  uuid4,
} from "./demoInvoiceTypes.ts";
import {
  demoForbidden,
  demoError,
  demoContextOk,
  demoSearchOk,
  demoOpenOk,
} from "./demoInvoiceResponses.ts";

export type { DemoScenario, DemoInvoiceRow };
export { DEMO_RECORDS, DEMO_CONTEXT_VERSION, DEMO_COMPANY_LABEL };

export function createDemoInvoiceTransport(scenario: DemoScenario = "NORMAL"): InvoiceActionTransport {
  const instanceId = uuid4();
  let activeContextRef: string | null = null;
  let contextExpiresAt = 0;
  const activeSelections = new Map<string, DemoInvoiceRow>();

  return {
    async post(capability: InvoiceCapability, payload: unknown): Promise<TransportResult> {
      const p = (payload as Record<string, any>) || {};
      const requestId = p.request_id || uuid4();
      const correlationId = uuid4();

      if (scenario === "FORBIDDEN") {
        return demoForbidden(capability, correlationId, requestId);
      }

      if (capability === "invoice.context") {
        contextExpiresAt = Date.now() + 600 * 1000;
        activeContextRef = `ref.v1.ctx.demo.${instanceId}.${correlationId}`;
        activeSelections.clear();
        return demoContextOk(correlationId, requestId, activeContextRef, new Date(contextExpiresAt).toISOString());
      }

      if (scenario === "EXPIRED") {
        return demoError(409, "CONTEXT_CHANGED", capability, correlationId, requestId, "Demo context expired scenario");
      }

      // Enforce context reference, version matching, and TTL expiration
      const isContextValid =
        activeContextRef !== null &&
        p.context_ref === activeContextRef &&
        p.expected_context_version === DEMO_CONTEXT_VERSION &&
        Date.now() < contextExpiresAt;

      if (!isContextValid) {
        return demoError(409, "CONTEXT_CHANGED", capability, correlationId, requestId, "Demo context changed or invalid reference");
      }

      if (capability === "invoice.search") {
        activeSelections.clear();
        if (scenario === "EMPTY") {
          return demoSearchOk(correlationId, requestId, [], true, "EMPTY_RESULT");
        }

        if (scenario === "PARTIAL") {
          const partialItems = DEMO_RECORDS.map((r) => ({ ...r, selection_ref: null }));
          return demoSearchOk(correlationId, requestId, partialItems, false, "COVERAGE_INCOMPLETE", ["COVERAGE_INCOMPLETE"]);
        }

        // NORMAL scenario: filter records and bind unique per-instance selection handles
        const filters = p.filters || {};
        const filtered = DEMO_RECORDS.filter((r) => {
          if (filters.invoice_name_prefix && !r.invoice_id.toUpperCase().startsWith(String(filters.invoice_name_prefix).toUpperCase())) return false;
          if (filters.docstatus === "DRAFT" && r.docstatus !== 0) return false;
          if (filters.docstatus === "SUBMITTED" && r.docstatus !== 1) return false;
          if (filters.posting_from && filters.posting_to && (r.posting_date < filters.posting_from || r.posting_date > filters.posting_to)) return false;
          return true;
        });

        const boundItems = filtered.map((r) => {
          const selRef = `ref.v2.sel.demo.${instanceId}.${r.invoice_id}`;
          const boundRow = { ...r, selection_ref: selRef };
          activeSelections.set(selRef, boundRow);
          return boundRow;
        });

        return demoSearchOk(correlationId, requestId, boundItems, true, boundItems.length > 0 ? "RESULTS_FOUND" : "EMPTY_RESULT");
      }

      if (capability === "invoice.open") {
        if (scenario === "STALE") {
          return demoError(409, "STALE_SELECTION", capability, correlationId, requestId, "Demo stale selection");
        }

        const selectionRef = p.selection_ref;
        const matched = selectionRef ? activeSelections.get(selectionRef) : undefined;
        if (!matched) {
          return demoError(409, "STALE_SELECTION", capability, correlationId, requestId, "Demo unknown or cross-scope selection reference");
        }

        return demoOpenOk(correlationId, requestId, matched);
      }

      return { status: 422, data: null };
    },
  };
}
