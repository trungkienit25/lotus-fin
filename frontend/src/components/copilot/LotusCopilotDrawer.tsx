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
      {open ? (
        <div
          className="fixed bottom-5 right-4 sm:right-6 z-50 w-[calc(100vw-32px)] sm:w-[400px] md:w-[420px] h-[580px] max-h-[calc(100vh-40px)] rounded-2xl shadow-2xl border border-gray-200/90 bg-white flex flex-col overflow-hidden transition-all duration-200 origin-bottom-right animate-in fade-in zoom-in-95"
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
      ) : (
        /* Floating Action Button (Clean, compact size-12) */
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-5 right-4 sm:right-6 z-40 flex size-12 items-center justify-center rounded-full bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 border-2 border-white/80 cursor-pointer group"
          title="Open Lotus Fin AI Copilot"
        >
          <div className="flex items-center justify-center relative">
            <span className="text-xl group-hover:rotate-12 transition-transform duration-200">✦</span>
            <span className="absolute -top-1 -right-1 size-2.5 rounded-full bg-emerald-400 border-2 border-white animate-pulse"></span>
          </div>
        </button>
      )}
    </>
  );
};

export default LotusCopilotDrawer;
