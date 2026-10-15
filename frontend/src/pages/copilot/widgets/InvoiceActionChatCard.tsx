import React, { useState } from "react";
import type { InvoiceRowVm, ResultsVm, EmptyVm, DocumentVm } from "../actions/invoiceActionTypes";

export interface InvoiceActionChatCardProps {
  company: string;
  onOpenModalTab?: () => void;
}

const DEMO_INVOICES: InvoiceRowVm[] = [
  {
    invoiceId: "SINV-2026-00088",
    postingDate: "2026-09-15",
    docstatus: 1,
    recordVersion: "v1.2",
    selectionRef: "ref-sinv-88",
  },
  {
    invoiceId: "SINV-2026-00092",
    postingDate: "2026-09-22",
    docstatus: 1,
    recordVersion: "v1.0",
    selectionRef: "ref-sinv-92",
  },
  {
    invoiceId: "SINV-2026-00104",
    postingDate: "2026-09-25",
    docstatus: 0,
    recordVersion: "v0.9",
    selectionRef: "ref-sinv-104",
  },
];

export const InvoiceActionChatCard: React.FC<InvoiceActionChatCardProps> = ({
  company,
  onOpenModalTab,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "DRAFT" | "SUBMITTED">("ALL");
  const [selectedDoc, setSelectedDoc] = useState<DocumentVm | null>(null);
  const [loading, setLoading] = useState(false);

  const filteredInvoices = DEMO_INVOICES.filter((inv) => {
    const matchesSearch = inv.invoiceId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "DRAFT" && inv.docstatus === 0) ||
      (statusFilter === "SUBMITTED" && inv.docstatus === 1);
    return matchesSearch && matchesStatus;
  });

  const handleOpenDoc = (inv: InvoiceRowVm) => {
    setLoading(true);
    setTimeout(() => {
      setSelectedDoc({
        kind: "document",
        companyLabel: company || "Lotus-fin (Demo)",
        cid: "cid-sim-991",
        requestId: "req-read-442",
        sourceMode: "DEMO_ISOLATED",
        observedAt: new Date().toISOString(),
        timezone: "Asia/Ho_Chi_Minh",
        siteRef: "lotus-fin.local",
        productRef: "lotus-core",
        connectionRef: "demo-pipe",
        connectionVersion: "1.0",
        document: {
          invoice_type: "SALES",
          invoice_id: inv.invoiceId,
          posting_date: inv.postingDate,
          docstatus: inv.docstatus,
          record_version: inv.recordVersion,
        },
      });
      setLoading(false);
    }, 250);
  };

  return (
    <div className="w-full rounded-2xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-2xs font-sans text-slate-800 space-y-3.5 my-2">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="size-7 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs shadow-2xs">
            📄
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
              Tra cứu Hóa đơn Bán hàng (L1/L2)
            </h4>
            <div className="text-[11px] text-slate-400">
              Công ty: <span className="font-semibold text-slate-700">{company}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60">
            <span className="size-1.5 rounded-full bg-amber-500 animate-pulse" />
            MÔ PHỎNG DEMO
          </span>
          {onOpenModalTab && (
            <button
              onClick={onOpenModalTab}
              className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer ml-1"
            >
              Mở bộ lọc đầy đủ ↗
            </button>
          )}
        </div>
      </div>

      {/* Detail Read View Modal / In-place expand */}
      {selectedDoc ? (
        <div className="rounded-xl border border-blue-200 bg-blue-50/40 p-3.5 space-y-2.5 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-blue-100 pb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-blue-900 font-mono">
                {selectedDoc.document.invoice_id}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                CHỈ ĐỌC (READ-ONLY)
              </span>
            </div>
            <button
              onClick={() => setSelectedDoc(null)}
              className="text-xs text-slate-400 hover:text-slate-700 px-1.5 py-0.5 rounded hover:bg-white cursor-pointer font-bold"
            >
              ✕ Đóng xem
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px]">Loại chứng từ:</span>
              <span className="font-medium text-slate-800">Hóa đơn Bán hàng</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Ngày ghi nhận:</span>
              <span className="font-medium text-slate-800">{selectedDoc.document.posting_date}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Trạng thái:</span>
              <span className={`font-semibold ${selectedDoc.document.docstatus === 1 ? "text-emerald-700" : "text-slate-600"}`}>
                {selectedDoc.document.docstatus === 1 ? "Đã ghi nhận (Submitted)" : "Bản nháp (Draft)"}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Phiên bản bản ghi:</span>
              <span className="font-mono text-slate-700 text-[11px]">{selectedDoc.document.record_version}</span>
            </div>
            <div className="col-span-2">
              <span className="text-slate-400 block text-[10px]">Mã phiên & nguồn:</span>
              <span className="font-mono text-slate-500 text-[10px] truncate block">{selectedDoc.requestId} · {selectedDoc.sourceMode}</span>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Quick Filter Inputs */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <div className="relative flex-1 min-w-[140px]">
              <input
                type="text"
                placeholder="Tìm mã (VD: SINV-2026)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full text-xs rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 placeholder-slate-400 transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm("")}
                  className="absolute right-2 top-1.5 text-xs text-slate-400 hover:text-slate-600"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-xl">
              {(["ALL", "SUBMITTED", "DRAFT"] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`text-[10px] font-bold px-2 py-1 rounded-lg transition-all cursor-pointer ${
                    statusFilter === st
                      ? "bg-white text-blue-700 shadow-2xs"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {st === "ALL" ? "Tất cả" : st === "SUBMITTED" ? "Đã ghi nhận" : "Nháp"}
                </button>
              ))}
            </div>
          </div>

          {/* Results list */}
          <div className="space-y-1.5 pt-1">
            {filteredInvoices.length === 0 ? (
              <div className="text-center py-4 text-xs text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                Không tìm thấy hóa đơn phù hợp trong phạm vi kiểm tra.
              </div>
            ) : (
              filteredInvoices.map((inv) => (
                <div
                  key={inv.invoiceId}
                  className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 bg-slate-50/40 transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-slate-400 group-hover:text-blue-500 text-xs">🧾</span>
                    <div>
                      <div className="font-mono text-xs font-bold text-slate-900 group-hover:text-blue-700">
                        {inv.invoiceId}
                      </div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <span>{inv.postingDate}</span>
                        <span>•</span>
                        <span
                          className={`font-semibold ${
                            inv.docstatus === 1 ? "text-emerald-600" : "text-amber-600"
                          }`}
                        >
                          {inv.docstatus === 1 ? "Submitted" : "Draft"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    disabled={loading}
                    onClick={() => handleOpenDoc(inv)}
                    className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:border-blue-500 hover:text-blue-600 text-slate-700 text-xs font-semibold shadow-2xs transition-all cursor-pointer disabled:opacity-50"
                  >
                    Mở xem
                  </button>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Footer grounded note */}
      <div className="text-[10px] text-slate-400 border-t border-slate-100 pt-2 flex items-center justify-between">
        <span>Phạm vi hiển thị: 3 hóa đơn mẫu · Không phụ thuộc ERPNext</span>
        <span className="font-mono text-slate-400">P2-B Read Only</span>
      </div>
    </div>
  );
};
