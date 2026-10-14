import React, { useState, useRef, useEffect, useMemo } from "react";
import { useTranslation } from "../../../i18n";
import { useCopilotRequest } from "./useCopilotRequest";
import { createProductionTransport } from "../actions/invoiceActionClient";
import { createDemoInvoiceTransport, type DemoScenario } from "../demo/demoInvoiceProvider";
import { FollowupPreview } from "../prepare/FollowupPreview.tsx";
import { ChatHeaderBar } from "./ChatHeaderBar";
import { ChatMessageStream } from "./ChatMessageStream";
import { ChatInputComposer } from "./ChatInputComposer";
import { InvoiceActionsTabView } from "./InvoiceActionsTabView";
import type { AttachedFile, ChatMessage, ChatPanelMode, StarterCard } from "./VercelChatPanelTypes";
import type { InvoiceActionTransport } from "../actions/invoiceActionController";
import { useAuthenticatedActionScope, type AuthenticatedActionScope } from "../../../providers/sessionScope.ts";
import { IntegratedCapabilities } from "./IntegratedCapabilities.tsx";
import { createCopilotMessageSender } from "./copilotMessageSender.ts";
export type { AttachedFile, ChatMessage, ChatPanelMode };
export interface VercelChatPanelProps {
  company: string;
  contextKey?: string;
  scope?: AuthenticatedActionScope;
  activeInspectorTab?: string;
  onOpenInspector?: (tab: string) => void;
  onClose?: () => void;
  onExpand?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
  className?: string;
  initialMode?: ChatPanelMode;
}
function createRevokedDemoTransport(): InvoiceActionTransport {
  return {
    async post() {
      return {
        status: 401,
        data: {
          exc_type: "AuthenticationError",
          message: "Session is unverified or revoked",
        },
      };
    },
  };
}
export const VercelChatPanel: React.FC<VercelChatPanelProps> = ({
  company,
  contextKey,
  scope: propsScope,
  activeInspectorTab,
  onOpenInspector,
  onClose,
  onExpand,
  onToggleSidebar,
  isSidebarOpen,
  className = "",
  initialMode = "chat",
}) => {
  const { t } = useTranslation();
  const fallbackScope = useAuthenticatedActionScope();
  const scope = propsScope ?? fallbackScope;
  const [activeMode, setActiveMode] = useState<ChatPanelMode>(initialMode);
  const [feature, setFeature] = useState<"L4" | "L5" | "V1" | null>(null);
  const [taskDraft, setTaskDraft] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState("");
  const selectMode = (mode: ChatPanelMode) => { setFeature(null); setActiveMode(mode); };
  const [demoProfile, setDemoProfile] = useState<"CORE" | "DEMO">("CORE");
  const profileRef = useRef(demoProfile);
  profileRef.current = demoProfile;
  const [demoScenario, setDemoScenario] = useState<DemoScenario>("NORMAL");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const coreTransport = useMemo(() => createProductionTransport(undefined, { mode: "http" }), []);
  const demoTransport = useMemo(() => {
    if (scope.state !== "VERIFIED") {
      return createRevokedDemoTransport();
    }
    return createDemoInvoiceTransport(demoScenario);
  }, [demoScenario, scope.sessionEpoch, scope.actor, scope.state]);
  const activeInvoiceTransport = demoProfile === "DEMO" ? demoTransport : coreTransport;
  const { loading, sendRequest, resetRequest } = useCopilotRequest({
    company,
    contextKey,
    hasQualifiedContext: false,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setMessages([]);
    setInputMessage("");
    setAttachedFiles([]);
    setCopiedId(null);
    setTaskDraft("");
    setSelectedInvoice("");
    setFeature(null);
    resetRequest();
  }, [company, contextKey, scope.sessionEpoch, scope.actor, scope.state, demoProfile, resetRequest]);
  useEffect(() => {
    if (messages.length > 0 || loading) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files: AttachedFile[] = Array.from(e.target.files).map((f) => ({ name: f.name, size: f.size, type: f.type }));
      setAttachedFiles((prev) => [...prev, ...files]);
      e.target.value = "";
    }
  };
  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  const handleSendMessage = createCopilotMessageSender({
    input: inputMessage, files: attachedFiles, loading, scope, profile: demoProfile,
    currentProfile: () => profileRef.current,
    append: message => setMessages(prev => [...prev, message]),
    clearInput: () => { setInputMessage(""); setAttachedFiles([]); if (textareaRef.current) textareaRef.current.style.height = "auto"; },
    selectMode, selectFeature: next => { setFeature(next); setActiveMode("chat"); }, sendRequest,
  });
  const starterCards: StarterCard[] = [
    { title: "Financial Health Snapshot", description: "Revenue, COGS, Gross Margin & Cash Balance", query: "Summary of financial health snapshot", inspectorTab: "financial_health", tag: "AI001" },
    { title: "30-Day Cash Forecast", description: "Daily balance trajectory & Liquidity runway", query: "Project 30-day cash forecast", inspectorTab: "cash_forecast", tag: "AI002" },
    { title: "Risk Signals & Overdue AR", description: "Overdue debt ratios & Supplier payment cluster", query: "Check risk signals and overdue AR", inspectorTab: "risk_signals", tag: "AI003" },
    { title: "What-If Stress-Testing", description: "Revenue shocks & Collection delay multi-KPI model", query: "Run What-If stress test simulation", inspectorTab: "what_if", tag: "AI004" },
  ];
  return (
    <div className={`flex flex-col h-full bg-[#F8FAFC] relative overflow-hidden font-satoshi ${className}`}>
      <ChatHeaderBar company={company} activeMode={activeMode} onSelectMode={selectMode} onClearChat={() => { resetRequest(); setMessages([]); setFeature(null); setTaskDraft(""); }} onOpenInspector={onOpenInspector} onClose={onClose} onExpand={onExpand} onToggleSidebar={onToggleSidebar} isSidebarOpen={isSidebarOpen} />
      <div className="flex flex-wrap gap-2 p-2 border-b text-xs shrink-0" aria-label="Integrated capabilities">
        <button aria-label="Select CORE globally" aria-pressed={demoProfile === "CORE"} onClick={() => setDemoProfile("CORE")} className="border rounded p-1">CORE</button>
        <button aria-label="Select DEMO globally" aria-pressed={demoProfile === "DEMO"} onClick={() => setDemoProfile("DEMO")} className="border rounded p-1">DEMO — Fictional</button>
        {(["L4", "L5", "V1"] as const).map(name => <button key={name} disabled={scope.state !== "VERIFIED"} onClick={() => { setFeature(name); setActiveMode("chat"); }} className="border rounded p-1">{name} · {scope.state !== "VERIFIED" ? "AWAITING_PERMISSION" : demoProfile === "DEMO" ? "DEMO_ONLY" : name === "L5" ? "DISABLED" : "AWAITING_DATA"}</button>)}
        <span>L0 READY · L3 {scope.state === "VERIFIED" ? "READY" : "AWAITING_PERMISSION"} · L1/L2 {scope.state !== "VERIFIED" ? "AWAITING_PERMISSION" : demoProfile === "DEMO" ? "DEMO_ONLY" : "AWAITING_DATA"}</span>
      </div>
      {feature && scope.state === "VERIFIED" && <IntegratedCapabilities key={`${scope.actor}:${scope.sessionEpoch}:${scope.generation}:${demoProfile}:${feature}`} profile={demoProfile} feature={feature} draft={taskDraft} />}
      {activeMode === "chat" && !feature && (
        <>
          <ChatMessageStream company={company} messages={messages} loading={loading} copiedId={copiedId} onCopyText={copyToClipboard} starterCards={starterCards} messagesEndRef={messagesEndRef} />
          <ChatInputComposer inputMessage={inputMessage} onInputChange={handleInputChange} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }} onSendMessage={() => handleSendMessage()} attachedFiles={attachedFiles} onRemoveAttachment={(idx) => setAttachedFiles((prev) => prev.filter((_, i) => i !== idx))} onFileSelect={handleFileSelect} loading={loading} textareaRef={textareaRef} fileInputRef={fileInputRef} />
        </>
      )}
      {activeMode === "invoices" && (
        <InvoiceActionsTabView
          company={company}
          contextKey={contextKey}
          demoProfile={demoProfile}
          demoScenario={demoScenario}
          onSetDemoProfile={setDemoProfile}
          onSetDemoScenario={setDemoScenario}
          activeInvoiceTransport={activeInvoiceTransport}
          scope={scope}
          onPrepareFollowup={invoiceId => { setSelectedInvoice(invoiceId); selectMode("followup"); }}
        />
      )}
      {activeMode === "followup" && (
        <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4 max-w-4xl mx-auto w-full">
          <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
            <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900 text-xs flex items-start gap-2">
              <span className="text-base" aria-hidden="true">🛡️</span>
              <div>
                <div className="font-semibold uppercase tracking-wide text-emerald-800">L3 LOCAL PREVIEW (UNSAVED / UNSENT DRAFT)</div>
                <div className="text-emerald-700 mt-0.5">Prepare → Review → Edit → Copy → Discard lifecycle. Protected by monotonic 10-minute TTL countdown. Zero network transmission.</div>
              </div>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl p-4 sm:p-5 shadow-xs">
            {selectedInvoice && <p className="text-xs mb-2">Hóa đơn đã chọn: {selectedInvoice}. Bản nháp không tự chèn số liệu tài chính.</p>}
            <FollowupPreview
              key={`${scope.actor}:${scope.sessionEpoch}:${demoProfile}`}
              onPrepareTask={body => { setTaskDraft(body); setFeature("L4"); setActiveMode("chat"); }}
              scopeEpoch={
                scope.state === "VERIFIED"
                  ? `${scope.actor ?? "actor"}:${scope.sessionEpoch}:${company || "lotus-fin-default"}:${demoProfile}`
                  : ""
              }
            />
          </div>
        </div>
      )}
    </div>
  );
};
export default VercelChatPanel;
