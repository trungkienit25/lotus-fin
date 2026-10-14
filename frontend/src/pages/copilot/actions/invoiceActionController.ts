/**
 * Framework-free lifecycle controller for Sales Invoice search -> select -> open.
 *
 * Reuses the B1-S principles: generation counter + AbortController, only the latest
 * eligible response may update state, scope switch/reset clears protected state.
 * No console output, no storage, no URL writes. Transport is injected; the production
 * default (see invoiceActionClient.ts) is disabled.
 */
import type {
  ControllerDeps,
  InvoiceActionState,
  Notice,
} from "./invoiceActionControllerState.ts";
import { EMPTY_STATE } from "./invoiceActionControllerState.ts";
import {
  checkContextUsable,
  executeCall,
  expiredNotice,
} from "./invoiceActionControllerOps.ts";
import {
  buildContextPayload,
  buildOpenPayload,
  buildSearchPayload,
  validateSearchCriteria,
  MESSAGES,
} from "./invoiceActionPresentation.ts";
import type {
  SearchCriteriaInput,
} from "./invoiceActionPresentation.ts";

export * from "./invoiceActionControllerState.ts";

export class InvoiceActionController {
  private state: InvoiceActionState = EMPTY_STATE;
  private generation = 0;
  private abort: AbortController | null = null;
  private scope: string | null = null;
  private listeners = new Set<() => void>();
  private deps: ControllerDeps;

  constructor(deps: ControllerDeps) {
    this.deps = deps;
  }

  getState = (): InvoiceActionState => this.state;

  subscribe = (fn: () => void): (() => void) => {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  };

  private set(patch: Partial<InvoiceActionState>) {
    this.state = { ...this.state, ...patch };
    this.listeners.forEach((l) => l());
  }

  private fence(): { gen: number; signal: AbortSignal } {
    this.abort?.abort();
    this.abort = new AbortController();
    this.generation += 1;
    return { gen: this.generation, signal: this.abort.signal };
  }

  reset = () => {
    this.abort?.abort();
    this.abort = null;
    this.generation += 1;
    this.state = EMPTY_STATE;
    this.listeners.forEach((l) => l());
  };

  setScope = (key: string) => {
    if (this.scope === key) return;
    const first = this.scope === null;
    this.scope = key;
    if (!first) this.reset();
  };

  private clearProtected = (notice: Notice) => {
    this.set({ busy: null, context: null, results: null, selectedId: null, document: null, notice, clarification: null });
  };

  loadContext = async (companyCandidate: string) => {
    const { gen, signal } = this.fence();
    this.set({ ...EMPTY_STATE, busy: "context" });
    const vm = await executeCall(this.deps, "invoice.context", buildContextPayload({
      requestId: this.deps.newRequestId(), companyCandidate,
    }), signal);
    if (vm === "aborted" || gen !== this.generation) return;
    if (vm.kind === "context") {
      if (this.deps.now() >= Date.parse(vm.expiresAt)) {
        this.clearProtected(expiredNotice());
        return;
      }
      this.set({ busy: null, context: vm });
    }
    else if (vm.kind === "denied" || vm.kind === "expired" || vm.kind === "unavailable") this.clearProtected(vm);
    else this.clearProtected({ kind: "unavailable", reason: "INVALID_RESPONSE", message: MESSAGES.INVALID_RESPONSE, cid: null });
  };

  search = async (input: SearchCriteriaInput, pageSize?: number) => {
    const ctx = this.state.context;
    const checked = validateSearchCriteria(input, ctx?.defaults ?? null);
    if (!checked.ok) { this.set({ clarification: checked.questions, notice: null }); return; }
    const usable = checkContextUsable(this.state, this.deps, this.clearProtected);
    if (!usable) return;
    const { gen, signal } = this.fence();
    this.set({ busy: "search", results: null, selectedId: null, document: null, notice: null, clarification: null });
    const vm = await executeCall(this.deps, "invoice.search", buildSearchPayload({
      requestId: this.deps.newRequestId(), contextRef: usable.contextRef, contextVersion: usable.contextVersion,
      filters: checked.filters, pageSize,
    }), signal, usable);
    if (vm === "aborted" || gen !== this.generation) return;
    if (!checkContextUsable(this.state, this.deps, this.clearProtected)) return;
    if (vm.kind === "results" || vm.kind === "empty") this.set({ busy: null, results: vm });
    else if (vm.kind === "denied" || vm.kind === "expired") this.clearProtected(vm);
    else if (vm.kind === "unavailable") {
      if (vm.reason === "INVALID_RESPONSE") this.clearProtected(vm);
      else this.set({ busy: null, results: null, notice: vm });
    }
    else this.clearProtected({ kind: "unavailable", reason: "INVALID_RESPONSE", message: MESSAGES.INVALID_RESPONSE, cid: null });
  };

  openInvoice = async (invoiceId: string) => {
    const results = this.state.results;
    if (!results || results.kind !== "results" || !results.complete) return;
    const item = results.items.find((i) => i.invoiceId === invoiceId);
    if (!item || item.selectionRef === null) return;
    const usable = checkContextUsable(this.state, this.deps, this.clearProtected);
    if (!usable) return;
    const { gen, signal } = this.fence();
    this.set({ busy: "open", selectedId: invoiceId, document: null, notice: null });
    const vm = await executeCall(this.deps, "invoice.open", buildOpenPayload({
      requestId: this.deps.newRequestId(), contextRef: usable.contextRef, contextVersion: usable.contextVersion,
      selectionRef: item.selectionRef,
    }), signal, usable);
    if (vm === "aborted" || gen !== this.generation) return;
    if (!checkContextUsable(this.state, this.deps, this.clearProtected)) return;
    if (vm.kind === "document") {
      const d = vm.document;
      if (d.invoice_id !== item.invoiceId || d.record_version !== item.recordVersion) {
        this.clearProtected({ kind: "unavailable", reason: "INVALID_RESPONSE", message: MESSAGES.INVALID_RESPONSE, cid: vm.cid });
        return;
      }
      this.set({ busy: null, document: vm });
    } else if (vm.kind === "denied" || vm.kind === "expired") this.clearProtected(vm);
    else if (vm.kind === "unavailable") this.clearProtected(vm);
    else this.clearProtected({ kind: "unavailable", reason: "INVALID_RESPONSE", message: MESSAGES.INVALID_RESPONSE, cid: null });
  };
}

