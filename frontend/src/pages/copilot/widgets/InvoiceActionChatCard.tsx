import React, { useState } from "react";
import type { InvoiceRowVm, DocumentVm } from "../actions/invoiceActionTypes";
import { ModuleBadge } from "../components/ModuleBadge";

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
    }, 200);
  };

  return (
    <div className="w-full mt-3 rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs font-sans text-slate-800 transition-all">
      {/* Top Brand Banner */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-blue-900 via-indigo-950 to-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModuleBadge moduleId="financial_health" size="sm" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-white">
                Tra cứu Hóa đơn Bán hàng (Sales Invoices)
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
                L1 / L2 Engine
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Tra cứu theo đầu mã, kỳ phát sinh và trạng thái chứng từ
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/10 text-slate-200 border border-white/20 backdrop-blur font-mono">
            {company}
          </span>
          {onOpenModalTab && (
            <button
              onClick={onOpenModalTab}
              className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-white text-slate-800 hover:bg-slate-100 transition-all cursor-pointer shadow-2xs"
            >
              Mở Tab Đầy Đủ ↗
            </button>
          )}
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {selectedDoc ? (
          <div className="rounded-xl border border-blue-200 bg-[#F8FAFC] p-4 space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-blue-100 pb-2.5">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-blue-900">
                  {selectedDoc.document.invoice_id}
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                  CHỈ ĐỌC (READ-ONLY)
                </span>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 rounded-lg hover:bg-white cursor-pointer font-bold transition-all"
              >
                ✕ Thu gọn
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-white border border-slate-200/60">
                <span className="text-slate-400 block text-[10px]">Loại chứng từ</span>
                <span className="font-bold text-slate-800 mt-0.5 block">Hóa đơn Bán hàng</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200/60">
                <span className="text-slate-400 block text-[10px]">Ngày ghi nhận</span>
                <span className="font-bold text-slate-800 font-mono mt-0.5 block">{selectedDoc.document.posting_date}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200/60">
                <span className="text-slate-400 block text-[10px]">Trạng thái</span>
                <span className={`font-bold mt-0.5 block ${selectedDoc.document.docstatus === 1 ? "text-emerald-700" : "text-amber-700"}`}>
                  {selectedDoc.document.docstatus === 1 ? "Đã ghi nhận" : "Bản nháp"}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200/60">
                <span className="text-slate-400 block text-[10px]">Phiên bản bản ghi</span>
                <span className="font-mono text-slate-800 font-bold mt-0.5 block">{selectedDoc.document.record_version}</span>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Quick search & Filter bar */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="Nhập mã chứng từ (VD: SINV-2026)..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all"
                />
              </div>

              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
                {(["ALL", "SUBMITTED", "DRAFT"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                      statusFilter === st
                        ? "bg-white text-blue-700 shadow-2xs"
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {st === "ALL" ? "Tất cả" : st === "SUBMITTED" ? "Đã ghi nhận" : "Bản nháp"}
                  </button>
                ))}
              </div>
            </div>

            {/* Invoices List */}
            <div className="space-y-2">
              {filteredInvoices.map((inv) => (
                <div
                  key={inv.invoiceId}
                  className="p-3 rounded-xl border border-slate-200/80 bg-[#F9FBFC] hover:bg-white hover:border-blue-300 transition-all flex items-center justify-between gap-3 shadow-2xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="size-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-500 font-mono text-xs">
                      🧾
                    </div>
                    <div>
                      <span className="font-mono text-xs font-bold text-slate-900 block">
                        {inv.invoiceId}
                      </span>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                        <span>Ngày: {inv.postingDate}</span>
                        <span>•</span>
                        <span className={inv.docstatus === 1 ? "text-emerald-600 font-semibold" : "text-amber-600 font-semibold"}>
                          {inv.docstatus === 1 ? "Submitted" : "Draft"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    disabled={loading}
                    onClick={() => handleOpenDoc(inv)}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-[#1E63B7] text-[#1E63B7] text-xs font-bold shadow-2xs transition-all cursor-pointer hover:bg-blue-50/50"
                  >
                    Mở xem ↗
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Footer */}
        <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
          <span>Phạm vi tra cứu: 3 chứng từ mẫu được phê duyệt</span>
          <span className="font-mono text-slate-400">P2-B Read Only Contract</span>
        </div>
      </div>
    </div>
  );
};
