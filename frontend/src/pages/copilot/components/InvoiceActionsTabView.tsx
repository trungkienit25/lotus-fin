import React, { useState, useEffect } from "react";
import type { InvoiceActionTransport } from "../actions/invoiceActionController";
import type { DemoScenario } from "../demo/demoInvoiceProvider";
import { InvoiceActionPanel } from "../actions/InvoiceActionPanel";
import { ModuleBadge } from "./ModuleBadge";
import type { AuthenticatedActionScope } from "../../../providers/sessionScope.ts";
import { bootstrapSession } from "../../../providers/sessionBootstrap";

interface InvoiceActionsTabViewProps {
  company: string;
  contextKey?: string;
  demoProfile?: "CORE" | "DEMO";
  demoScenario?: DemoScenario;
  onSetDemoProfile?: (profile: "CORE" | "DEMO") => void;
  onSetDemoScenario?: (scenario: DemoScenario) => void;
  activeInvoiceTransport?: InvoiceActionTransport;
  scope?: AuthenticatedActionScope;
  onPrepareFollowup?: (invoiceId: string) => void;
}

export const InvoiceActionsTabView: React.FC<InvoiceActionsTabViewProps> = ({
  company,
  contextKey,
  demoProfile = "CORE",
  demoScenario = "NORMAL",
  activeInvoiceTransport,
  scope,
  onPrepareFollowup,
}) => {
  const [stats, setStats] = useState<{ total: number; submitted: number; draft: number; totalAmount: number }>({
    total: 0,
    submitted: 0,
    draft: 0,
    totalAmount: 0,
  });
  const [loadingStats, setLoadingStats] = useState<boolean>(true);

  // Fetch real ERP stats for live indicator
  useEffect(() => {
    let isMounted = true;
    async function loadRealStats() {
      try {
        const session = await bootstrapSession().catch(() => null);
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (session?.csrfToken) {
          headers["X-Frappe-CSRF-Token"] = session.csrfToken;
        }
        const res = await fetch("/api/method/lotus_fin.api.copilot_api.search_real_invoices", {
          method: "POST",
          headers,
          credentials: "same-origin",
          body: JSON.stringify({ company, limit: 100 }),
        });
        if (res.ok) {
          const wire = await res.json();
          const list: any[] = wire.message?.invoices || [];
          if (isMounted) {
            const submitted = list.filter((x) => x.docstatus === 1).length;
            const draft = list.filter((x) => x.docstatus === 0).length;
            const totalAmount = list.reduce((sum, x) => sum + (Number(x.grandTotal) || 0), 0);
            setStats({ total: list.length, submitted, draft, totalAmount });
            setLoadingStats(false);
          }
          return;
        }
      } catch (err) {
        console.warn("Could not load real invoice stats:", err);
      }
      if (isMounted) {
        setLoadingStats(false);
      }
    }
    loadRealStats();
    return () => {
      isMounted = false;
    };
  }, [company]);

  const scopeKey = `${scope?.actor ?? "anonymous"}:${scope?.sessionEpoch ?? ""}:${company || "lotus-fin"}:${contextKey || "default"}:CORE:REAL`;

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 max-w-5xl mx-auto w-full font-sans">
      {/* Executive Header Banner */}
      <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 p-5 text-white shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="size-11 rounded-xl bg-blue-600/30 border border-blue-400/30 flex items-center justify-center text-xl backdrop-blur">
              🧾
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white">
                  Tra cứu Chứng từ & Hóa đơn Bán hàng (Sales Invoices)
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                  ⚡ ERP Live
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Kết nối thời gian thực cơ sở dữ liệu Frappe ERPNext · Đối chiếu trạng thái hạch toán và giá trị chứng từ
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-slate-200 border border-white/20 font-mono">
              {company || "Lotus-fin"}
            </span>
          </div>
        </div>

        {/* Live Metrics Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-white/10 text-xs">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
            <span className="text-[10px] font-medium text-slate-400 block uppercase tracking-wider">
              Tổng chứng từ
            </span>
            <span className="text-base font-bold text-white mt-0.5 font-mono block">
              {loadingStats ? "..." : stats.total}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
            <span className="text-[10px] font-medium text-slate-400 block uppercase tracking-wider">
              Đã ghi nhận (Submitted)
            </span>
            <span className="text-base font-bold text-emerald-400 mt-0.5 font-mono block">
              {loadingStats ? "..." : stats.submitted}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
            <span className="text-[10px] font-medium text-slate-400 block uppercase tracking-wider">
              Bản nháp (Draft)
            </span>
            <span className="text-base font-bold text-amber-400 mt-0.5 font-mono block">
              {loadingStats ? "..." : stats.draft}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
            <span className="text-[10px] font-medium text-slate-400 block uppercase tracking-wider">
              Tổng phát sinh (USD)
            </span>
            <span className="text-base font-bold text-blue-300 mt-0.5 font-mono block truncate">
              {loadingStats ? "..." : `$${Number(stats.totalAmount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            </span>
          </div>
        </div>
      </div>

      {/* Main Real Action Panel */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs">
        <RealInvoiceExplorer company={company || "Lotus-fin"} onPrepareFollowup={onPrepareFollowup} />
      </div>
    </div>
  );
};

interface RealInvoiceExplorerProps {
  company: string;
  onPrepareFollowup?: (invoiceId: string) => void;
}

const RealInvoiceExplorer: React.FC<RealInvoiceExplorerProps> = ({ company, onPrepareFollowup }) => {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "SUBMITTED" | "DRAFT">("ALL");
  const [selectedInvoice, setSelectedInvoice] = useState<any | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadInvoices() {
      setLoading(true);
      try {
        const session = await bootstrapSession().catch(() => null);
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (session?.csrfToken) {
          headers["X-Frappe-CSRF-Token"] = session.csrfToken;
        }
        const res = await fetch("/api/method/lotus_fin.api.copilot_api.search_real_invoices", {
          method: "POST",
          headers,
          credentials: "same-origin",
          body: JSON.stringify({ company, limit: 100 }),
        });
        if (res.ok) {
          const wire = await res.json();
          const list: any[] = wire.message?.invoices || [];
          if (isMounted) {
            setInvoices(list);
            setLoading(false);
          }
          return;
        }
      } catch (err) {
        console.warn("Could not load invoices:", err);
      }
      if (isMounted) {
        setLoading(false);
      }
    }
    loadInvoices();
    return () => {
      isMounted = false;
    };
  }, [company]);

  const filtered = invoices.filter((inv) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      inv.invoiceId?.toLowerCase().includes(term) ||
      inv.customerName?.toLowerCase().includes(term);
    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "SUBMITTED" && inv.docstatus === 1) ||
      (statusFilter === "DRAFT" && inv.docstatus === 0);
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Tìm theo mã chứng từ hoặc khách hàng (VD: ACC-SINV-2026)..."
            className="w-full text-xs rounded-xl border border-slate-200 bg-[#F9FBFC] px-3.5 py-2.5 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1E63B7]/20 focus:border-[#1E63B7] transition-all"
          />
        </div>

        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl shrink-0">
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

      {selectedInvoice && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/30 p-4 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-blue-100">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-slate-900">
                {selectedInvoice.invoiceId}
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  selectedInvoice.docstatus === 1
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {selectedInvoice.docstatus === 1 ? "Đã ghi nhận (Submitted)" : "Bản nháp (Draft)"}
              </span>
            </div>
            <button
              onClick={() => setSelectedInvoice(null)}
              className="text-xs text-slate-500 hover:text-slate-800 font-bold px-2 py-1 rounded-lg hover:bg-white cursor-pointer"
            >
              ✕ Đóng chi tiết
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-white rounded-xl border border-blue-100">
              <span className="text-[10px] text-slate-400 block uppercase">Khách hàng</span>
              <span className="font-bold text-slate-900 mt-0.5 block truncate">
                {selectedInvoice.customerName || "—"}
              </span>
            </div>
            <div className="p-3 bg-white rounded-xl border border-blue-100">
              <span className="text-[10px] text-slate-400 block uppercase">Ngày ghi nhận</span>
              <span className="font-mono font-bold text-slate-900 mt-0.5 block">
                {selectedInvoice.postingDate || "—"}
              </span>
            </div>
            <div className="p-3 bg-white rounded-xl border border-blue-100">
              <span className="text-[10px] text-slate-400 block uppercase">Tổng tiền chứng từ</span>
              <span className="font-mono font-bold text-blue-700 mt-0.5 block">
                ${Number(selectedInvoice.grandTotal || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="p-3 bg-white rounded-xl border border-blue-100">
              <span className="text-[10px] text-slate-400 block uppercase">Dư nợ còn lại</span>
              <span className="font-mono font-bold text-rose-600 mt-0.5 block">
                ${Number(selectedInvoice.outstandingAmount || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {onPrepareFollowup && (
            <div className="pt-2">
              <button
                type="button"
                onClick={() => onPrepareFollowup(selectedInvoice.invoiceId)}
                className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all cursor-pointer shadow-2xs flex items-center justify-center gap-2"
              >
                <span>✍️ Soạn thư nhắc nợ & Tạo việc theo dõi cho hóa đơn này</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Results List */}
      <div className="space-y-2">
        {loading ? (
          <div className="py-12 text-center text-slate-400 font-sans">
            <span className="inline-block animate-pulse">Đang kết nối cơ sở dữ liệu ERPNext và nạp danh sách hóa đơn...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-12 text-center text-slate-400 font-sans border border-dashed border-slate-200 rounded-xl">
            Không tìm thấy chứng từ nào khớp với bộ lọc hiện tại.
          </div>
        ) : (
          filtered.map((inv) => (
            <div
              key={inv.invoiceId}
              className="p-3.5 rounded-xl border border-slate-200/80 bg-[#F9FBFC] hover:bg-white hover:border-blue-300 transition-all flex items-center justify-between gap-3 shadow-2xs group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="size-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-500 font-mono text-sm shrink-0 group-hover:border-blue-300">
                  🧾
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-900">
                      {inv.invoiceId}
                    </span>
                    {inv.customerName && (
                      <span className="text-xs text-slate-600 truncate max-w-[200px]">
                        • {inv.customerName}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                    <span>Ngày: {inv.postingDate}</span>
                    <span>•</span>
                    <span className={inv.docstatus === 1 ? "text-emerald-600 font-semibold" : "text-amber-600 font-semibold"}>
                      {inv.docstatus === 1 ? "Submitted" : "Draft"}
                    </span>
                    <span>•</span>
                    <span className="font-mono font-semibold text-slate-700">
                      ${Number(inv.grandTotal || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    {inv.outstandingAmount > 0 && (
                      <>
                        <span>•</span>
                        <span className="font-mono font-semibold text-rose-600">
                          Còn nợ: ${Number(inv.outstandingAmount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setSelectedInvoice(inv)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-[#1E63B7] text-[#1E63B7] text-xs font-bold shadow-2xs transition-all cursor-pointer hover:bg-blue-50/50 shrink-0"
              >
                Mở xem ↗
              </button>
            </div>
          ))
        )}
      </div>

      <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
        <span>Hiển thị {filtered.length} / {invoices.length} chứng từ trong phạm vi</span>
        <span className="font-mono text-emerald-600 font-medium">⚡ Connected Frappe ERPNext</span>
      </div>
    </div>
  );
};

