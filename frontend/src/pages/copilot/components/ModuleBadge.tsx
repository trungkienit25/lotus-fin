import React from "react";

export type AIModuleId =
  | "financial_health"
  | "health"
  | "cash_forecast"
  | "risk_signals"
  | "risk_signal"
  | "what_if"
  | "financing_copilot"
  | "financing"
  | "repayment_schedule"
  | "repayment"
  | "lotus_ai"
  | string;

export interface ModuleBadgeConfig {
  bg: string;
  icon: React.ReactNode;
  label: string;
  code: string;
}

export const getAIModuleBadgeConfig = (id: string): ModuleBadgeConfig => {
  const normalized = (id || "").toLowerCase().replace(/[-_]/g, "");

  // 1. AI001 — Financial Health Snapshot (Key Visual Gradient: Deep Blue -> Light Blue -> Mint Green)
  if (normalized.includes("health") || normalized.includes("ai001") || normalized.includes("snapshot")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A]",
      code: "AI001",
      label: "Financial Health",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      ),
    };
  }

  // 2. AI002 — 30-Day Cash Forecast (Deep Blue -> Light Blue Gradient)
  if (normalized.includes("cash") || normalized.includes("forecast") || normalized.includes("ai002")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#6EC1F6]",
      code: "AI002",
      label: "30-Day Cash Forecast",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
        </svg>
      ),
    };
  }

  // 3. AI003 — Risk Signals & Overdue AR (Pink Accent -> Rose Coral Gradient)
  if (normalized.includes("risk") || normalized.includes("signal") || normalized.includes("ai003") || normalized.includes("overdue")) {
    return {
      bg: "bg-gradient-to-br from-[#FF8FB1] via-[#F43F5E] to-[#E11D48]",
      code: "AI003",
      label: "Risk Signals",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      ),
    };
  }

  // 4. AI004 — Stress-Testing Studio / What-If (Indigo -> Purple Gradient)
  if (normalized.includes("whatif") || normalized.includes("stress") || normalized.includes("ai004") || normalized.includes("scenario")) {
    return {
      bg: "bg-gradient-to-br from-[#6366F1] to-[#8B5CF6]",
      code: "AI004",
      label: "Stress-Testing Studio",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
      ),
    };
  }

  // 5. AI005 — Loan Matchmaker / Financing Copilot (Teal -> Mint Green Gradient)
  if (normalized.includes("financ") || normalized.includes("loan") || normalized.includes("ai005") || normalized.includes("credit")) {
    return {
      bg: "bg-gradient-to-br from-[#39C6B7] to-[#2FB29A]",
      code: "AI005",
      label: "Loan Matchmaker",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="5" width="20" height="14" rx="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
      ),
    };
  }

  // 6. AI006 — Repayment Schedule / PMT Amortization (Deep Blue -> Teal Gradient)
  if (normalized.includes("repay") || normalized.includes("pmt") || normalized.includes("schedule") || normalized.includes("ai006")) {
    return {
      bg: "bg-gradient-to-br from-[#1E63B7] to-[#39C6B7]",
      code: "AI006",
      label: "Repayment Schedule",
      icon: (
        <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      ),
    };
  }

  // Default: Lotus Fin AI Core Sparkle Gradient
  return {
    bg: "bg-gradient-to-br from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A]",
    code: "AI",
    label: "Lotus Fin AI",
    icon: (
      <svg className="w-full h-full block shrink-0 text-white drop-shadow-2xs" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z" />
      </svg>
    ),
  };
};

export interface ModuleBadgeProps {
  moduleId: string;
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

export const ModuleBadge: React.FC<ModuleBadgeProps> = ({ moduleId, size = "sm", className = "" }) => {
  const config = getAIModuleBadgeConfig(moduleId);

  const sizeClasses = {
    xs: "w-4 h-4 min-w-[16px] min-h-[16px] max-w-[16px] max-h-[16px] p-0.5 rounded",
    sm: "w-6 h-6 min-w-[24px] min-h-[24px] max-w-[24px] max-h-[24px] p-1 rounded-lg",
    md: "w-8 h-8 min-w-[32px] min-h-[32px] max-w-[32px] max-h-[32px] p-1.5 rounded-xl shadow-xs",
    lg: "w-10 h-10 min-w-[40px] min-h-[40px] max-w-[40px] max-h-[40px] p-2 rounded-xl shadow-md shadow-blue-500/10",
  }[size];

  return (
    <span
      className={`inline-flex items-center justify-center shrink-0 overflow-hidden text-white ${config.bg} ${sizeClasses} ${className}`}
      title={`${config.code}: ${config.label}`}
      style={{
        width: size === "xs" ? 16 : size === "sm" ? 24 : size === "md" ? 32 : 40,
        height: size === "xs" ? 16 : size === "sm" ? 24 : size === "md" ? 32 : 40,
      }}
    >
      {config.icon}
    </span>
  );
};

export default ModuleBadge;
