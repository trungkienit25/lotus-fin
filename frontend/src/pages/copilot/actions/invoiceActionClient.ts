/**
 * Production transport for invoice actions against Frappe Core.
 *
 * Implements real POST-only communication with CSRF handling, correlation ID
 * capture, abort fencing, and typed outcome envelopes.
 */
import type { InvoiceActionTransport, TransportResult } from "./invoiceActionController.ts";
import type { InvoiceCapability } from "./invoiceActionTypes.ts";
import { bootstrapSession, SessionBootstrapError, sessionGeneration,
  assertSessionGeneration, clearSessionBootstrap, requireSameOrigin } from "../../../providers/sessionBootstrap.ts";
import type { SessionState } from "../../../providers/sessionBootstrap.ts";

export interface HttpTransportOptions {
  baseUrl?: string;
  getCsrfToken?: () => string | null;
  mode?: "http" | "disabled";
}

const CAPABILITY_METHOD_MAP: Record<InvoiceCapability, string> = {
  "invoice.context": "/api/method/lotus_fin.api.invoice_actions_api.get_context",
  "invoice.search": "/api/method/lotus_fin.api.invoice_actions_api.search_invoices",
  "invoice.open": "/api/method/lotus_fin.api.invoice_actions_api.open_invoice",
};

export function isInvoiceActionsFlagOn(env: Record<string, unknown> | undefined): boolean {
  return env?.VITE_LOTUS_INVOICE_ACTIONS === "on";
}

function uuid4(): string {
  return typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : "00000000-0000-4000-8000-000000000000";
}

export function createHttpTransport(options?: HttpTransportOptions): InvoiceActionTransport {
  const baseUrl = options?.baseUrl ?? "";
  requireSameOrigin(baseUrl);

  return {
    async post(capability, payload, signal): Promise<TransportResult> {
      const methodPath = CAPABILITY_METHOD_MAP[capability];
      if (!methodPath) {
        return { status: 422, data: null };
      }

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "application/json",
      };

      const generation = sessionGeneration();
      let csrf: string | null;
      let session: SessionState | undefined;
      try {
        if (options?.getCsrfToken) csrf = options.getCsrfToken();
        else { session = await bootstrapSession(signal); csrf = session.csrfToken; }
      } catch (error) {
        if (error instanceof SessionBootstrapError) return { status: error.status, data: error.data };
        throw error;
      }
      assertSessionGeneration(generation);
      if (csrf) {
        headers["X-Frappe-CSRF-Token"] = csrf;
      }

      const res = await fetch(`${baseUrl}${methodPath}`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        credentials: "same-origin",
        signal,
      });

      const correlationId = res.headers.get("x-correlation-id") || undefined;
      const data = await res.json().catch(() => null);
      assertSessionGeneration(generation);
      if (res.status === 401 || res.status === 403 || (res.status === 400
          && (data as { exc_type?: unknown } | null)?.exc_type === "CSRFTokenError")) {
        clearSessionBootstrap();
      } else if (session) {
        // Fence a reply if another tab changed the cookie during this request.
        const current = await bootstrapSession(signal);
        if (current.user !== session.user || current.csrfToken !== session.csrfToken) {
          clearSessionBootstrap();
          throw new DOMException("Session changed", "AbortError");
        }
      }

      return {
        status: res.status,
        data,
        headers: correlationId ? { "x-correlation-id": correlationId } : undefined,
      };
    },
  };
}

export function createProductionTransport(
  env?: Record<string, unknown>,
  options?: HttpTransportOptions,
): InvoiceActionTransport {
  if (options?.mode === "http" || env?.VITE_LOTUS_API_MODE === "http") {
    return createHttpTransport(options);
  }
  return {
    async post(capability, payload): Promise<TransportResult> {
      const requestId = (payload as { request_id?: string }).request_id ?? uuid4();
      return {
        status: 503,
        data: {
          message: {
            contract_version: "p1.invoice.v1",
            status: "NOT_AVAILABLE",
            reason_code: "CAPABILITY_DISABLED",
            correlation_id: uuid4(),
            request_id: requestId,
            capability,
            source: null,
            context_version: null,
            data: null,
            user_message: "disabled",
          },
        },
      };
    },
  };
}

/** Resolved once at module load by the mounting code; OFF unless explicitly enabled. */
export function readInvoiceActionsFlag(): boolean {
  const meta = import.meta as unknown as { env?: Record<string, unknown> };
  return isInvoiceActionsFlagOn(meta.env);
}
