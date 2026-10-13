import React from "react";
import { ModuleBadge } from "./ModuleBadge";
import { CopilotMessageBody } from "./CopilotMessageBody";
import type { ChatMessage, StarterCard } from "./VercelChatPanelTypes";

interface ChatMessageStreamProps {
  company: string;
  messages: ChatMessage[];
  loading: boolean;
  copiedId: string | null;
  onCopyText: (id: string, text: string) => void;
  starterCards: StarterCard[];
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

export const ChatMessageStream: React.FC<ChatMessageStreamProps> = ({
  company,
  messages,
  loading,
  copiedId,
  onCopyText,
  starterCards,
  messagesEndRef,
}) => {
  return (
    <div className="flex-1 overflow-y-auto px-3 sm:px-6 pt-3 pb-32 space-y-4">
      {messages.length === 0 && (
        <div className="max-w-2xl mx-auto pt-1 pb-4 flex flex-col items-center text-center">
          <div
            className="size-9 rounded-xl flex items-center justify-center text-white text-base font-bold shadow-xs mb-2"
            style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
            aria-hidden="true"
          >
            ✦
          </div>
          <h1 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight">
            How can I assist with your financial analytics today?
          </h1>
          <p className="text-[11px] text-gray-500 mt-0.5 max-w-sm">
            Lotus Fin AI assistant for <strong className="text-gray-700">{company || "Lotus Fin Core"}</strong>.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 w-full mt-3.5 text-left">
            {starterCards.map((card, idx) => (
              <button
                key={idx}
                type="button"
                disabled={true}
                title="Unavailable under unqualified observation context"
                className="px-3 py-2 rounded-xl bg-gray-50 border border-gray-200 text-gray-400 flex items-center justify-between group cursor-not-allowed text-left opacity-75"
              >
                <div className="flex items-center gap-2 min-w-0 pr-1">
                  <ModuleBadge moduleId={card.inspectorTab} size="xs" />
                  <div className="min-w-0">
                    <div className="text-[11px] font-bold text-gray-500 truncate">{card.title}</div>
                    <div className="text-[10px] text-gray-400 truncate">{card.description}</div>
                  </div>
                </div>
                <span className="text-[10px] font-bold text-gray-300 shrink-0 ml-1" aria-hidden="true">➔</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex flex-col max-w-3xl mx-auto w-full ${msg.sender === "user" ? "items-end" : "items-start"}`}
        >
          <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-gray-400">
            {msg.sender === "assistant" && (
              <div
                className="size-3.5 rounded-full flex items-center justify-center text-[9px] text-white font-bold"
                style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
                aria-hidden="true"
              >
                ✦
              </div>
            )}
            <span className="font-semibold text-gray-500">{msg.sender === "user" ? "You" : "Lotus Fin AI"}</span>
            <span>• {msg.timestamp}</span>
          </div>

          {msg.attachments && msg.attachments.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-1.5 justify-end">
              {msg.attachments.map((file, i) => (
                <div key={i} className="text-[10px] px-2 py-0.5 rounded-md bg-blue-50 border border-blue-200 text-blue-700 flex items-center gap-1">
                  <span>📄</span>
                  <span className="truncate max-w-[120px]">{file.name}</span>
                </div>
              ))}
            </div>
          )}

          <div
            className={`rounded-2xl p-3.5 text-xs sm:text-sm leading-relaxed max-w-[90%] sm:max-w-[85%] ${
              msg.sender === "user"
                ? "bg-[#1E63B7] text-white rounded-tr-xs shadow-xs"
                : "bg-white border border-gray-200 text-gray-800 rounded-tl-xs shadow-theme-xs"
            }`}
          >
            {msg.sender === "user" ? (
              <div className="whitespace-pre-wrap">{msg.content}</div>
            ) : (
              <CopilotMessageBody content={msg.content} />
            )}
          </div>

          {msg.sender === "assistant" && (
            <div className="flex items-center gap-2 mt-1 px-1 text-[10px] text-gray-400">
              {msg.sourceLabel && <span className="font-medium text-gray-500">{msg.sourceLabel}</span>}
              {msg.correlationId && <span>CID: {msg.correlationId.slice(0, 8)}...</span>}
              <button
                type="button"
                onClick={() => onCopyText(msg.id, msg.content)}
                className="hover:text-gray-600 transition-colors cursor-pointer"
                aria-label={copiedId === msg.id ? "Copied to clipboard" : "Copy response"}
              >
                {copiedId === msg.id ? "Copied!" : "Copy"}
              </button>
            </div>
          )}
        </div>
      ))}

      {loading && (
        <div className="max-w-3xl mx-auto flex flex-col items-start w-full">
          <div className="flex items-center gap-1.5 mb-1 px-1 text-[11px] text-gray-400">
            <div
              className="size-3.5 rounded-full flex items-center justify-center text-[9px] text-white font-bold"
              style={{ background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }}
              aria-hidden="true"
            >
              ✦
            </div>
            <span className="font-semibold text-gray-700">Lotus Fin AI</span>
            <span>• Processing</span>
          </div>
          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-xs p-3.5 shadow-theme-xs" role="status">
            <div className="flex items-center gap-2">
              <div className="size-2 rounded-full bg-[#1E63B7] animate-bounce" style={{ animationDelay: "0ms" }}></div>
              <div className="size-2 rounded-full bg-[#6EC1F6] animate-bounce" style={{ animationDelay: "150ms" }}></div>
              <div className="size-2 rounded-full bg-[#2FB29A] animate-bounce" style={{ animationDelay: "300ms" }}></div>
              <span className="text-xs text-gray-500 font-medium ml-1">Processing request...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};
