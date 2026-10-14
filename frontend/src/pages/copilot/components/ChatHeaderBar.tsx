import React from "react";
import type { ChatPanelMode } from "./VercelChatPanelTypes";

interface ChatHeaderBarProps {
  company: string;
  activeMode: ChatPanelMode;
  onSelectMode: (mode: ChatPanelMode) => void;
  onClearChat: () => void;
  onOpenInspector?: (tab: string) => void;
  onClose?: () => void;
  onExpand?: () => void;
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const ChatHeaderBar: React.FC<ChatHeaderBarProps> = ({
  company,
  activeMode,
  onSelectMode,
  onClearChat,
  onOpenInspector,
  onClose,
  onExpand,
  onToggleSidebar,
  isSidebarOpen,
}) => {
  return (
    <div className="flex items-center justify-between px-3 sm:px-5 py-2.5 border-b border-gray-200 bg-white/95 backdrop-blur sticky top-0 z-10 shrink-0 gap-2">
      <div className="flex items-center gap-2 min-w-0">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="p-1.5 -ml-1 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
            title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            aria-label={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          </button>
        )}
        <div
          className="size-7 rounded-lg flex items-center justify-center text-white font-bold text-xs shadow-xs shrink-0"
          style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
          aria-hidden="true"
        >
          ✦
        </div>
        <div className="min-w-0">
          <div className="font-bold text-gray-900 text-xs sm:text-sm truncate">Lotus Fin AI</div>
          <div className="text-[10px] text-gray-400 truncate">
            Scope: <span className="font-semibold text-gray-600">{company || "Core"}</span>
          </div>
        </div>
      </div>

      {/* Mode switcher tabs with accessible roles and labels */}
      <div className="flex items-center gap-1 bg-gray-100 p-0.5 rounded-xl border border-gray-200 shrink-0" role="tablist" aria-label="Copilot modes">
        <button
          type="button"
          role="tab"
          aria-selected={activeMode === "chat"}
          aria-label="Chat mode"
          onClick={() => onSelectMode("chat")}
          className={`px-2 sm:px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeMode === "chat" ? "bg-white text-blue-700 shadow-xs" : "text-gray-500 hover:text-gray-900"
          }`}
        >
          Chat
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeMode === "invoices"}
          aria-label="Invoice Actions mode"
          onClick={() => onSelectMode("invoices")}
          className={`px-2 sm:px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeMode === "invoices" ? "bg-white text-blue-700 shadow-xs" : "text-gray-500 hover:text-gray-900"
          }`}
        >
          Invoice Actions
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeMode === "followup"}
          aria-label="Followup L3 mode"
          onClick={() => onSelectMode("followup")}
          className={`px-2 sm:px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
            activeMode === "followup" ? "bg-white text-blue-700 shadow-xs" : "text-gray-500 hover:text-gray-900"
          }`}
        >
          Followup (L3)
        </button>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        {onOpenInspector && (
          <button
            type="button"
            disabled={true}
            className="px-2 py-1 rounded-lg border border-gray-200 bg-gray-100 text-gray-400 text-[11px] font-semibold flex items-center gap-1 cursor-not-allowed shadow-2xs opacity-60"
            title="Reports unavailable under unqualified observation context"
            aria-label="Reports unavailable"
          >
            <svg className="size-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span className="hidden sm:inline">Reports</span>
            <span className="text-[10px]">↗</span>
          </button>
        )}

        <button
          type="button"
          onClick={onClearChat}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
          title="Reset conversation"
          aria-label="Reset conversation"
        >
          <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        {onExpand && (
          <button
            type="button"
            onClick={onExpand}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
            title="Expand to Full Copilot Page"
            aria-label="Expand to Full Copilot Page"
          >
            <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
            </svg>
          </button>
        )}

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
            title="Close panel"
            aria-label="Close panel"
          >
            <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
