import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

interface RefineLinkControlProps {
  targetDocType: string;
  value?: string;
  onChange?: (val: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const RefineLinkControl: React.FC<RefineLinkControlProps> = ({
  targetDocType,
  value,
  onChange,
  disabled,
  placeholder,
}) => {
  const [options, setOptions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!targetDocType) return;
    setLoading(true);
    axios
      .get(`/api/resource/${encodeURIComponent(targetDocType)}?limit_page_length=50&fields=["name"]`)
      .then((res) => {
        const list = (res.data?.data || []).map((d: any) => d.name);
        setOptions(list);
      })
      .catch(() => {
        setOptions([]);
      })
      .finally(() => setLoading(false));
  }, [targetDocType]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter((opt) =>
    opt.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="relative" ref={containerRef}>
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`flex h-10 w-full items-center justify-between rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus-within:border-brand-500 focus-within:bg-white dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
          disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
        }`}
      >
        <span className={value ? "text-gray-900 dark:text-white font-medium truncate" : "text-gray-400"}>
          {value || placeholder || `Select ${targetDocType}...`}
        </span>

        <div className="flex items-center gap-1">
          {value && !disabled && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChange?.("");
              }}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          )}
          <svg className="size-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {isOpen && !disabled && (
        <div className="absolute left-0 top-full z-50 mt-1 w-full rounded-xl border border-gray-200 bg-white p-2 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark animate-in fade-in duration-100">
          <input
            type="text"
            placeholder="Search options..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-2 h-8 w-full rounded-md border border-gray-200 bg-gray-50 px-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            autoFocus
          />

          <div className="max-h-48 overflow-y-auto space-y-0.5">
            {loading ? (
              <div className="px-3 py-2 text-xs text-gray-400 text-center">Loading...</div>
            ) : filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-xs text-gray-400 text-center">No matching records</div>
            ) : (
              filteredOptions.map((opt) => (
                <div
                  key={opt}
                  onClick={() => {
                    onChange?.(opt);
                    setIsOpen(false);
                    setSearchTerm("");
                  }}
                  className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium cursor-pointer transition-colors ${
                    value === opt
                      ? "bg-[#E8F2FB] text-[#1E63B7] font-semibold"
                      : "text-gray-700 hover:bg-[#E8F2FB] hover:text-[#1E63B7]"
                  }`}
                >
                  <span className="truncate">{opt}</span>
                  {value === opt && <span className="text-[#1E63B7] font-bold">✓</span>}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

