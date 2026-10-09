import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { VercelChatPanel } from "../../pages/copilot/components/VercelChatPanel";

export const LotusCopilotDrawer: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleExpandToFullPage = () => {
    setOpen(false);
    navigate("/page/lotus-copilot");
  };

  const handleOpenInspector = (tab: string) => {
    setOpen(false);
    navigate(`/page/lotus-copilot?tab=${tab}`);
  };

  return (
    <>
      {/* Floating Messenger-style Chat Bubble Window */}
      {open && (
        <div
          className="fixed bottom-22 right-4 sm:right-6 z-50 w-[calc(100vw-32px)] sm:w-[440px] md:w-[480px] h-[640px] max-h-[calc(100vh-110px)] rounded-3xl shadow-2xl border border-gray-200/90 bg-white flex flex-col overflow-hidden transition-all duration-300 origin-bottom-right animate-in fade-in zoom-in-95"
          style={{ boxShadow: "0 20px 50px -12px rgba(15, 23, 42, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.05)" }}
        >
          <div className="flex-1 h-full overflow-hidden">
            <VercelChatPanel
              company="Lotus-fin (Demo)"
              onOpenInspector={handleOpenInspector}
              onExpand={handleExpandToFullPage}
              onClose={() => setOpen(false)}
              className="h-full"
            />
          </div>
        </div>
      )}

      {/* Floating Messenger Action Button (Bottom-Right Bubble) */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`fixed bottom-6 right-4 sm:right-6 z-50 flex size-14 items-center justify-center rounded-full text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 border-2 border-white/80 cursor-pointer group ${
          open ? "bg-slate-800 rotate-90" : "bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A]"
        }`}
        title={open ? "Close Copilot Chat" : "Open Lotus Fin AI Copilot"}
      >
        {open ? (
          <svg className="size-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <div className="flex items-center justify-center relative">
            <span className="text-2xl group-hover:rotate-12 transition-transform duration-200">✦</span>
            <span className="absolute -top-1 -right-1 size-3 rounded-full bg-emerald-400 border-2 border-white animate-pulse"></span>
          </div>
        )}
      </button>
    </>
  );
};

export default LotusCopilotDrawer;
