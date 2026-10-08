import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Badge from "../../components/ui/badge/Badge";

interface WorkspaceLink {
  label: string;
  type: string; // "Link" | "Card Break"
  link_type: string; // "DocType" | "Page" | "Report"
  link_to?: string;
  hidden?: number;
  onboard?: number;
}

interface WorkspaceData {
  name: string;
  title: string;
  links?: WorkspaceLink[];
  content?: string;
}

// Global in-memory cache for Workspaces
const workspaceCache = new Map<string, WorkspaceData>();

export const UniversalWorkspaceView: React.FC = () => {
  const { workspaceName } = useParams<{ workspaceName: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const isDashboardView = searchParams.get("view") === "dashboard";

  const [workspace, setWorkspace] = useState<WorkspaceData | null>(
    () => (workspaceName && workspaceCache.has(workspaceName) ? workspaceCache.get(workspaceName)! : null)
  );
  const [loading, setLoading] = useState(!workspaceName || !workspaceCache.has(workspaceName));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceName) return;

    if (workspaceCache.has(workspaceName)) {
      setWorkspace(workspaceCache.get(workspaceName)!);
      setLoading(false);
    } else {
      setLoading(true);
    }

    setError(null);

    const tryLoadSidebar = (wsName: string) => {
      return axios
        .get(`/api/resource/Workspace Sidebar/${encodeURIComponent(wsName)}`)
        .then((wsRes) => {
          const items = wsRes.data?.data?.items || [];
          if (items.length > 0) {
            const convertedLinks: WorkspaceLink[] = items.map((it: any) => ({
              label: it.label,
              type: it.type === "Section Break" || it.type === "Card Break" ? "Card Break" : "Link",
              link_type: it.link_type || "DocType",
              link_to: it.link_to || it.label,
              hidden: it.hidden ? 1 : 0,
            }));
            const wsData: WorkspaceData = {
              name: workspaceName,
              title: workspaceName,
              links: convertedLinks,
            };
            workspaceCache.set(workspaceName, wsData);
            setWorkspace(wsData);
            return true;
          }
          return false;
        });
    };

    axios
      .get(`/api/resource/Workspace/${encodeURIComponent(workspaceName)}`)
      .then((res) => {
        const wsData = res.data?.data;
        if (wsData && wsData.links && wsData.links.length > 0) {
          workspaceCache.set(workspaceName, wsData);
          setWorkspace(wsData);
        } else {
          tryLoadSidebar(workspaceName).catch(() => {
            if (workspaceName.toLowerCase() === "accounting") {
              tryLoadSidebar("Invoicing").catch(() => {});
            }
          });
        }
      })
      .catch(() => {
        tryLoadSidebar(workspaceName)
          .catch(() => {
            if (workspaceName.toLowerCase() === "accounting") {
              return tryLoadSidebar("Invoicing");
            }
            throw new Error(`Unable to load Workspace "${workspaceName}"`);
          })
          .catch((err) => {
            // Built-in fallback links for common workspaces
            const fallbackMap: Record<string, WorkspaceLink[]> = {
              Accounting: [
                { label: "Receivables", type: "Card Break", link_type: "DocType" },
                { label: "Customer", type: "Link", link_type: "DocType" },
                { label: "Sales Invoice", type: "Link", link_type: "DocType", onboard: 1 },
                { label: "Accounts Receivable", type: "Link", link_type: "Report" },
                { label: "Payables", type: "Card Break", link_type: "DocType" },
                { label: "Supplier", type: "Link", link_type: "DocType" },
                { label: "Purchase Invoice", type: "Link", link_type: "DocType", onboard: 1 },
                { label: "Accounts Payable", type: "Link", link_type: "Report" },
                { label: "Financial Reports", type: "Card Break", link_type: "DocType" },
                { label: "General Ledger", type: "Link", link_type: "Report", onboard: 1 },
                { label: "Profit and Loss Statement", type: "Link", link_type: "Report" },
                { label: "Balance Sheet", type: "Link", link_type: "Report" },
                { label: "Accounting Masters", type: "Card Break", link_type: "DocType" },
                { label: "Chart of Accounts", type: "Link", link_type: "Page", onboard: 1 },
                { label: "Company", type: "Link", link_type: "DocType" },
                { label: "Payment Entry", type: "Link", link_type: "DocType" },
              ],
              Invoicing: [
                { label: "Receivables", type: "Card Break", link_type: "DocType" },
                { label: "Customer", type: "Link", link_type: "DocType" },
                { label: "Sales Invoice", type: "Link", link_type: "DocType", onboard: 1 },
                { label: "Accounts Receivable", type: "Link", link_type: "Report" },
                { label: "Payables", type: "Card Break", link_type: "DocType" },
                { label: "Supplier", type: "Link", link_type: "DocType" },
                { label: "Purchase Invoice", type: "Link", link_type: "DocType", onboard: 1 },
                { label: "Accounts Payable", type: "Link", link_type: "Report" },
              ],
            };

            const matchedFallback = fallbackMap[workspaceName] || fallbackMap["Accounting"];
            if (matchedFallback) {
              const wsData: WorkspaceData = {
                name: workspaceName,
                title: workspaceName,
                links: matchedFallback,
              };
              workspaceCache.set(workspaceName, wsData);
              setWorkspace(wsData);
            } else {
              setError(err.response?.data?.message || `Unable to load Workspace "${workspaceName}"`);
            }
          });
      })
      .finally(() => {
        setLoading(false);
      });
  }, [workspaceName]);

  if (loading && !workspace) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
          <div className="h-4 w-72 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-3">
              <div className="h-5 w-32 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
              <div className="space-y-2 pt-2">
                <div className="h-4 w-full bg-gray-50 dark:bg-gray-800/50 rounded animate-pulse" />
                <div className="h-4 w-3/4 bg-gray-50 dark:bg-gray-800/50 rounded animate-pulse" />
                <div className="h-4 w-5/6 bg-gray-50 dark:bg-gray-800/50 rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !workspace) {
    return (
      <div className="rounded-2xl border border-error-500/20 bg-error-50 p-8 text-center dark:bg-error-500/10">
        <p className="text-error-600 font-medium">{error || "No workspace found"}</p>
      </div>
    );
  }

  // Group links by Card Break
  const cardSections: { title: string; links: WorkspaceLink[] }[] = [];
  let currentSection: { title: string; links: WorkspaceLink[] } = {
    title: "Overview & Masters",
    links: [],
  };

  (workspace.links || []).forEach((link) => {
    if (link.type === "Card Break") {
      if (currentSection.links.length > 0) {
        cardSections.push(currentSection);
      }
      currentSection = {
        title: link.label,
        links: [],
      };
    } else if (link.type === "Link" && !link.hidden) {
      currentSection.links.push(link);
    }
  });
  if (currentSection.links.length > 0) {
    cardSections.push(currentSection);
  }

  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
            {isDashboardView ? `${workspace.title || workspace.name} Dashboard` : (workspace.title || workspace.name)}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {isDashboardView
              ? `Financial metrics & KPIs for ${workspace.title || workspace.name}`
              : `Reports & Masters Directory`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/workspace/${encodeURIComponent(workspaceName || "")}`)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              !isDashboardView
                ? "bg-brand-500 text-white shadow-theme-xs"
                : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => navigate(`/workspace/${encodeURIComponent(workspaceName || "")}?view=dashboard`)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              isDashboardView
                ? "bg-brand-500 text-white shadow-theme-xs"
                : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            Dashboard KPI
          </button>
        </div>
      </div>

      {/* 2. TailAdmin Fintech KPI Metrics (Only on Dashboard View) */}
      {isDashboardView && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 md:gap-6">
          {/* Outgoing Bills */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 dark:bg-brand-500/10 text-brand-500">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Projected Revenue</span>
                <h4 className="mt-1 text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                  363,000 <span className="text-xs font-normal text-gray-400">USD</span>
                </h4>
              </div>
              <Badge color="info" size="sm">
                Sales
              </Badge>
            </div>
          </div>

          {/* Incoming Bills */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 dark:bg-warning-500/10 text-warning-600">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a4 4 0 00-4 4v1H5a1 1 0 00-.994.89l-1 9A1 1 0 004 18h12a1 1 0 00.994-1.11l-1-9A1 1 0 0015 7h-1V6a4 4 0 00-4-4zm2 5V6a2 2 0 10-4 0v1h4zm-6 3a1 1 0 112 0 1 1 0 01-2 0zm7-1a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Outstanding Payables</span>
                <h4 className="mt-1 text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                  349,150 <span className="text-xs font-normal text-gray-400">USD</span>
                </h4>
              </div>
              <Badge color="warning" size="sm">
                Buying
              </Badge>
            </div>
          </div>

          {/* Incoming Payment */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 dark:bg-success-500/10 text-success-600">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Collected Payments</span>
                <h4 className="mt-1 text-xl sm:text-2xl font-bold text-success-600">
                  47,000 <span className="text-xs font-normal text-gray-400">USD</span>
                </h4>
              </div>
              <Badge color="success" size="sm">
                Inflow
              </Badge>
            </div>
          </div>

          {/* Outgoing Payment */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-50 dark:bg-error-500/10 text-error-600">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12 13a1 1 0 100 2h5a1 1 0 001-1V9a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586 3.707 5.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L11 9.414 14.586 13H12z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Disbursed Expenses</span>
                <h4 className="mt-1 text-xl sm:text-2xl font-bold text-error-600">
                  164,850 <span className="text-xs font-normal text-gray-400">USD</span>
                </h4>
              </div>
              <Badge color="error" size="sm">
                Outflow
              </Badge>
            </div>
          </div>
        </div>
      )}

      {/* 3. Reports & Masters Grid (Matching Image 2 Matrix Layout Exactly) */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {cardSections.map((section, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark flex flex-col justify-between"
          >
            <div>
              <h3 className="mb-3.5 pb-2.5 text-sm font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
                <span>{section.title}</span>
                <span className="text-[10px] font-normal text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
                  {section.links.length}
                </span>
              </h3>

              <div className="space-y-1">
                {section.links.map((link, lIdx) => {
                  const target = link.link_to || link.label;
                  let targetUrl = `/app/${encodeURIComponent(target)}`;
                  if (
                    link.link_type === "Report" ||
                    link.link_type === "Query Report" ||
                    link.link_type === "Script Report"
                  ) {
                    targetUrl = `/report/${encodeURIComponent(target)}`;
                  } else if (link.link_type === "Workspace") {
                    targetUrl = `/workspace/${encodeURIComponent(target)}`;
                  }

                  return (
                    <div
                      key={lIdx}
                      onClick={() => navigate(targetUrl)}
                      className="group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-300 hover:text-brand-500 dark:hover:text-brand-400 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="truncate">{link.label}</span>
                        {link.onboard ? (
                          <span className="text-[9px] font-semibold text-brand-600 bg-brand-50 dark:bg-brand-500/15 dark:text-brand-400 px-1.5 py-0.2 rounded">
                            Primary
                          </span>
                        ) : null}
                      </div>

                      <div className="flex items-center gap-1.5 text-gray-400 group-hover:text-brand-500 transition-colors">
                        {link.link_type === "Report" && (
                          <span className="text-[9px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-1 rounded">
                            Report
                          </span>
                        )}
                        {/* ↗ Matrix Link Arrow matching ERPNext Desk */}
                        <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
