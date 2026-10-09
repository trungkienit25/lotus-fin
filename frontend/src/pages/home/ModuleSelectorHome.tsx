import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useTranslation } from "../../i18n";
import { formatBrandText } from "../../utils/brand";

interface WorkspaceMeta {
  name: string;
  title: string;
  icon?: string;
  module?: string;
}

// Map corresponding icons and rich brand gradients for each Workspace module (Lotus Fin Brand Guideline)
const getModuleBadgeConfig = (name: string) => {
  const n = name.toLowerCase();

  // 1. Lotus Fin AI — Special Multi-tone Lotus Blossom Gradient
  if (n.includes("ai") || n.includes("copilot") || n.includes("lotus fin ai")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#FF8FB1]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
      ),
    };
  }

  // 2. Financial Reports — Key Visual Gradient (Deep Blue -> Light Blue -> Mint Green)
  if (n.includes("financial report") || n.includes("financial")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      ),
    };
  }

  // 3. Invoicing / Accounting — Deep Blue to Light Blue Gradient
  if (n.includes("invoicing") || n.includes("account")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#6EC1F6]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <line x1="12" y1="8" x2="12" y2="16" />
          <line x1="8" y1="12" x2="16" y2="12" />
        </svg>
      ),
    };
  }

  // 4. Selling / CRM — Teal to Mint Green Gradient
  if (n.includes("selling") || n.includes("crm")) {
    return {
      bg: "bg-gradient-to-br from-[#39C6B7] to-[#2FB29A]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 0 1-8 0" />
        </svg>
      ),
    };
  }

  // 5. Buying — Deep Blue to Teal Gradient
  if (n.includes("buying")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#39C6B7]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
          <line x1="7" y1="7" x2="7.01" y2="7" />
        </svg>
      ),
    };
  }

  // 6. Stock / Assets — Light Blue to Mint Gradient
  if (n.includes("stock") || n.includes("asset")) {
    return {
      bg: "bg-gradient-to-br from-[#6EC1F6] to-[#2FB29A]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
      ),
    };
  }

  // 7. Projects — Navy to Deep Blue Gradient
  if (n.includes("project")) {
    return {
      bg: "bg-gradient-to-br from-[#143f79] to-[#1E63B7]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      ),
    };
  }

  // 8. Quality — Mint to Light Blue Gradient
  if (n.includes("quality")) {
    return {
      bg: "bg-gradient-to-br from-[#2FB29A] to-[#6EC1F6]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <polyline points="9 12 11 14 15 10" />
        </svg>
      ),
    };
  }

  // 9. Users / HR / Organization — Deep Blue to Light Blue Gradient
  if (n.includes("user") || n.includes("hr") || n.includes("organ")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#6EC1F6]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
    };
  }

  // 10. Manufacturing — Deep Blue to Sky Gradient
  if (n.includes("manufactur")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#38acf7]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 20h20" />
          <path d="M6 20V10l6 4V10l6 4v6" />
        </svg>
      ),
    };
  }

  // 11. Subcontracting — Teal to Mint Gradient
  if (n.includes("subcontract")) {
    return {
      bg: "bg-gradient-to-br from-[#39C6B7] to-[#2FB29A]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
        </svg>
      ),
    };
  }

  // 12. Build / Framework — Sleek Dark Charcoal Slate Gradient
  if (n.includes("build") || n.includes("framework")) {
    return {
      bg: "bg-gradient-to-br from-[#344054] to-[#1d2939]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" />
          <rect x="14" y="3" width="7" height="7" />
          <rect x="14" y="14" width="7" height="7" />
          <rect x="3" y="14" width="7" height="7" />
        </svg>
      ),
    };
  }

  // 13. Settings — Slate Gradient
  if (n.includes("setting")) {
    return {
      bg: "bg-gradient-to-br from-[#475467] to-[#1d2939]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      ),
    };
  }

  // 14. Support / Website / Integrations
  if (n.includes("support") || n.includes("website") || n.includes("integrat")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#39C6B7]",
      svg: (
        <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18" />
          <path d="M9 21V9" />
        </svg>
      ),
    };
  }

  // Default Fallback
  return {
    bg: "bg-gradient-to-br from-[#1E63B7] to-[#6EC1F6]",
    svg: (
      <svg className="size-7 text-white drop-shadow-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M3 9h18" />
        <path d="M9 21V9" />
      </svg>
    ),
  };
};

export const ModuleSelectorHome: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState<WorkspaceMeta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/resource/Workspace?limit_page_length=50")
      .then((res) => {
        const list: WorkspaceMeta[] = res.data?.data || [];
        const filtered = list.filter(
          (w) => !["Home", "Welcome Workspace"].includes(w.name)
        );
        setWorkspaces(filtered);
      })
      .catch((err) => {
        console.error("Error loading Workspaces:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3">
        <svg className="size-8 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-xs font-medium text-gray-500">{t("common.loading")}...</span>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl py-8 sm:py-12 px-4">
      {/* Module Grid (Lotus Fin Brand Gradients) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6 sm:gap-8">
        {workspaces.map((ws) => {
          const config = getModuleBadgeConfig(ws.name);
          const isAi = ws.name.toLowerCase().includes("ai") || ws.name.toLowerCase().includes("copilot");
          const targetUrl = isAi ? "/ai" : `/workspace/${encodeURIComponent(ws.name)}`;

          return (
            <div
              key={ws.name}
              onClick={() => navigate(targetUrl)}
              className="group flex flex-col items-center text-center cursor-pointer transition-transform duration-200 hover:-translate-y-1.5 active:scale-95"
            >
              {/* Vibrant Gradient App Icon Square */}
              <div
                className={`flex size-16 sm:size-18 items-center justify-center rounded-2xl ${config.bg} shadow-md shadow-gray-200/80 group-hover:shadow-lg group-hover:shadow-gray-300/80 transition-all duration-200`}
              >
                {config.svg}
              </div>

              {/* App Label */}
              <span className="mt-3 text-xs sm:text-sm font-semibold text-[#2E3A59] group-hover:text-[#1E63B7] transition-colors line-clamp-1">
                {formatBrandText(ws.title || ws.name)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
