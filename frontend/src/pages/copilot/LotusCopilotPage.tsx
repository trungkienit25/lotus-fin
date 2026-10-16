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
import { IntegratedCapabilities } from "./components/IntegratedCapabilities";
import { FollowupPreview } from "./prepare/FollowupPreview.tsx";
import { V1PastDueChatCard } from "./widgets/V1PastDueChatCard";
import { L4ProposalChatCard } from "./widgets/L4ProposalChatCard";
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
  | "invoice_actions"
  | "past_final_due"
  | "task_followup"
  | "debt_reminder"
  | "policy_gate";

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

  // Trigger prompt in chat stream
  const [activePrompt, setActivePrompt] = useState<string | null>(null);

  const handleTriggerChatPrompt = (query: string) => {
    setActivePrompt(query);
    // Ensure modal is closed when triggering in chat
    setIsReportModalOpen(false);
  };

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

  // Category 1: Auxiliary Financial Analysis & Planning Tools (AI001 - AI006)
  const financialAnalysisTools: Array<{ id: CopilotTab; label: string; shortLabel: string; desc: string; query: string }> = [
    { id: "financial_health", label: "Financial Health (AI001)", shortLabel: "Health (AI001)", desc: "8 key ratios & P&L metrics", query: "Phân tích sức khỏe tài chính & các chỉ số kế toán trọng yếu năm 2026" },
    { id: "cash_forecast", label: "30-Day Cash Forecast (AI002)", shortLabel: "Cash (AI002)", desc: "Balance trajectory & AR/AP", query: "Dự báo dòng tiền 30 ngày tới và đánh giá rủi ro thanh khoản" },
    { id: "risk_signals", label: "Risk Signals (AI003)", shortLabel: "Risk (AI003)", desc: "Overdue debt & AP schedule", query: "Kiểm tra tín hiệu rủi ro nợ quá hạn và lịch trả nợ nhà cung cấp" },
    { id: "what_if", label: "Stress-Testing Studio (AI004)", shortLabel: "What-If (AI004)", desc: "9-KPI stress simulations", query: "Chạy mô phỏng Stress-Test What-If 9 chỉ số nếu doanh thu biến động" },
    { id: "financing_copilot", label: "Loan Matchmaker (AI005)", shortLabel: "Financing (AI005)", desc: "Bank credit products", query: "Gợi ý các gói vay tín dụng ngân hàng phù hợp với hồ sơ tài chính" },
    { id: "repayment_schedule", label: "Repayment Schedule (AI006)", shortLabel: "Repayment (AI006)", desc: "PMT amortization table", query: "Lập bảng phân bổ lịch trả nợ PMT gốc và lãi chi tiết" },
  ];

  // Category 2: ERP Ledger, Database & Operational Audit Tools
  const erpLedgerTools: Array<{ id: CopilotTab; label: string; shortLabel: string; desc: string; query: string }> = [
    { id: "invoice_actions", label: "Tra cứu Chứng từ (L1/L2)", shortLabel: "Chứng từ (L1/L2)", desc: "Tìm kiếm & đối soát Sales Invoices", query: "Tìm hóa đơn có mã SINV" },
    { id: "past_final_due", label: "Hóa đơn Quá hạn Cuối (V1)", shortLabel: "Quá hạn (V1)", desc: "Hóa đơn quá hạn cuối còn dư nợ", query: "Cho tôi xem danh sách hóa đơn quá hạn cuối còn dư nợ" },
    { id: "task_followup", label: "Tạo Việc Theo dõi ERP (L4)", shortLabel: "Tạo việc (L4)", desc: "Khởi tạo tác vụ theo dõi trên tabTask", query: "Tạo task theo dõi công nợ cho hóa đơn ACC-SINV-2026-00001" },
    { id: "debt_reminder", label: "Soạn Thư Nhắc Nợ (L3)", shortLabel: "Nhắc nợ (L3)", desc: "Bản nháp gửi khách hàng kiểm toán", query: "Soạn thư nhắc nợ đối soát công nợ cho khách hàng" },
    { id: "policy_gate", label: "Cổng Chính sách Tác động (L5)", shortLabel: "Chính sách (L5)", desc: "Kiểm soát an toàn dual-control", query: "Đánh giá chính sách hủy bỏ chứng từ hoặc gửi thanh toán tự động" },
  ];

  const allFeatureTools = [...financialAnalysisTools, ...erpLedgerTools];

  // Accordion open/close states
  const [isFinToolsExpanded, setIsFinToolsExpanded] = useState<boolean>(false);
  const [isErpToolsExpanded, setIsErpToolsExpanded] = useState<boolean>(false);

  // Modal Left Sidebar category dropdown open/close states
  const [isModalFinOpen, setIsModalFinOpen] = useState<boolean>(true);
  const [isModalErpOpen, setIsModalErpOpen] = useState<boolean>(true);

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
              setActivePrompt(null);
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
                    onClick={() => handleTriggerChatPrompt(chat.query)}
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

            {/* Accordion 1: Auxiliary Financial Tools (AI001 - AI006) */}
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsFinToolsExpanded(!isFinToolsExpanded)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50 text-slate-600 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-xs text-slate-400 group-hover:text-blue-600 transition-transform duration-200 shrink-0">
                    {isFinToolsExpanded ? "▼" : "▶"}
                  </span>
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-tight truncate whitespace-nowrap">
                    Financial Tools
                  </span>
                </div>
                <span className="text-[10px] font-semibold bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded shrink-0 ml-1">
                  {financialAnalysisTools.length}
                </span>
              </button>

              {/* Financial tools list when expanded: triggers in chat directly */}
              {isFinToolsExpanded && (
                <div className="mt-1.5 space-y-1 pl-1 pr-0.5 animate-fadeIn">
                  {financialAnalysisTools.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleTriggerChatPrompt(t.query)}
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
                        💬
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Accordion 2: ERP Ledger & Database Audit Tools (Tra cứu DB, Sổ cái & Chứng từ) */}
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsErpToolsExpanded(!isErpToolsExpanded)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50 text-slate-600 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-xs text-slate-400 group-hover:text-indigo-600 transition-transform duration-200 shrink-0">
                    {isErpToolsExpanded ? "▼" : "▶"}
                  </span>
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-tight truncate whitespace-nowrap">
                    ERP Ledger Tools
                  </span>
                </div>
                <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded shrink-0 ml-1">
                  {erpLedgerTools.length}
                </span>
              </button>

              {/* ERP Ledger tools list when expanded: triggers in chat directly */}
              {isErpToolsExpanded && (
                <div className="mt-1.5 space-y-1 pl-1 pr-0.5 animate-fadeIn">
                  {erpLedgerTools.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleTriggerChatPrompt(t.query)}
                      className="w-full text-left p-2 rounded-xl hover:bg-indigo-50/70 hover:border-indigo-200 border border-transparent text-slate-700 transition-all flex items-center justify-between cursor-pointer group"
                    >
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        <ModuleBadge moduleId={t.id} size="sm" />
                        <div className="overflow-hidden">
                          <div className="text-xs truncate font-medium text-slate-800 group-hover:text-indigo-700">
                            {t.label}
                          </div>
                          <div className="text-[10px] text-slate-400 truncate">{t.desc}</div>
                        </div>
                      </div>
                      <span className="text-[10px] text-indigo-500 font-bold opacity-0 group-hover:opacity-100 shrink-0 transition-opacity">
                        💬
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
        <VercelChatPanel
          company={selectedCompany}
          activeInspectorTab={activeReportTab}
          onOpenInspector={handleOpenReportModal}
          onToggleSidebar={() => setIsLeftSidebarOpen(!isLeftSidebarOpen)}
          isSidebarOpen={isLeftSidebarOpen}
          externalTriggerPrompt={activePrompt}
          onClearExternalTrigger={() => setActivePrompt(null)}
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
            <div className="px-5 py-3 border-b border-slate-200 bg-white flex items-center justify-between gap-4 shrink-0">
              {/* Left: Title, Active Tab Info & Company Badge */}
              <div className="flex items-center gap-3 min-w-0">
                <ModuleBadge moduleId={activeReportTab} size="md" />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm tracking-tight truncate">
                      {allFeatureTools.find((t) => t.id === activeReportTab)?.label || "Financial Analytics & AI Audit"}
                    </span>
                    <span className="text-[10px] font-semibold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200 shrink-0">
                      {selectedCompany}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">
                    {allFeatureTools.find((t) => t.id === activeReportTab)?.desc || "Đối soát sổ cái kế toán thời gian thực"}
                  </div>
                </div>
              </div>

              {/* Right: Window Controls (Maximize & Close) */}
              <div className="flex items-center gap-1.5 shrink-0">
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

            {/* Modal Body Container with Compact-to-Expanded Left Sidebar */}
            <div className="flex-1 flex overflow-hidden bg-[#F8FAFC]">
              {/* Left Column: Hover-expanding Tool Navigation Column */}
              <div
                className="group/modalsb relative bg-white border-r border-slate-200/90 transition-all duration-300 ease-in-out shrink-0 z-10 flex flex-col w-[54px] hover:w-64 shadow-sm"
              >
                <div className="p-2 flex flex-col h-full overflow-y-auto no-scrollbar">
                  {/* Category 1: Auxiliary Financial Tools */}
                  <div className="mb-2">
                    <button
                      onClick={() => setIsModalFinOpen(!isModalFinOpen)}
                      className="w-full h-7 flex items-center justify-between px-2 rounded-lg hover:bg-slate-50 transition-colors text-left cursor-pointer group/cat1"
                    >
                      <div className="flex items-center gap-1.5 overflow-hidden">
                        <span className="text-[10px] text-slate-400 group-hover/cat1:text-blue-600 transition-transform duration-200">
                          {isModalFinOpen ? "▼" : "▶"}
                        </span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider truncate opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200">
                          Auxiliary Financial
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold bg-blue-50 text-blue-600 px-1 py-0.2 rounded opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200 shrink-0">
                        {financialAnalysisTools.length}
                      </span>
                    </button>

                    {isModalFinOpen && (
                      <div className="space-y-1 mt-1">
                        {financialAnalysisTools.map((tab) => {
                          const isActive = activeReportTab === tab.id;
                          return (
                            <button
                              key={tab.id}
                              onClick={() => setActiveReportTab(tab.id)}
                              className={`w-full flex items-center gap-2.5 p-2 rounded-xl transition-all cursor-pointer text-left ${
                                isActive
                                  ? "bg-blue-50 text-blue-700 font-bold border border-blue-200/80 shadow-2xs"
                                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent"
                              }`}
                              title={tab.label}
                            >
                              <ModuleBadge moduleId={tab.id} size="sm" />
                              <div className="min-w-0 flex-1 overflow-hidden opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                                <div className="text-xs truncate font-medium">{tab.shortLabel}</div>
                                <div className="text-[10px] text-slate-400 truncate font-normal">{tab.desc}</div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Category 2: ERP Ledger & Audit Tools */}
                  <div className="pt-2 border-t border-slate-100">
                    <button
                      onClick={() => setIsModalErpOpen(!isModalErpOpen)}
                      className="w-full h-7 flex items-center justify-between px-2 rounded-lg hover:bg-slate-50 transition-colors text-left cursor-pointer group/cat2"
                    >
                      <div className="flex items-center gap-1.5 overflow-hidden">
                        <span className="text-[10px] text-slate-400 group-hover/cat2:text-indigo-600 transition-transform duration-200">
                          {isModalErpOpen ? "▼" : "▶"}
                        </span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider truncate opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200">
                          ERP Ledger & Audit
                        </span>
                      </div>
                      <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-600 px-1 py-0.2 rounded opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200 shrink-0">
                        {erpLedgerTools.length}
                      </span>
                    </button>

                    {isModalErpOpen && (
                      <div className="space-y-1 mt-1">
                        {erpLedgerTools.map((tab) => {
                          const isActive = activeReportTab === tab.id;
                          return (
                            <button
                              key={tab.id}
                              onClick={() => setActiveReportTab(tab.id)}
                              className={`w-full flex items-center gap-2.5 p-2 rounded-xl transition-all cursor-pointer text-left ${
                                isActive
                                  ? "bg-slate-900 text-white font-bold shadow-2xs"
                                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent"
                              }`}
                              title={tab.label}
                            >
                              <ModuleBadge moduleId={tab.id} size="sm" />
                              <div className="min-w-0 flex-1 overflow-hidden opacity-0 group-hover/modalsb:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                                <div className="text-xs truncate font-medium">{tab.shortLabel}</div>
                                <div className={`text-[10px] truncate font-normal ${isActive ? "text-slate-300" : "text-slate-400"}`}>
                                  {tab.desc}
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Main Content Area */}
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
                  onPrepareFollowup={(invId) => {
                    handleTriggerChatPrompt(`Soạn thư nhắc nợ đối soát công nợ cho hóa đơn ${invId}`);
                  }}
                />
              )}
              {activeReportTab === "past_final_due" && (
                <div className="max-w-4xl mx-auto space-y-4">
                  <V1PastDueChatCard
                    company={selectedCompany}
                    onSelectInvoice={(invId) => {
                      handleTriggerChatPrompt(`Tạo task theo dõi công nợ cho hóa đơn ${invId}`);
                    }}
                  />
                </div>
              )}
              {activeReportTab === "task_followup" && (
                <div className="max-w-3xl mx-auto space-y-4">
                  <L4ProposalChatCard
                    initialTitle="Theo dõi công nợ quá hạn ACC-SINV-2026-00001"
                    targetEntity="Sales Invoice/ACC-SINV-2026-00001"
                    company={selectedCompany}
                  />
                </div>
              )}
              {activeReportTab === "debt_reminder" && (
                <div className="max-w-2xl mx-auto py-4">
                  <FollowupPreview
                    scopeEpoch="epoch-erp-active"
                    onPrepareTask={(body: string) => {
                      handleTriggerChatPrompt(`Tạo task theo dõi công nợ: ${body.slice(0, 50)}...`);
                    }}
                  />
                </div>
              )}
              {activeReportTab === "policy_gate" && (
                <div className="max-w-3xl mx-auto">
                  <IntegratedCapabilities
                    profile={demoProfile}
                    feature="L5"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default LotusCopilotPage;

