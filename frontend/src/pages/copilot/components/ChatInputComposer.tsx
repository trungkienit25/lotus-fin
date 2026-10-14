import React from "react";
import type { AttachedFile } from "./VercelChatPanelTypes";

interface ChatInputComposerProps {
  inputMessage: string;
  onInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: () => void;
  attachedFiles: AttachedFile[];
  onRemoveAttachment: (index: number) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  loading: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export const ChatInputComposer: React.FC<ChatInputComposerProps> = ({
  inputMessage,
  onInputChange,
  onKeyDown,
  onSendMessage,
  attachedFiles,
  onRemoveAttachment,
  onFileSelect,
  loading,
  textareaRef,
  fileInputRef,
}) => {
  const canSend = (inputMessage.trim().length > 0 || attachedFiles.length > 0) && !loading;

  return (
    <div className="absolute bottom-0 left-0 right-0 pointer-events-none p-2 sm:p-3 bg-gradient-to-t from-[#F8FAFC] via-[#F8FAFC]/95 to-transparent z-10">
      <div className="max-w-3xl mx-auto pointer-events-auto w-full">
        {/* Quick suggestions pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 mb-1">
          {["Financial Health", "Cash Forecast 30D", "Risk Signals", "What-If Studio"].map((pill, i) => (
            <button
              key={i}
              type="button"
              disabled={true}
              title="Unavailable under unqualified observation context"
              className="whitespace-nowrap px-2.5 py-0.5 rounded-full bg-gray-100/90 border border-gray-200 text-gray-400 font-medium cursor-not-allowed text-[10px]"
            >
              {pill}
            </button>
          ))}
        </div>

        {/* Vercel Input Box Card */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-md shadow-gray-200/50 p-2 focus-within:border-[#1E63B7] focus-within:ring-2 focus-within:ring-[#1E63B7]/10 transition-all">
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-1.5 pb-1.5 border-b border-gray-100 px-1">
              {attachedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-[10px] font-medium shadow-2xs">
                  <span>📄</span>
                  <span className="truncate max-w-[140px]">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => onRemoveAttachment(idx)}
                    className="text-blue-400 hover:text-rose-600 ml-1 font-bold cursor-pointer"
                    title={`Remove ${file.name}`}
                    aria-label={`Remove file ${file.name}`}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <textarea
            ref={textareaRef}
            rows={1}
            value={inputMessage}
            onChange={onInputChange}
            onKeyDown={onKeyDown}
            placeholder="Ask anything about invoices, followup drafts, metrics..."
            aria-label="Message prompt input"
            className="w-full resize-none border-0 bg-transparent text-xs text-gray-800 placeholder-gray-400 focus:outline-hidden focus:ring-0 px-1 py-0.5 min-h-[32px] max-h-[120px]"
          />

          <div className="flex items-center justify-between pt-1.5 border-t border-gray-100 px-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <input
                type="file"
                ref={fileInputRef}
                multiple
                accept=".csv,.xlsx,.xls,.pdf,.png,.jpg,.jpeg,.json"
                onChange={onFileSelect}
                aria-label="Upload file attachment"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-1 rounded-lg text-gray-400 hover:text-[#1E63B7] hover:bg-[#E8F2FB] transition-colors cursor-pointer shrink-0"
                title="Attach files (CSV, Excel, PDF, Images)"
                aria-label="Attach files"
              >
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
              <span className="text-[10px] text-gray-400 hidden lg:inline truncate">
                Enter to send
              </span>
            </div>

            <button
              type="button"
              onClick={onSendMessage}
              disabled={!canSend}
              className={`size-7 rounded-lg transition-all flex items-center justify-center shrink-0 ${
                canSend
                  ? "text-white shadow-xs cursor-pointer hover:opacity-90 active:scale-95"
                  : "bg-gray-100 text-gray-300 cursor-not-allowed"
              }`}
              style={
                canSend
                  ? { background: "linear-gradient(135deg, #1E63B7 0%, #2FB29A 100%)" }
                  : undefined
              }
              title="Send message"
              aria-label="Send message"
            >
              <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
