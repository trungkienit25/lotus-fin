import React from "react";
import type { DocumentVm } from "./invoiceActionPresentation.ts";
import { safeText } from "./invoiceActionPresentation.ts";

const STATUS_LABEL: Record<number, string> = { 0: "Draft", 1: "Submitted" };

/** Fixed read-only Lotus viewer (sales-invoice-minimal-v1): five contract fields + server company label. */
export const InvoiceReadView: React.FC<{ doc: DocumentVm }> = ({ doc }) => {
  const d = doc.document;
  const isSubmitted = d.docstatus === 1;

  return (
    <section
      data-testid="read-view"
      aria-label="Sales invoice (read-only)"
      className="border border-slate-200/80 rounded-2xl bg-white overflow-hidden shadow-xs space-y-4 font-sans animate-fadeIn"
    >
      <header className="p-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-base">📄</span>
          <div>
            <h3 className="font-bold text-xs tracking-tight text-white">
              Sales Invoice Details (ERP Ledger Record)
            </h3>
            <span className="text-[10px] text-slate-300 font-mono">
              {safeText(d.invoice_id)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            data-testid="readonly-badge"
            className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30"
          >
            Read-only
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isSubmitted
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/30"
                : "bg-amber-500/20 text-amber-300 border border-amber-400/30"
            }`}
          >
            {STATUS_LABEL[d.docstatus]}
          </span>
        </div>
      </header>

      {doc.sourceMode === "DEMO_ISOLATED" && (
        <div
          data-testid="demo-banner"
          role="note"
          className="mx-4 p-2.5 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex items-center gap-2"
        >
          <span>ℹ️</span>
          <span>Isolated test data source.</span>
        </div>
      )}

      <div className="p-4 pt-0">
        <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Mã hóa đơn</dt>
            <dd data-testid="f-invoice-id" className="font-mono font-bold text-slate-900 mt-1">
              {safeText(d.invoice_id)}
            </dd>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Loại chứng từ</dt>
            <dd data-testid="f-type" className="font-medium text-slate-800 mt-1">
              Sales Invoice
            </dd>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Đơn vị hạch toán</dt>
            <dd data-testid="f-company" className="font-medium text-slate-800 mt-1">
              {safeText(doc.companyLabel)}
            </dd>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Ngày ghi nhận</dt>
            <dd data-testid="f-date" className="font-mono font-bold text-slate-800 mt-1">
              {safeText(d.posting_date, 10)}
            </dd>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Trạng thái hạch toán</dt>
            <dd data-testid="f-status" className={`font-semibold mt-1 ${isSubmitted ? "text-emerald-700" : "text-amber-700"}`}>
              {STATUS_LABEL[d.docstatus]}
            </dd>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFC] border border-slate-200/60">
            <dt className="text-slate-400 text-[10px] font-medium uppercase tracking-wider">Phiên bản bản ghi</dt>
            <dd data-testid="f-version" className="font-mono font-bold text-slate-800 mt-1 truncate">
              {safeText(d.record_version, 64)}
            </dd>
          </div>
        </dl>
      </div>

      <footer className="text-[10px] text-slate-400 border-t border-slate-100 p-3.5 bg-slate-50/50 flex flex-wrap items-center justify-between gap-2 font-mono" data-testid="trace">
        <div>
          Request ID: <span data-testid="trace-rid">{doc.requestId}</span> · Correlation ID:{" "}
          <span data-testid="trace-cid">{doc.cid}</span>
        </div>
        <div>
          Ghi nhận lúc: {safeText(doc.observedAt, 64)}
        </div>
      </footer>
    </section>
  );
};

