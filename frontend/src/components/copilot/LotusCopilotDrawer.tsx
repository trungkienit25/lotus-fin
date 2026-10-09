import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "../../i18n";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  toolCalls?: string[];
  widget?: any;
}

const QUICK_PROMPTS = [
  "Dự báo dòng tiền 30 ngày",
  "Khách nợ quá hạn >30 ngày",
  "Tồn kho dưới an toàn",
];

export const LotusCopilotDrawer: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init-1",
      sender: "assistant",
      content: "Xin chào! Tôi là Lotus Fin AI. Bạn cần phân tích dòng tiền, đối soát công nợ hay kiểm tra dữ liệu gì hôm nay?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open]);

  const handleSendMessage = async (customText?: string) => {
    const text = (customText || inputMessage).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setInputMessage("");
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await axios.post("/api/method/lotus_fin.presentation.controller.copilot_controller.handle_send_message", {
        message: text,
      });

      const responseData = res.data?.message;
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: "assistant",
          content: responseData?.reply || "Đã xử lý tác vụ thành công.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          toolCalls: responseData?.executed_tools,
          widget: responseData?.ui_widget,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          content: `Lỗi kết nối Lotus AI: ${err.response?.data?.message || err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExpandToFullPage = () => {
    setOpen(false);
    navigate("/ai");
  };

  return (
    <>
      {/* Floating Action Button (Lotus Brand Multi-tone Gradient with Pulse) */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] p-2.5 text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 border-2 border-white/40"
        title="Lotus Fin AI Copilot"
      >
        <img src="/brand/favicon.jpg" alt="Lotus AI" className="size-8 rounded-xl object-contain bg-white/20 p-0.5" />
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-50 bg-gray-900/40 backdrop-blur-xs transition-opacity duration-200 animate-in fade-in"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Drawer Panel (Vercel Style Mini Copilot) */}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-screen w-full max-w-md flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out dark:bg-gray-900 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Drawer Header (Lotus Primary Gradient) */}
        <div className="flex h-16 items-center justify-between border-b border-gray-100 bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] px-5 text-white">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-xl bg-white/20 p-1 backdrop-blur-xs">
              <img src="/brand/favicon.jpg" alt="Lotus Copilot" className="size-7 rounded-lg object-contain" />
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">Lotus Fin AI</h3>
              <p className="text-[10px] text-white/80 font-medium">Trợ lý tài chính & ERP</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Expand to Full Page Button */}
            <button
              type="button"
              onClick={handleExpandToFullPage}
              title="Mở toàn màn hình"
              className="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
            >
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>

            {/* Close Button */}
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="flex size-8 items-center justify-center rounded-lg bg-white/10 text-white hover:bg-white/20 transition-colors"
            >
              <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        {/* Quick Suggestion Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto p-3 border-b border-gray-100 dark:border-gray-800 bg-gray-50/70 no-scrollbar">
          {QUICK_PROMPTS.map((qp, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(qp)}
              className="shrink-0 rounded-full border border-gray-200 bg-white px-2.5 py-1 text-[11px] font-medium text-gray-700 hover:border-[#1E63B7] hover:text-[#1E63B7] hover:bg-[#E8F2FB] transition-all shadow-theme-xs"
            >
              {qp}
            </button>
          ))}
        </div>

        {/* Messages List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#F8FAFC] dark:bg-gray-950">
          {messages.map((item) => (
            <div
              key={item.id}
              className={`flex flex-col ${
                item.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[88%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-theme-xs ${
                  item.sender === "user"
                    ? "bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] text-white font-medium rounded-br-xs"
                    : "bg-white text-[#2E3A59] border border-gray-200 rounded-bl-xs dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100"
                }`}
              >
                <div className="whitespace-pre-wrap">{item.content}</div>

                {item.toolCalls && item.toolCalls.length > 0 && (
                  <div className="mt-2.5 border-t border-gray-100 dark:border-gray-700 pt-2 text-[10px]">
                    <span className="font-semibold text-gray-400 block mb-1">
                      Công cụ đã gọi:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {item.toolCalls.map((tc) => (
                        <span
                          key={tc}
                          className="rounded bg-[#E8F2FB] px-1.5 py-0.5 font-mono text-[#1E63B7] border border-[#1E63B7]/20"
                        >
                          {tc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span className="mt-1 px-1 text-[9px] text-gray-400">{item.timestamp}</span>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-gray-400 p-2 animate-in fade-in">
              <svg className="size-4 animate-spin text-[#1E63B7]" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>AI đang truy vấn sổ cái & tính toán...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area (2px Gradient Glow) */}
        <div className="border-t border-gray-200 bg-white p-3.5 dark:border-gray-800 dark:bg-gray-900">
          <div className="p-[1.5px] rounded-xl bg-gray-200 focus-within:bg-gradient-to-r focus-within:from-[#1E63B7] focus-within:via-[#6EC1F6] focus-within:to-[#2FB29A] transition-all">
            <div className="flex items-center gap-2 rounded-[10px] bg-gray-50/90 focus-within:bg-white p-1.5 dark:bg-gray-800">
              <input
                type="text"
                placeholder="Nhập câu hỏi tài chính..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={loading}
                className="h-9 flex-1 bg-transparent px-2 text-xs text-gray-900 placeholder:text-gray-400 focus:outline-none dark:text-white"
              />

              <button
                type="button"
                onClick={() => handleSendMessage()}
                disabled={loading || !inputMessage.trim()}
                className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-r from-[#1E63B7] to-[#2FB29A] text-white shadow-theme-xs hover:opacity-95 disabled:opacity-40 transition active:scale-95 shrink-0"
              >
                <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
