import type {
  ContextVm,
  DocumentVm,
  EmptyVm,
  InvoiceCapability,
  InvoiceVm,
  ResultsVm,
} from "./invoiceActionTypes.ts";

export interface TransportResult {
  status: number;
  data: unknown;
  headers?: Record<string, unknown>;
}

export interface InvoiceActionTransport {
  post(capability: InvoiceCapability, payload: unknown, signal: AbortSignal): Promise<TransportResult>;
}

export type Notice = Extract<InvoiceVm, { kind: "denied" | "expired" | "unavailable" }>;

export interface InvoiceActionState {
  busy: null | "context" | "search" | "open";
  context: ContextVm | null;
  results: ResultsVm | EmptyVm | null;
  selectedId: string | null;
  document: DocumentVm | null;
  notice: Notice | null;
  clarification: string[] | null;
}

export interface ControllerDeps {
  transport: InvoiceActionTransport;
  newRequestId: () => string;
  now: () => number;
  allowDemoSource?: boolean;
}

export const EMPTY_STATE: InvoiceActionState = {
  busy: null,
  context: null,
  results: null,
  selectedId: null,
  document: null,
  notice: null,
  clarification: null,
};
