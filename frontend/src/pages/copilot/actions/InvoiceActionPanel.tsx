import React, { useEffect, useRef, useState } from "react";
import type { InvoiceActionTransport } from "./invoiceActionController.ts";
import { useInvoiceActions } from "./useInvoiceActions.ts";
import { parseInvoiceIntent } from "./invoiceActionPresentation.ts";
import type { DocStatusFilter, SearchCriteriaInput } from "./invoiceActionPresentation.ts";
import { InvoiceSearchResults } from "./InvoiceSearchResults.tsx";
import { InvoiceReadView } from "./InvoiceReadView.tsx";
import type { AuthenticatedActionScope } from "../../../providers/sessionScope.ts";

export interface InvoiceActionPanelProps {
  /** Candidate only: the server decides whether this company is authorized. */
  companyCandidate: string;
  /** Opaque identity key (actor/site/context); change clears all protected state. */
  scopeKey: string;
  transport: InvoiceActionTransport;
  allowDemoSource?: boolean;
  scope?: AuthenticatedActionScope;
  onPrepareFollowup?: (invoiceId: string) => void;
}

export const InvoiceActionPanel: React.FC<InvoiceActionPanelProps> = ({
  companyCandidate, scopeKey, transport, allowDemoSource, scope, onPrepareFollowup,
}) => {
  const { state, controller } = useInvoiceActions({ transport, scopeKey, allowDemoSource });
  const [prefix, setPrefix] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [status, setStatus] = useState<"" | DocStatusFilter>("");
  const [ask, setAsk] = useState("");
  const [intentNote, setIntentNote] = useState<string[] | null>(null);

  const isVerified = !scope || scope.state === "VERIFIED";

  // Track the last verified actor and session epoch to detect true session invalidations/rotations
  const lastVerifiedActorRef = useRef<string | null>(scope?.state === "VERIFIED" ? (scope.actor ?? null) : null);
  const lastVerifiedEpochRef = useRef<string | null>(scope?.state === "VERIFIED" ? (scope.sessionEpoch ?? null) : null);

  useEffect(() => {
    if (!scope) return;

    if (scope.state === "REVOKED") {
      controller.reset();
      setPrefix("");
      setFrom("");
      setTo("");
      setStatus("");
      setAsk("");
      setIntentNote(null);
      lastVerifiedActorRef.current = null;
      lastVerifiedEpochRef.current = null;
      return;
    }

    if (scope.state === "VERIFIED") {
      const prevActor = lastVerifiedActorRef.current;
      const prevEpoch = lastVerifiedEpochRef.current;
      const currActor = scope.actor;
      const currEpoch = scope.sessionEpoch;

      if (prevActor !== null && (prevActor !== currActor || prevEpoch !== currEpoch)) {
        // Actor changed (User A -> User B) or session epoch rotated
        controller.reset();
        setPrefix("");
        setFrom("");
        setTo("");
        setStatus("");
        setAsk("");
        setIntentNote(null);
        if (companyCandidate) {
          void controller.loadContext(companyCandidate);
        }
      }

      lastVerifiedActorRef.current = currActor;
      lastVerifiedEpochRef.current = currEpoch;
    }
  }, [scope?.state, scope?.actor, scope?.sessionEpoch, controller, companyCandidate]);

  useEffect(() => {
    if (!isVerified) return;
    if (companyCandidate && !state.context) {
      void controller.loadContext(companyCandidate);
    }
  }, [controller, companyCandidate, isVerified, state.context]);

  const criteria = (): SearchCriteriaInput => ({
    ...(prefix !== "" ? { prefix } : {}),
    ...(from !== "" ? { postingFrom: from } : {}),
    ...(to !== "" ? { postingTo: to } : {}),
    ...(status !== "" ? { docstatus: status } : {}),
  });

  const onAsk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isVerified) return;
    const intent = parseInvoiceIntent(ask);
    if (intent.kind === "search") {
      setIntentNote(null);
      const c = intent.criteria;
      setPrefix(c.prefix ?? ""); setFrom(c.postingFrom ?? ""); setTo(c.postingTo ?? ""); setStatus(c.docstatus ?? "");
      void controller.search(c);
    } else if (intent.kind === "clarify") setIntentNote(intent.questions);
    else setIntentNote(["I can search Sales Invoices by invoice number prefix, date range, and Draft/Submitted status."]);
  };

  const busy = state.busy !== null;
  const ctx = state.context;
  const questions = state.clarification ?? intentNote;

  return (
    <div data-testid="invoice-panel" className="space-y-3 text-sm" aria-busy={busy}>
      <div data-testid="context-line" className="text-xs text-gray-600">
        {ctx ? <>Company (set by server): <strong data-testid="company-label">{ctx.companyLabel}</strong></> : "No active invoice search context."}
      </div>

      {!isVerified && (
        <div data-testid="scope-revoked-banner" className="p-3 border border-amber-300 bg-amber-50 rounded-lg text-amber-900 text-xs">
          Session unverified or revoked. Protected invoice actions are disabled.
        </div>
      )}

      <form onSubmit={onAsk} className="flex gap-2" aria-label="Ask about invoices">
        <input data-testid="ask-input" value={ask} onChange={(e) => setAsk(e.target.value)} maxLength={300}
          placeholder="e.g. find submitted invoices SINV-2026" className="flex-1 border rounded px-2 py-1" />
        <button type="submit" data-testid="ask-btn" disabled={busy || !ctx || !isVerified} className="px-3 py-1 rounded border">Ask</button>
      </form>

      <form onSubmit={(e) => { e.preventDefault(); if (!isVerified) return; setIntentNote(null); void controller.search(criteria()); }}
        className="grid grid-cols-2 gap-2" aria-label="Invoice search criteria">
        <label className="col-span-2">Invoice number prefix
          <input data-testid="f-prefix" value={prefix} maxLength={128} onChange={(e) => setPrefix(e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1" />
        </label>
        <label>From date
          <input data-testid="f-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1" />
        </label>
        <label>To date
          <input data-testid="f-to" type="date" value={to} onChange={(e) => setTo(e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1" />
        </label>
        <label className="col-span-2">Status
          <select data-testid="f-docstatus" value={status} onChange={(e) => setStatus(e.target.value as "" | DocStatusFilter)}
            className="mt-1 w-full border rounded px-2 py-1">
            <option value="">Choose…</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="BOTH">Both</option>
          </select>
        </label>
        <button type="submit" data-testid="search-btn" disabled={busy || !ctx || !isVerified}
          className="col-span-2 px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50">Find invoices</button>
      </form>

      {questions && questions.length > 0 && (
        <ul data-testid="clarify" role="status" className="p-3 border border-blue-300 bg-blue-50 rounded-lg list-disc list-inside">
          {questions.map((q) => <li key={q}>{q}</li>)}
        </ul>
      )}

      {state.busy && <div data-testid="loading" role="status">Working… ({state.busy})</div>}

      {state.notice && (
        <div data-testid="notice" data-kind={state.notice.kind} data-reason={state.notice.reason} role="alert"
          className="p-3 border border-red-300 bg-red-50 rounded-lg">
          <div>{state.notice.message}</div>
          {state.notice.cid && <div className="text-xs text-gray-500">Correlation ID {state.notice.cid}</div>}
          {state.notice.kind === "expired" && companyCandidate && (
            <button type="button" data-testid="restart-btn" className="mt-2 px-2 py-1 border rounded"
              onClick={() => void controller.loadContext(companyCandidate)}>Start a new search</button>
          )}
        </div>
      )}

      {state.results && (
        <InvoiceSearchResults results={state.results} selectedId={state.selectedId} busy={busy}
          onOpen={(id) => void controller.openInvoice(id)} />
      )}
      {state.results && state.results.kind !== "empty" && (
        <div className="text-xs text-gray-500" data-testid="search-trace">
          Request ID {state.results.requestId} · Correlation ID {state.results.cid}
        </div>
      )}
      {state.document && <InvoiceReadView doc={state.document} />}
      {state.document && onPrepareFollowup && <button disabled={!isVerified} type="button" className="border rounded p-2" onClick={() => onPrepareFollowup(state.document!.document.invoice_id)}>Soạn lời nhắc cho hóa đơn đã chọn (L3)</button>}
    </div>
  );
};
