import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useGetIdentity, useLogout } from "@refinedev/core";
import { formatBrandText } from "../../utils/brand";

interface HeaderProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeWorkspace: string;
  searchDocType: string;
  setSearchDocType: (val: string) => void;
  onSelectDocType?: (doctype: string) => void;
  doctypes?: { name: string; module?: string }[];
}

export const TailAdminHeader: React.FC<HeaderProps> = ({
  sidebarOpen,
  setSidebarOpen,
  activeWorkspace,
  searchDocType,
  setSearchDocType,
  onSelectDocType,
  doctypes = [],
}) => {
  const { data: identity } = useGetIdentity<{ name: string; email?: string }>();
  const { mutate: logout } = useLogout();
  const location = useLocation();
  const navigate = useNavigate();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const notificationRef = useRef<HTMLDivElement>(null);

  const currentPath = decodeURIComponent(location.pathname);
  const isHomePage = currentPath === "/" || currentPath === "/home";

  // Determine current page title / breadcrumbs
  let pageTitle = "Dashboard";
  if (isHomePage) {
    pageTitle = "Desk";
  } else if (currentPath === "/ai" || currentPath === "/copilot") {
    pageTitle = "Copilot";
  } else if (currentPath.startsWith("/page/financial-health")) {
    pageTitle = "Financial Health";
  } else if (currentPath.startsWith("/page/cash-forecast")) {
    pageTitle = "Cash Forecast";
  } else if (currentPath.startsWith("/page/risk-signal")) {
    pageTitle = "Risk Signals";
  } else if (currentPath.startsWith("/page/what-if-studio")) {
    pageTitle = "What-If Studio";
  } else if (currentPath.startsWith("/page/financing-copilot")) {
    pageTitle = "Financing Copilot";
  } else if (currentPath.startsWith("/page/repayment-schedule")) {
    pageTitle = "Repayment Schedule";
  } else if (currentPath.startsWith("/app/")) {
    const raw = currentPath.replace("/app/", "");
    const parts = raw.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0] === parts[1]) {
      pageTitle = parts[0];
    } else if (parts.length >= 2) {
      pageTitle = `${parts[1]} (${parts[0]})`;
    } else {
      pageTitle = parts[0] || raw;
    }
  } else if (currentPath.startsWith("/report/")) {
    pageTitle = currentPath.replace("/report/", "").split("?")[0];
  } else if (currentPath.startsWith("/workspace/")) {
    pageTitle = activeWorkspace || "Overview";
  } else if (currentPath.startsWith("/page/")) {
    pageTitle = currentPath.replace("/page/", "").split("?")[0];
  }

  // Keyboard shortcut (Ctrl+K or Cmd+K) to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
        setShowSearchResults(true);
      }
      if (e.key === "Escape") {
        setShowSearchResults(false);
        setDropdownOpen(false);
        setNotificationOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowSearchResults(false);
      }
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(e.target as Node)) {
        setNotificationOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filtered search results
  const filteredDocs = searchDocType.trim()
    ? doctypes
        .filter((d) => d.name.toLowerCase().includes(searchDocType.toLowerCase()))
        .slice(0, 12)
    : [];

  const handleSelectResult = (docName: string) => {
    setShowSearchResults(false);
    setSearchDocType("");
    if (onSelectDocType) {
      onSelectDocType(docName);
    } else {
      navigate(`/app/${encodeURIComponent(docName)}`);
    }
  };

  const userName = identity?.name || "Administrator";
  const userInitial = userName.charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-gray-200 bg-white px-4 sm:px-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
      {/* Left: Logo & Breadcrumbs / Toggle */}
      <div className="flex items-center gap-3">
        {/* Lotus Fin Brand Logo (Home Link) */}
        <Link
          to="/home"
          className="flex size-9 items-center justify-center rounded-xl bg-white hover:opacity-90 transition p-0.5"
          title="Lotus Fin Desk"
        >
          <img
            src={`${import.meta.env.BASE_URL}brand/logo.jpg`}
            alt="Lotus Fin"
            className="size-8 object-contain"
          />
        </Link>

        {/* Sidebar Toggle Button (Mobile / Non-Home) */}
        {!isHomePage && (
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden flex size-8 items-center justify-center rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-400"
          >
            <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        )}

        {/* Breadcrumb Path */}
        {!isHomePage && (
          <div className="hidden md:flex items-center gap-2 text-xs font-medium">
            <Link
              to="/home"
              className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            >
              Desk
            </Link>
            <span className="text-gray-300 dark:text-gray-700">/</span>
            <Link
              to={`/workspace/${encodeURIComponent(activeWorkspace)}`}
              className="text-gray-600 hover:text-[#1E63B7] dark:text-gray-300 transition-colors"
            >
              {formatBrandText(activeWorkspace)}
            </Link>
            <span className="text-gray-300 dark:text-gray-700">/</span>
            <span className="font-semibold text-gray-900 dark:text-white truncate max-w-[200px]">
              {formatBrandText(pageTitle)}
            </span>
          </div>
        )}
      </div>

      {/* Center: Search Box (ERPNext Style Search Bar with Ctrl+K & Brand Gradient Active Border) */}
      <div className="relative w-full max-w-sm sm:max-w-md mx-4" ref={searchContainerRef}>
        <div className="p-[2px] rounded-xl bg-gray-200/90 hover:bg-gray-300/80 focus-within:bg-gradient-to-r focus-within:from-[#1E63B7] focus-within:via-[#6EC1F6] focus-within:to-[#2FB29A] focus-within:shadow-md focus-within:shadow-[#1E63B7]/20 transition-all duration-200">
          <div className="relative rounded-[10px] bg-gray-50/90 focus-within:bg-white transition-colors">
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search or type a command (Ctrl + K)..."
              value={searchDocType}
              onChange={(e) => {
                setSearchDocType(e.target.value);
                setShowSearchResults(true);
              }}
              onFocus={() => setShowSearchResults(true)}
              className="h-9 w-full rounded-[10px] bg-transparent py-2 pl-9 pr-14 text-xs text-gray-800 placeholder:text-gray-400 focus:outline-none dark:border-gray-800 dark:bg-gray-800/70 dark:text-white dark:placeholder:text-gray-500 transition-all"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">
              <svg className="size-4 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </span>
            <div className="absolute right-2.5 top-1.5 flex items-center gap-0.5">
              <kbd className="rounded border border-gray-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-gray-400 dark:border-gray-700 dark:bg-gray-800 shadow-theme-xs">
                Ctrl+K
              </kbd>
            </div>
          </div>
        </div>

        {/* Quick Search Dropdown */}
        {showSearchResults && filteredDocs.length > 0 && (
          <div className="absolute left-0 mt-1.5 w-full rounded-2xl border border-gray-200 bg-white p-2 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark max-h-80 overflow-y-auto z-50 animate-in fade-in duration-100">
            <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
              DocTypes & Documents
            </div>
            {filteredDocs.map((doc) => (
              <div
                key={doc.name}
                onClick={() => handleSelectResult(doc.name)}
                className="flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-gray-700 hover:bg-[#E8F2FB] hover:text-[#1E63B7] cursor-pointer dark:text-gray-300 dark:hover:bg-brand-500/10 dark:hover:text-brand-400 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="size-3.5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <span>{formatBrandText(doc.name)}</span>
                </div>
                {doc.module && (
                  <span className="text-[10px] text-gray-400 dark:text-gray-500">{formatBrandText(doc.module)}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Notifications & User Avatar */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Notifications Bell */}
        <div className="relative" ref={notificationRef}>
          <button
            type="button"
            onClick={() => setNotificationOpen(!notificationOpen)}
            className="relative flex size-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-white/5 transition shadow-theme-xs"
            title="Notifications"
          >
            <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-brand-500" />
          </button>

          {notificationOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-gray-200 bg-white p-3 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark z-50">
              <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-800">
                <span className="text-xs font-semibold text-gray-900 dark:text-white">Notifications</span>
                <span className="text-[10px] text-[#1E63B7] cursor-pointer">Mark all as read</span>
              </div>
              <div className="py-3 text-center text-xs text-gray-400">
                No new notifications
              </div>
            </div>
          )}
        </div>

        {/* User Profile Avatar */}
        <div className="relative" ref={profileMenuRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-xl p-1 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
          >
            <div className="size-8 rounded-full bg-emerald-500 text-white font-bold text-xs flex items-center justify-center uppercase shadow-theme-xs">
              {userInitial}
            </div>
            <span className="hidden lg:block text-xs font-semibold text-gray-800 dark:text-white">
              {userName}
            </span>
            <svg className="hidden lg:block size-3.5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 rounded-2xl border border-gray-200 bg-white p-2 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark z-50 animate-in fade-in duration-100">
              <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-800">
                <p className="text-xs font-semibold text-gray-900 dark:text-white">
                  {userName}
                </p>
                <p className="text-[10px] text-gray-400 truncate">
                  {identity?.email || "admin@lotusfin.com"}
                </p>
              </div>

              <div className="py-1">
                <Link
                  to="/home"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-white/5 transition-colors"
                >
                  <svg className="size-4 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
                  </svg>
                  Switch Workspace
                </Link>

                <button
                  type="button"
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-500/10 transition-colors"
                >
                  <svg className="size-4 fill-current" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" />
                  </svg>
                  Log Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
