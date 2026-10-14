import { useEffect, useState, useSyncExternalStore } from "react";
import { InvoiceActionController } from "./invoiceActionController.ts";
import type { InvoiceActionState, InvoiceActionTransport } from "./invoiceActionController.ts";

export interface UseInvoiceActionsOptions {
  /** Injected transport. Production passes the disabled transport; test/dev composition may inject a synthetic one. */
  transport: InvoiceActionTransport;
  /** Identity of actor/company/site/context. Any change clears protected state and fences late responses. */
  scopeKey: string;
  allowDemoSource?: boolean;
}

function newRequestId(): string {
  return typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : "00000000-0000-4000-8000-000000000000";
}

interface ControllerRecord {
  controller: InvoiceActionController;
  transport: InvoiceActionTransport;
  allowDemoSource: boolean;
  scopeKey: string;
}

export function useInvoiceActions(options: UseInvoiceActionsOptions): {
  state: InvoiceActionState;
  controller: InvoiceActionController;
} {
  const allowDemo = options.allowDemoSource === true;

  const [record, setRecord] = useState<ControllerRecord>(() => {
    const c = new InvoiceActionController({
      transport: options.transport,
      newRequestId,
      now: () => Date.now(),
      allowDemoSource: allowDemo,
    });
    c.setScope(options.scopeKey);
    return {
      controller: c,
      transport: options.transport,
      allowDemoSource: allowDemo,
      scopeKey: options.scopeKey,
    };
  });

  let currentRecord = record;
  const isInitialVerificationTransition =
    record.scopeKey.startsWith("anonymous:") &&
    !options.scopeKey.startsWith("anonymous:") &&
    record.transport === options.transport &&
    record.allowDemoSource === allowDemo;

  if (isInitialVerificationTransition) {
    record.scopeKey = options.scopeKey;
    record.controller.setScope(options.scopeKey);
  }

  const isMismatch =
    record.transport !== options.transport ||
    record.allowDemoSource !== allowDemo ||
    record.scopeKey !== options.scopeKey;

  if (isMismatch) {
    // 1. Immediately dispose old controller: aborts in-flight requests, increments generation, clears state
    record.controller.reset();

    // 2. Instantiate new controller bound strictly to the new security and transport scope
    const nextController = new InvoiceActionController({
      transport: options.transport,
      newRequestId,
      now: () => Date.now(),
      allowDemoSource: allowDemo,
    });
    nextController.setScope(options.scopeKey);

    currentRecord = {
      controller: nextController,
      transport: options.transport,
      allowDemoSource: allowDemo,
      scopeKey: options.scopeKey,
    };
    setRecord(currentRecord);
  }

  // Effect to clean up active controller on unmount or when replaced
  useEffect(() => {
    const activeController = currentRecord.controller;
    return () => {
      activeController.reset();
    };
  }, [currentRecord.controller]);

  const state = useSyncExternalStore(
    currentRecord.controller.subscribe,
    currentRecord.controller.getState,
    currentRecord.controller.getState
  );

  return { state, controller: currentRecord.controller };
}
