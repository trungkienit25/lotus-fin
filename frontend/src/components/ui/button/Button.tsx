import React, { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "outline" | "gradient" | "accent" | "mint";
  startIcon?: ReactNode;
  endIcon?: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit" | "reset";
}

const Button: React.FC<ButtonProps> = ({
  children,
  size = "md",
  variant = "primary",
  startIcon,
  endIcon,
  onClick,
  className = "",
  disabled = false,
  type = "button",
}) => {
  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-lg",
    md: "px-4 py-2.5 text-xs rounded-xl",
    lg: "px-5 py-3 text-sm rounded-xl",
  };

  const variantClasses = {
    primary:
      "bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] text-white shadow-theme-xs hover:opacity-95 disabled:opacity-50 active:scale-[0.98]",
    outline:
      "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300 shadow-theme-xs",
    gradient:
      "bg-lotus-primary text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98]",
    accent:
      "bg-lotus-pink text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98]",
    mint:
      "bg-lotus-mint text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98]",
  };

  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 font-semibold transition-all duration-150 ${
        sizeClasses[size]
      } ${variantClasses[variant]} ${
        disabled ? "cursor-not-allowed opacity-50 pointer-events-none" : ""
      } ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {startIcon && <span className="flex items-center">{startIcon}</span>}
      {children}
      {endIcon && <span className="flex items-center">{endIcon}</span>}
    </button>
  );
};

export default Button;
