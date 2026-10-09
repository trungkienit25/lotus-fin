import React from "react";

type BadgeVariant = "light" | "solid";
type BadgeSize = "sm" | "md";
type BadgeColor =
  | "primary"
  | "success"
  | "error"
  | "warning"
  | "info"
  | "light"
  | "dark"
  | "accent"
  | "mint";

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  color?: BadgeColor;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  variant = "light",
  color = "primary",
  size = "sm",
  startIcon,
  endIcon,
  children,
  className = "",
}) => {
  const baseStyles =
    "inline-flex items-center justify-center gap-1 rounded-full font-medium select-none";

  const sizeStyles = {
    sm: "px-2.5 py-0.5 text-[11px]",
    md: "px-3 py-1 text-xs",
  };

  const variants: Record<BadgeVariant, Record<BadgeColor, string>> = {
    light: {
      primary: "bg-brand-50 text-brand-600 border border-brand-100",
      success: "bg-emerald-50 text-lotus-mint border border-emerald-100",
      error: "bg-rose-50 text-rose-600 border border-rose-100",
      warning: "bg-amber-50 text-amber-700 border border-amber-100",
      info: "bg-sky-50 text-sky-700 border border-sky-100",
      light: "bg-gray-100 text-gray-700 border border-gray-200",
      dark: "bg-gray-800 text-gray-200",
      accent: "bg-[#FFDDE7] text-[#c73b64] border border-[#ffc4d6]",
      mint: "bg-[#e6f7f4] text-lotus-mint border border-[#bceae1]",
    },
    solid: {
      primary: "bg-brand-500 text-white shadow-theme-xs",
      success: "bg-lotus-mint text-white shadow-theme-xs",
      error: "bg-rose-600 text-white shadow-theme-xs",
      warning: "bg-amber-500 text-white shadow-theme-xs",
      info: "bg-sky-600 text-white shadow-theme-xs",
      light: "bg-gray-200 text-gray-700",
      dark: "bg-gray-800 text-white",
      accent: "bg-lotus-pink text-white shadow-theme-xs",
      mint: "bg-lotus-mint text-white shadow-theme-xs",
    },
  };

  const sizeClass = sizeStyles[size];
  const colorStyles = variants[variant][color] || variants.light.primary;

  return (
    <span className={`${baseStyles} ${sizeClass} ${colorStyles} ${className}`}>
      {startIcon && <span className="flex items-center">{startIcon}</span>}
      {children}
      {endIcon && <span className="flex items-center">{endIcon}</span>}
    </span>
  );
};

export default Badge;
