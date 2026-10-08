import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export type ViewMode = "List View" | "Report View" | "Kanban View";

interface ListToolbarProps {
  pageTitle: string;
  doctype: string;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onRefresh: () => void;
  loading: boolean;
  onExportCsv: () => void;
  onSelectPresetFilter: (preset: string) => void;
  activePreset: string;
}

export const TailAdminListToolbar: React.FC<ListToolbarProps> = ({
  pageTitle,
  doctype,
  viewMode,
  onViewModeChange,
  onRefresh,
  loading,
  onExportCsv,
  onSelectPresetFilter,
  activePreset,
}) => {
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [showViewDropdown, setShowViewDropdown] = useState(false);
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);

  const menuRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<HTMLDivElement>(null);
  const filterRef = useRef<HTMLDivElement>(null);

  // Đóng dropdown khi click ra ngoài
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
      if (viewRef.current && !viewRef.current.contains(e.target as Node)) {
        setShowViewDropdown(false);
      }
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setShowFilterDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const presetFilters = [
    { label: "All", value: "" },
    { label: "Draft", value: "Draft" },
    { label: "Submitted", value: "Submitted" },
    { label: "Paid", value: "Paid" },
    { label: "Overdue", value: "Overdue" },
    { label: "Cancelled", value: "Cancelled" },
  ];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      {/* Left: Back Button + Title + DocType Tag */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-800 shadow-theme-xs hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-white transition-colors"
          title="Go Back"
        >
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
              {pageTitle}
            </h1>
            {pageTitle !== doctype && (
              <span className="rounded bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                {doctype}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Manage and view all {pageTitle} records in the system
          </p>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex flex-wrap items-center gap-2">
        {/* 1. View Mode Switcher Dropdown */}
        <div className="relative" ref={viewRef}>
          <button
            onClick={() => setShowViewDropdown((p) => !p)}
            className="inline-flex h-8.5 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span>{viewMode}</span>
            <svg className="size-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {showViewDropdown && (
            <div className="absolute right-0 z-40 mt-1 w-40 rounded-xl border border-gray-100 bg-white p-1.5 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900 animate-in fade-in duration-100">
              <button
                onClick={() => {
                  onViewModeChange("List View");
                  setShowViewDropdown(false);
                }}
                className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
                  viewMode === "List View"
                    ? "bg-brand-50 text-brand-500 dark:bg-brand-500/10"
                    : "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                <span>☰</span>
                <span>List View</span>
              </button>
              <button
                onClick={() => {
                  navigate(`/report/${encodeURIComponent(doctype)}`);
                  setShowViewDropdown(false);
                }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
              >
                <span>📊</span>
                <span>Report View</span>
              </button>
            </div>
          )}
        </div>

        {/* 2. Saved / Preset Filters Dropdown */}
        <div className="relative" ref={filterRef}>
          <button
            onClick={() => setShowFilterDropdown((p) => !p)}
            className="inline-flex h-8.5 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            <span>Preset Filters</span>
            {activePreset && (
              <span className="rounded bg-brand-50 px-1.5 py-0.2 text-[10px] font-semibold text-brand-600 dark:bg-brand-500/20 dark:text-brand-400">
                {activePreset}
              </span>
            )}
            <svg className="size-3 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {showFilterDropdown && (
            <div className="absolute right-0 z-40 mt-1 w-48 rounded-xl border border-gray-100 bg-white p-1.5 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900 animate-in fade-in duration-100">
              <div className="px-2 py-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                Common Statuses
              </div>
              {presetFilters.map((p) => (
                <button
                  key={p.value}
                  onClick={() => {
                    onSelectPresetFilter(p.value);
                    setShowFilterDropdown(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    activePreset === p.value
                      ? "bg-brand-50 text-brand-500 dark:bg-brand-500/10"
                      : "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  }`}
                >
                  <span>{p.label}</span>
                  {activePreset === p.value && <span>✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 3. Refresh Button */}
        <button
          onClick={onRefresh}
          title="Reload List"
          className="flex h-8.5 w-8.5 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          <svg
            className={`size-3.5 fill-current ${loading ? "animate-spin text-brand-500" : ""}`}
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        {/* 4. Menu Actions "..." Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu((p) => !p)}
            title="More Actions"
            className="flex h-8.5 w-8.5 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
          </button>

          {showMenu && (
            <div className="absolute right-0 z-40 mt-1 w-44 rounded-xl border border-gray-100 bg-white p-1.5 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900 animate-in fade-in duration-100">
              <button
                onClick={() => {
                  onExportCsv();
                  setShowMenu(false);
                }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
              >
                <svg className="size-3.5 fill-current text-gray-400" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>Export CSV</span>
              </button>

              <button
                onClick={() => {
                  window.print();
                  setShowMenu(false);
                }}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
              >
                <svg className="size-3.5 fill-current text-gray-400" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>Print List</span>
              </button>
            </div>
          )}
        </div>

        {/* 5. Primary CTA "+ Add DocType" */}
        <button
          onClick={() => navigate(`/app/${encodeURIComponent(doctype || "")}/new`)}
          className="inline-flex h-8.5 items-center justify-center gap-1.5 rounded-lg bg-brand-500 px-3.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 dark:bg-brand-500 dark:hover:bg-brand-600 transition-colors"
        >
          <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          <span>+ Add {pageTitle}</span>
        </button>
      </div>
    </div>
  );
};

