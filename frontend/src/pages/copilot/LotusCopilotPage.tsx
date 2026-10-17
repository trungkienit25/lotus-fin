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
import { DebtReminderManagementView } from "./prepare/DebtReminderManagementView.tsx";
import { PolicyGateAuditView } from "./l5/PolicyGateAuditView.tsx";
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

  // Real chat history loaded from database
  const [chatSessions, setChatSessions] = useState<Array<{ id: string; title: string; time: string; query?: string }>>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Load chat sessions from database
  const fetchChatSessions = () => {
    axios
      .get(`/api/method/lotus_fin.api.copilot_api.list_chat_sessions?company=${encodeURIComponent(selectedCompany)}&limit=50`)
      .then((res) => {
        const list = res.data?.message || [];
        if (Array.isArray(list) && list.length > 0) {
          const mapped = list.map((s: any) => {
            const rawTime = s.last_message_at || s.creation || "";
            let timeLabel = "Today";
            if (rawTime) {
              const d = new Date(rawTime);
              const diffHours = (Date.now() - d.getTime()) / (1000 * 60 * 60);
              if (diffHours < 24) timeLabel = "Today";
              else if (diffHours < 48) timeLabel = "Yesterday";
              else if (diffHours < 168) timeLabel = `${Math.floor(diffHours / 24)} days ago`;
              else timeLabel = d.toLocaleDateString("en-US");
            }
            return {
              id: s.session_id || s.id,
              title: s.title || "Conversation",
              time: timeLabel,
            };
          });
          setChatSessions(mapped);
          if (!activeSessionId) {
            setActiveSessionId(mapped[0].id);
          }
        }
      })
      .catch((err) => {
        console.warn("Failed to load chat sessions:", err);
      });
  };

  useEffect(() => {
    fetchChatSessions();
  }, [selectedCompany]);

  // Trigger prompt in chat stream
  const [activePrompt, setActivePrompt] = useState<string | null>(null);

  const handleTriggerChatPrompt = (query: string) => {
    setActivePrompt(query);
    // Ensure modal is closed when triggering in chat
    setIsReportModalOpen(false);
  };

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    setActivePrompt(null);
    setIsReportModalOpen(false);
  };

  const handleStartNewChat = () => {
    const newId = `session_${Date.now()}`;
    setActiveSessionId(newId);
    setActivePrompt(null);
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

  // Category 1: Auxiliary Financial Analysis & Planning Tools (Clean Executive Labels)
  const financialAnalysisTools: Array<{ id: CopilotTab; label: string; shortLabel: string; desc: string; query: string }> = [
    { id: "financial_health", label: "Corporate Financial Health", shortLabel: "Financial Health", desc: "8 Key Accounting Ratios & P&L", query: "Analyze corporate financial health and key accounting metrics for 2026" },
    { id: "cash_forecast", label: "30-Day Cash Flow Forecast", shortLabel: "Cash Forecast", desc: "Balance Trajectory & AR/AP", query: "Generate 30-day cash flow forecast and evaluate liquidity risk" },
    { id: "risk_signals", label: "Risk Signals Monitoring", shortLabel: "Risk Signals", desc: "Overdue AR & AP Due Dates", query: "Check risk signals for overdue receivables and supplier payment schedules" },
    { id: "what_if", label: "Cash Stress Simulation (What-If)", shortLabel: "What-If Studio", desc: "Stress-Test Scenarios", query: "Run What-If stress test across 9 indicators under revenue fluctuation" },
    { id: "financing_copilot", label: "Credit & Financing Matcher", shortLabel: "Financing Copilot", desc: "Bank Loan Products", query: "Match suitable banking credit and loan facilities based on financial profile" },
    { id: "repayment_schedule", label: "Loan Amortization & Schedule", shortLabel: "Repayment Schedule", desc: "PMT Principal & Interest", query: "Calculate detailed PMT amortization schedule for principal and interest" },
  ];

  // Category 2: ERP Ledger, Database & Operational Audit Tools
  const erpLedgerTools: Array<{ id: CopilotTab; label: string; shortLabel: string; desc: string; query: string }> = [
    { id: "invoice_actions", label: "Sales Invoices Explorer", shortLabel: "Sales Invoices", desc: "Search & Reconcile Invoices", query: "Find invoices with prefix SINV" },
    { id: "past_final_due", label: "Past Final Due Invoices", shortLabel: "Past Due Invoices", desc: "Overdue Receivables List", query: "Show list of past final due sales invoices with outstanding balance" },
    { id: "task_followup", label: "Create Follow-up Task", shortLabel: "Follow-up Tasks", desc: "Initiate Task in ERP Ledger", query: "Create follow-up task for invoice ACC-SINV-2026-00001" },
    { id: "debt_reminder", label: "Customer Debt Reminder", shortLabel: "Debt Reminder", desc: "Draft Customer Notice", query: "Prepare payment reminder and statement for customer" },
    { id: "policy_gate", label: "Accounting Policy Gate", shortLabel: "Policy Gate", desc: "Dual-Control Safety Checks", query: "Verify policy gate for document cancellation and automated payments" },
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
            onClick={handleStartNewChat}
            className="w-full py-2.5 px-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-2xs shrink-0 mb-3"
          >
            <span className="text-base font-bold text-blue-600">+</span>
            <span>New Chat</span>
          </button>

          {/* Top Section: Quick Capabilities & Tools (Auto-collapsed accordions) */}
          <div className="space-y-1.5 shrink-0 pb-3 border-b border-slate-100">
            {/* Accordion 1: Financial Tools */}
            <div className="rounded-xl border border-slate-100 overflow-hidden bg-slate-50/50">
              <button
                onClick={() => setIsFinToolsExpanded(!isFinToolsExpanded)}
                className="w-full flex items-center justify-between px-2.5 py-2 hover:bg-slate-100/80 text-slate-700 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-[10px] text-slate-400 group-hover:text-blue-600 transition-transform duration-200 shrink-0">
                    {isFinToolsExpanded ? "▼" : "▶"}
                  </span>
                  <span className="text-xs font-bold text-slate-700 truncate">
                    Financial Tools
                  </span>
                </div>
                <span className="text-[10px] font-semibold bg-blue-50 text-blue-600 px-1.5 py-0.2 rounded-full shrink-0">
                  {financialAnalysisTools.length}
                </span>
              </button>

              {/* Financial tools list when expanded */}
              {isFinToolsExpanded && (
                <div className="p-1 space-y-0.5 bg-white border-t border-slate-100 max-h-52 overflow-y-auto animate-fadeIn">
                  {financialAnalysisTools.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleTriggerChatPrompt(t.query)}
                      className="w-full text-left p-1.5 rounded-lg hover:bg-blue-50/70 border border-transparent text-slate-700 transition-all flex items-center justify-between cursor-pointer group"
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
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

            {/* Accordion 2: ERP Ledger Tools */}
            <div className="rounded-xl border border-slate-100 overflow-hidden bg-slate-50/50">
              <button
                onClick={() => setIsErpToolsExpanded(!isErpToolsExpanded)}
                className="w-full flex items-center justify-between px-2.5 py-2 hover:bg-slate-100/80 text-slate-700 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-[10px] text-slate-400 group-hover:text-indigo-600 transition-transform duration-200 shrink-0">
                    {isErpToolsExpanded ? "▼" : "▶"}
                  </span>
                  <span className="text-xs font-bold text-slate-700 truncate">
                    ERP Ledger Tools
                  </span>
                </div>
                <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-600 px-1.5 py-0.2 rounded-full shrink-0">
                  {erpLedgerTools.length}
                </span>
              </button>

              {/* ERP Ledger tools list when expanded */}
              {isErpToolsExpanded && (
                <div className="p-1 space-y-0.5 bg-white border-t border-slate-100 max-h-52 overflow-y-auto animate-fadeIn">
                  {erpLedgerTools.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleTriggerChatPrompt(t.query)}
                      className="w-full text-left p-1.5 rounded-lg hover:bg-indigo-50/70 border border-transparent text-slate-700 transition-all flex items-center justify-between cursor-pointer group"
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
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

          {/* Primary Section: Chat History (Placed below for extensive scrollability, like Gemini) */}
          <div className="flex-1 overflow-y-auto pr-1 pt-3 space-y-1 min-h-0">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-2 flex items-center justify-between">
              <span>Chat History</span>
              <span className="text-[10px] text-slate-400 font-normal">{chatSessions.length}</span>
            </div>

            {chatSessions.length === 0 ? (
              <div className="px-3 py-6 text-center text-xs text-slate-400">
                No conversations yet
              </div>
            ) : (
              chatSessions.map((session) => {
                const isActive = activeSessionId === session.id;
                return (
                  <div
                    key={session.id}
                    onClick={() => handleSelectSession(session.id)}
                    className={`p-2 rounded-xl border cursor-pointer transition-all group ${
                      isActive
                        ? "bg-blue-50/80 border-blue-200 text-blue-900 shadow-2xs font-semibold"
                        : "hover:bg-slate-50 border-transparent hover:border-slate-200 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-2 text-xs truncate">
                      <svg
                        className={`size-3.5 shrink-0 ${
                          isActive ? "text-blue-600" : "text-slate-400 group-hover:text-blue-500"
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      <span className="truncate">{session.title}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 pl-5.5 mt-0.5">{session.time}</div>
                  </div>
                );
              })
            )}
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
          key={activeSessionId || "new_session"}
          company={selectedCompany}
          activeSessionId={activeSessionId}
          onSessionChange={(sId) => {
            setActiveSessionId(sId);
            fetchChatSessions();
          }}
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
                    {allFeatureTools.find((t) => t.id === activeReportTab)?.desc || "Real-time general ledger reconciliation"}
                  </div>
                </div>
              </div>

              {/* Right: Window Controls (Maximize & Close) */}
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => setIsModalMaximized(!isModalMaximized)}
                  className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                  title={isModalMaximized ? "Restore window" : "Maximize fullscreen"}
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
                  title="Close window (Esc)"
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
                    handleTriggerChatPrompt(`Draft debt reminder and reconciliation follow-up for invoice ${invId}`);
                  }}
                />
              )}
              {activeReportTab === "past_final_due" && (
                <div className="max-w-4xl mx-auto space-y-4">
                  <V1PastDueChatCard
                    company={selectedCompany}
                    onSelectInvoice={(invId) => {
                      handleTriggerChatPrompt(`Create receivables follow-up task for invoice ${invId}`);
                    }}
                  />
                </div>
              )}
              {activeReportTab === "task_followup" && (
                <div className="max-w-3xl mx-auto space-y-4">
                  <L4ProposalChatCard
                    initialTitle="Follow up overdue receivables ACC-SINV-2026-00001"
                    targetEntity="Sales Invoice/ACC-SINV-2026-00001"
                    company={selectedCompany}
                  />
                </div>
              )}
              {activeReportTab === "debt_reminder" && (
                <div className="py-2">
                  <DebtReminderManagementView
                    company={selectedCompany}
                    onPrepareTask={(taskTitle: string) => {
                      handleTriggerChatPrompt(`Create receivables follow-up task: ${taskTitle}`);
                    }}
                  />
                </div>
              )}
              {activeReportTab === "policy_gate" && (
                <div className="py-2">
                  <PolicyGateAuditView
                    company={selectedCompany}
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

