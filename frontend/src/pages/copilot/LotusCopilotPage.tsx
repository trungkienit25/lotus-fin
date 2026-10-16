import React, { useState, useEffect } from "react";
import { useSearchParams, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "../../i18n";
import { formatBrandText } from "../../utils/brand";

import {
  VercelChatPanel,
  FinancialHealthView,
  CashForecastView,
  RiskSignalView,
  WhatIfStudioView,
  FinancingCopilotView,
  RepaymentScheduleView,
  ModuleBadge,
  InvoiceActionsTabView,
} from "./components";
import { createHttpTransport } from "./actions/invoiceActionClient";
import { createDemoInvoiceTransport, type DemoScenario } from "./demo/demoInvoiceProvider";
import type { InvoiceActionTransport } from "./actions/invoiceActionController";

export type CopilotTab =
  | "financial_health"
  | "cash_forecast"
  | "risk_signals"
  | "what_if"
  | "financing_copilot"
  | "repayment_schedule"
  | "invoice_actions";

export const LotusCopilotPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const { pageName } = useParams<{ pageName?: string }>();

  // Determine initial inspector sub-tab
  const getInitialTab = (): CopilotTab => {
    const p = pageName || location.pathname.split("/").pop() || "";
    if (p === "cash-forecast") return "cash_forecast";
    if (p === "risk-signal") return "risk_signals";
    if (p === "what-if-studio") return "what_if";
    if (p === "financing-copilot") return "financing_copilot";
    if (p === "repayment-schedule") return "repayment_schedule";
    if (p === "financial-health") return "financial_health";
    if (p === "invoice-actions") return "invoice_actions";

    const queryTab = searchParams.get("tab") as CopilotTab;
    if (queryTab) return queryTab;

    return "financial_health";
  };

  const [activeReportTab, setActiveReportTab] = useState<CopilotTab>(getInitialTab());
  
  // Direct feature routes open modal by default
  const isDirectFeatureRoute = [
    "financial-health",
    "cash-forecast",
    "risk-signal",
    "what-if-studio",
    "financing-copilot",
    "repayment-schedule",
    "invoice-actions",
  ].includes(pageName || "");

  // Report Modal state
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(isDirectFeatureRoute);
  const [isModalMaximized, setIsModalMaximized] = useState<boolean>(false);
  
  // Left Sidebar & Tools Accordion state (DEFAULT COLLAPSED AS REQUESTED)
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState<boolean>(true);
  const [isToolsExpanded, setIsToolsExpanded] = useState<boolean>(false);

  const [companies, setCompanies] = useState<string[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("Lotus-fin (Demo)");

  // Invoice Actions P2-B Profile & Transport (DEFAULT REAL ERP PRODUCTION)
  const [demoProfile, setDemoProfile] = useState<"CORE" | "DEMO">("CORE");
  const [demoScenario, setDemoScenario] = useState<DemoScenario>("NORMAL");

  const activeInvoiceTransport: InvoiceActionTransport = React.useMemo(() => {
    return createHttpTransport();
  }, []);

  // Recent chat history items
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; time: string; query: string }>>([
    {
      id: "chat-1",
      title: "Phân tích sức khỏe tài chính 2026",
      time: "Hôm nay",
      query: "Tổng hợp sức khỏe tài chính & các chỉ số trọng yếu năm 2026",
    },
    {
      id: "chat-2",
      title: "Dự báo dòng tiền 30 ngày tới",
      time: "Hôm nay",
      query: "Dự báo dòng tiền 30 ngày tới và kiểm tra quỹ đạo số dư cuối ngày",
    },
    {
      id: "chat-3",
      title: "Mô phỏng Stress-Test What-If",
      time: "Hôm qua",
      query: "Chạy mô phỏng Stress-Test What-If nếu doanh thu giảm 20% và khách trả chậm 15 ngày",
    },
    {
      id: "chat-4",
      title: "Kiểm tra nợ quá hạn và NCC",
      time: "2 ngày trước",
      query: "Kiểm tra tín hiệu rủi ro nợ quá hạn và lịch thanh toán nhà cung cấp",
    },
    {
      id: "chat-5",
      title: "Khớp nối gói vay & Lịch trả nợ",
      time: "Tuần này",
      query: "Tìm gói vay phù hợp và tính bảng phân bổ lịch trả nợ PMT",
    },
  ]);

  // Sync tab with URL
  useEffect(() => {
    const currentTab = getInitialTab();
    setActiveReportTab(currentTab);
    if (isDirectFeatureRoute) {
      setIsReportModalOpen(true);
    }
  }, [location.pathname, searchParams, pageName]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isReportModalOpen) {
        setIsReportModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isReportModalOpen]);

  const handleOpenReportModal = (tab?: string) => {
    if (tab) {
      setActiveReportTab(tab as CopilotTab);
    }
    setIsReportModalOpen(true);
  };

  const handleCloseReportModal = () => {
    setIsReportModalOpen(false);
  };

  // Fetch company list
  useEffect(() => {
    axios
      .get('/api/resource/Company?fields=["name"]')
      .then((res) => {
        const comps = (res.data?.data || []).map((c: any) => c.name);
        if (comps.length > 0) {
          setCompanies(comps);
          if (!comps.includes(selectedCompany)) {
            setSelectedCompany(comps[0]);
          }
        }
      })
      .catch(() => {});
  }, []);

  const featureTools: Array<{ id: CopilotTab; label: string; shortLabel: string; desc: string }> = [
    { id: "financial_health", label: "Financial Health (AI001)", shortLabel: "Health (AI001)", desc: "8 key ratios & P&L metrics" },
    { id: "cash_forecast", label: "30-Day Cash Forecast (AI002)", shortLabel: "Cash (AI002)", desc: "Balance trajectory & AR/AP" },
    { id: "risk_signals", label: "Risk Signals (AI003)", shortLabel: "Risk (AI003)", desc: "Overdue debt & AP schedule" },
    { id: "what_if", label: "Stress-Testing Studio (AI004)", shortLabel: "What-If (AI004)", desc: "9-KPI stress simulations" },
    { id: "financing_copilot", label: "Loan Matchmaker (AI005)", shortLabel: "Financing (AI005)", desc: "Bank credit products" },
    { id: "repayment_schedule", label: "Repayment Schedule (AI006)", shortLabel: "Repayment (AI006)", desc: "PMT amortization table" },
    { id: "invoice_actions", label: "Chứng từ & Tác vụ (P2-B)", shortLabel: "Chứng từ", desc: "Tra cứu hóa đơn & việc theo dõi" },
  ];

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-[#F8FAFC] relative">
      {/* 1. Left Chatbot Sidebar (Collapsible History & Financial Sub-tools) */}
      <div
        className={`bg-white border-r border-slate-200 transition-all duration-300 flex flex-col justify-between shrink-0 z-20 ${
          isLeftSidebarOpen ? "w-64" : "w-0 overflow-hidden"
        }`}
      >
        <div className="p-3.5 flex flex-col h-full overflow-hidden">
          {/* New Chat Button */}
          <button
            onClick={() => {
              setIsReportModalOpen(false);
            }}
            className="w-full py-2.5 px-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-2xs shrink-0 mb-3"
          >
            <span className="text-base font-bold text-blue-600">+</span>
            <span>New Chat</span>
          </button>

          {/* Primary Section: Chat History (Always visible & prominent) */}
          <div className="flex-1 overflow-y-auto pr-1 space-y-3 min-h-0">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-1.5 flex items-center justify-between">
                <span>Chat History</span>
                <span className="text-[10px] text-slate-400 font-normal">{recentChats.length}</span>
              </div>
              <div className="space-y-1">
                {recentChats.map((chat) => (
                  <div
                    key={chat.id}
                    onClick={() => {
                      // Trigger chat or focus
                    }}
                    className="p-2 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-200 cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-2 text-xs font-medium text-slate-700 group-hover:text-blue-700 truncate">
                      <svg className="size-3.5 text-slate-400 group-hover:text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span className="truncate">{chat.title}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 pl-5.5 mt-0.5">{chat.time}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Collapsible Auxiliary Tools Accordion (DEFAULT COLLAPSED) */}
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsToolsExpanded(!isToolsExpanded)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50 text-slate-600 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400 group-hover:text-blue-600 transition-transform duration-200">
                    {isToolsExpanded ? "▼" : "▶"}
                  </span>
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                    Auxiliary Financial Tools
                  </span>
                </div>
                <span className="text-[10px] font-semibold bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                  {featureTools.length}
                </span>
              </button>

              {/* Sub-tools list when expanded */}
              {isToolsExpanded && (
                <div className="mt-1.5 space-y-1 pl-1 pr-0.5 animate-fadeIn">
                  {featureTools.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleOpenReportModal(t.id)}
                      className="w-full text-left p-2 rounded-xl hover:bg-blue-50/70 hover:border-blue-200 border border-transparent text-slate-700 transition-all flex items-center justify-between cursor-pointer group"
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        <ModuleBadge moduleId={t.id} size="sm" />
                        <div className="overflow-hidden">
                          <div className="text-xs truncate font-medium text-slate-800 group-hover:text-blue-700">
                            {t.label}
                          </div>
                          <div className="text-[10px] text-slate-400 truncate">{t.desc}</div>
                        </div>
                      </div>
                      <span className="text-[10px] text-blue-500 font-bold opacity-0 group-hover:opacity-100 shrink-0 transition-opacity">
                        ↗
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Bottom Company Info Card */}
          <div className="pt-3 border-t border-slate-100 shrink-0 mt-auto">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">
              Company Audit Scope:
            </label>
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="w-full text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl p-2 text-slate-800 focus:outline-hidden"
            >
              {companies.length > 0 ? (
                companies.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))
              ) : (
                <option value={selectedCompany}>{selectedCompany}</option>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* 2. Main Center Workspace: Full Vercel AI Chatbot Feed (Spacious & 100% Focused) */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        {/* Toggle Left Sidebar Button Bar */}
        <div className="absolute top-3 left-3 z-30">
          <button
            onClick={() => setIsLeftSidebarOpen(!isLeftSidebarOpen)}
            className="p-2 rounded-xl bg-white/90 backdrop-blur border border-slate-200 text-slate-600 hover:text-slate-900 shadow-2xs hover:bg-slate-50 transition-all cursor-pointer"
            title={isLeftSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>
        </div>

        <VercelChatPanel
          company={selectedCompany}
          activeInspectorTab={activeReportTab}
          onOpenInspector={handleOpenReportModal}
          className="h-full"
        />
      </div>

      {/* 3. High-Quality Modal Dialog Popup for Detailed Financial Reports */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 md:p-6 animate-fadeIn">
          <div
            className={`bg-white rounded-2xl shadow-2xl border border-slate-200 w-full flex flex-col overflow-hidden transition-all duration-200 ${
              isModalMaximized
                ? "h-[98vh] max-w-[99vw]"
                : "h-[90vh] max-w-6xl"
            }`}
          >
            {/* Modal Header Bar */}
            <div className="px-5 py-3 border-b border-slate-200 bg-white flex flex-col md:flex-row md:items-center justify-between gap-3 shrink-0">
              {/* Header Title & Company Badge */}
              <div className="flex items-center gap-3">
                <ModuleBadge moduleId={activeReportTab} size="md" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">Financial Analytics & AI Audit</span>
                    <span className="text-[10px] font-semibold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200">
                      {selectedCompany}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Real-time ERPNext General Ledger reconciliation
                  </div>
                </div>
              </div>

              {/* Tabs Switcher Inside Modal */}
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 max-w-full">
                {featureTools.map((tab) => {
                  const isActive = activeReportTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveReportTab(tab.id)}
                      className={`px-2.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-2 ${
                        isActive
                          ? "bg-blue-600 text-white shadow-xs"
                          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                      }`}
                    >
                      <ModuleBadge moduleId={tab.id} size="xs" />
                      <span>{tab.shortLabel}</span>
                    </button>
                  );
                })}
              </div>

              {/* Window Controls: Maximize & Close */}
              <div className="flex items-center gap-1 self-end md:self-auto">
                <button
                  onClick={() => setIsModalMaximized(!isModalMaximized)}
                  className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                  title={isModalMaximized ? "Thu nhỏ cửa sổ" : "Phóng to toàn màn hình"}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {isModalMaximized ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 9L4 4m0 0l5 0m-5 0l0 5m11 11l5 5m0 0l-5 0m5 0l0-5" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                    )}
                  </svg>
                </button>

                <button
                  onClick={handleCloseReportModal}
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
                  title="Đóng cửa sổ (Esc)"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Body: Full Spacious Report Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#F8FAFC]">
              {activeReportTab === "financial_health" && (
                <FinancialHealthView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "cash_forecast" && (
                <CashForecastView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "risk_signals" && (
                <RiskSignalView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "what_if" && (
                <WhatIfStudioView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "financing_copilot" && (
                <FinancingCopilotView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "repayment_schedule" && (
                <RepaymentScheduleView
                  company={selectedCompany}
                  onNavigateTab={(tab) => setActiveReportTab(tab as CopilotTab)}
                />
              )}
              {activeReportTab === "invoice_actions" && (
                <InvoiceActionsTabView
                  company={selectedCompany}
                  demoProfile={demoProfile}
                  demoScenario={demoScenario}
                  onSetDemoProfile={setDemoProfile}
                  onSetDemoScenario={setDemoScenario}
                  activeInvoiceTransport={activeInvoiceTransport}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LotusCopilotPage;

