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
              Tổng phát sinh (VND)
            </span>
            <span className="text-base font-bold text-blue-300 mt-0.5 font-mono block truncate">
              {loadingStats ? "..." : Number(stats.totalAmount).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Main Real Action Panel */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs">
        <InvoiceActionPanel
          companyCandidate={company || "Lotus-fin"}
          scopeKey={scopeKey}
          transport={activeInvoiceTransport || (window as any).__lotusHttpTransport}
          allowDemoSource={false}
          scope={scope}
          onPrepareFollowup={onPrepareFollowup}
        />
      </div>
    </div>
  );
};

