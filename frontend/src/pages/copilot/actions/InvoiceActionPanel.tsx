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
    <div data-testid="invoice-panel" className="space-y-4 text-sm font-sans" aria-busy={busy}>
      <div data-testid="context-line" className="text-xs text-slate-500 flex items-center justify-between pb-2 border-b border-slate-100">
        <div>
          {ctx ? (
            <>
              Phạm vi xác thực: <strong data-testid="company-label" className="text-slate-800">{ctx.companyLabel}</strong>
            </>
          ) : (
            "Chưa có ngữ cảnh tra cứu hóa đơn."
          )}
        </div>
        <span className="text-[10px] font-mono text-slate-400">P2-B Contract Enforced</span>
      </div>

      {!isVerified && (
        <div data-testid="scope-revoked-banner" className="p-3 border border-amber-300 bg-amber-50 rounded-xl text-amber-900 text-xs flex items-center gap-2">
          <span>⚠️</span>
          <span>Phiên đăng nhập chưa được xác thực hoặc bị thu hồi. Thao tác bảo vệ đã tạm dừng.</span>
        </div>
      )}

      {/* Quick Search Bar */}
      <form onSubmit={onAsk} className="flex gap-2" aria-label="Ask about invoices">
        <input
          data-testid="ask-input"
          value={ask}
          onChange={(e) => setAsk(e.target.value)}
          maxLength={300}
          placeholder="Nhập yêu cầu (VD: tìm hóa đơn SINV-2026 đã ghi nhận)..."
          className="flex-1 text-xs rounded-xl border border-slate-200 bg-slate-50/60 px-3.5 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        />
        <button
          type="submit"
          data-testid="ask-btn"
          disabled={busy || !ctx || !isVerified}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all disabled:opacity-50 cursor-pointer shadow-2xs"
        >
          Hỏi
        </button>
      </form>

      {/* Structured Criteria Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!isVerified) return;
          setIntentNote(null);
          void controller.search(criteria());
        }}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-xl border border-slate-200/80 bg-slate-50/40"
        aria-label="Invoice search criteria"
      >
        <div className="col-span-1 sm:col-span-2">
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Đầu mã hóa đơn (Prefix)
          </label>
          <input
            data-testid="f-prefix"
            value={prefix}
            maxLength={128}
            onChange={(e) => setPrefix(e.target.value)}
            placeholder="VD: SINV-2026"
            className="w-full text-xs rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Từ ngày ghi nhận
          </label>
          <input
            data-testid="f-from"
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="w-full text-xs rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Đến ngày ghi nhận
          </label>
          <input
            data-testid="f-to"
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="w-full text-xs rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        <div className="col-span-1 sm:col-span-2">
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Trạng thái chứng từ
          </label>
          <select
            data-testid="f-docstatus"
            value={status}
            onChange={(e) => setStatus(e.target.value as "" | DocStatusFilter)}
            className="w-full text-xs rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          >
            <option value="">Tất cả trạng thái (Hoặc chọn...)</option>
            <option value="DRAFT">Bản nháp (Draft)</option>
            <option value="SUBMITTED">Đã ghi nhận (Submitted)</option>
            <option value="BOTH">Cả hai</option>
          </select>
        </div>

        <button
          type="submit"
          data-testid="search-btn"
          disabled={busy || !ctx || !isVerified}
          className="col-span-1 sm:col-span-2 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-2xs transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5"
        >
          <span>🔍 Tìm kiếm Hóa đơn</span>
        </button>
      </form>

      {questions && questions.length > 0 && (
        <ul data-testid="clarify" role="status" className="p-3.5 border border-blue-200 bg-blue-50/70 rounded-xl list-disc list-inside text-xs text-blue-900 space-y-1">
          {questions.map((q) => <li key={q}>{q}</li>)}
        </ul>
      )}

      {state.busy && (
        <div data-testid="loading" role="status" className="text-xs text-slate-500 flex items-center gap-2 py-1">
          <span className="size-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Đang xử lý ({state.busy})...</span>
        </div>
      )}

      {state.notice && (
        <div data-testid="notice" data-kind={state.notice.kind} data-reason={state.notice.reason} role="alert"
          className="p-3.5 border border-rose-200 bg-rose-50/70 rounded-xl text-xs text-rose-800 space-y-1.5">
          <div className="font-semibold">{state.notice.message}</div>
          {state.notice.cid && <div className="text-[10px] text-rose-500 font-mono">Correlation ID: {state.notice.cid}</div>}
          {state.notice.kind === "expired" && companyCandidate && (
            <button type="button" data-testid="restart-btn" className="mt-1 px-3 py-1 bg-white border border-rose-300 rounded-lg text-rose-700 font-bold hover:bg-rose-50 cursor-pointer"
              onClick={() => void controller.loadContext(companyCandidate)}>Bắt đầu tìm kiếm mới</button>
          )}
        </div>
      )}

      {state.results && (
        <InvoiceSearchResults results={state.results} selectedId={state.selectedId} busy={busy}
          onOpen={(id) => void controller.openInvoice(id)} />
      )}
      {state.results && state.results.kind !== "empty" && (
        <div className="text-[10px] text-slate-400 font-mono" data-testid="search-trace">
          Request ID: {state.results.requestId} · Correlation ID: {state.results.cid}
        </div>
      )}
      {state.document && <InvoiceReadView doc={state.document} />}
      {state.document && onPrepareFollowup && (
        <button
          disabled={!isVerified}
          type="button"
          className="w-full py-2 px-3 rounded-xl border border-blue-200 bg-blue-50/50 hover:bg-blue-100/60 text-blue-700 text-xs font-bold transition-all cursor-pointer shadow-2xs flex items-center justify-center gap-1.5"
          onClick={() => onPrepareFollowup(state.document!.document.invoice_id)}
        >
          <span>✍️ Soạn thư nhắc nợ cho hóa đơn đã chọn (L3)</span>
        </button>
      )}
    </div>
  );
};
