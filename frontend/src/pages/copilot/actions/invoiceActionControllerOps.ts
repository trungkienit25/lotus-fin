/**
 * Operations on invoiceActionController for context, search and open execution.
 */
import type {
  ControllerDeps,
  InvoiceActionState,
  Notice,
} from "./invoiceActionControllerState.ts";
import {
  parseInvoiceOutcome,
  MESSAGES,
} from "./invoiceActionPresentation.ts";
import type {
  ContextVm,
  InvoiceCapability,
  InvoiceVm,
} from "./invoiceActionPresentation.ts";

export function expiredNotice(): Notice {
  return { kind: "expired", reason: "CONTEXT_REQUIRED", message: MESSAGES.EXPIRED, cid: null };
}

export async function executeCall(
  deps: ControllerDeps,
  capability: InvoiceCapability,
  payload: { request_id: string },
  signal: AbortSignal,
  expectedContext?: ContextVm | null,
): Promise<InvoiceVm | "aborted"> {
  try {
    const res = await deps.transport.post(capability, payload, signal);
    const cidHeader = res.headers?.["x-correlation-id"];
    return parseInvoiceOutcome(res.data, {
      capability,
      requestId: payload.request_id,
      httpStatus: res.status,
      cidHeader,
      allowDemoSource: deps.allowDemoSource === true,
      expectedContext,
    });
  } catch (err) {
    const e = err as { name?: string; code?: string } | null;
    if (e?.name === "AbortError" || e?.name === "CanceledError" || e?.code === "ERR_CANCELED") {
      return "aborted" as const;
    }
    const timeout = e?.code === "ECONNABORTED" || e?.code === "ETIMEDOUT" || e?.name === "TimeoutError";
    const reason = timeout ? "TIMEOUT" : "SOURCE_ERROR";
    return {
      kind: "unavailable",
      reason,
      message: timeout ? MESSAGES.TIMEOUT : MESSAGES.SOURCE_ERROR,
      cid: null,
    } as InvoiceVm;
  }
}

export function checkContextUsable(
  state: InvoiceActionState,
  deps: ControllerDeps,
  clearProtected: (notice: Notice) => void,
): ContextVm | null {
  const ctx = state.context;
  if (!ctx) {
    clearProtected(expiredNotice());
    return null;
  }
  if (deps.now() >= Date.parse(ctx.expiresAt)) {
    clearProtected(expiredNotice());
    return null;
  }
  return ctx;
}
