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
      {/* Floating Action Button (Lotus Brand Multi-tone Gradient with Pulse) */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex size-13 items-center justify-center rounded-2xl bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] p-2.5 text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 border-2 border-white/60 cursor-pointer group"
        title="Open Lotus Fin AI Copilot"
      >
        <span className="text-xl group-hover:rotate-12 transition-transform duration-200">✦</span>
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-200 animate-fadeIn"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Drawer Panel (Embedding modern Vercel AI Chatbot Panel) */}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-screen w-full sm:max-w-lg md:max-w-xl lg:max-w-2xl flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
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
      </aside>
    </>
  );
};

export default LotusCopilotDrawer;
