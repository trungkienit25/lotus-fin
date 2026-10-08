import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";

export interface SidebarItem {
  label: string;
  type: string; // "Link" | "Section Break"
  link_type?: string;
  link_to?: string;
  icon?: string;
}

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeWorkspace: string;
  sidebarItems: SidebarItem[];
  loadingSidebar: boolean;
}

export const TailAdminSidebar: React.FC<SidebarProps> = ({
  sidebarOpen,
  setSidebarOpen,
  activeWorkspace,
  sidebarItems,
  loadingSidebar,
}) => {
  const location = useLocation();
  const currentFullUrl = location.pathname + (location.search ? location.search : "");

  // Normalize menu links from ERPNext Workspace Sidebar
  const menuGroups: { sectionTitle: string; links: { label: string; url: string; link_type?: string }[] }[] = [];
  let currentGroup: { sectionTitle: string; links: { label: string; url: string; link_type?: string }[] } = {
    sectionTitle: "OVERVIEW",
    links: [],
  };

  const seenKeys = new Set<string>();

  sidebarItems.forEach((item) => {
    if (item.type === "Section Break" || item.type === "Card Break") {
      if (currentGroup.links.length > 0) {
        menuGroups.push(currentGroup);
      }
      currentGroup = {
        sectionTitle: item.label.toUpperCase(),
        links: [],
      };
    } else if (item.type === "Link" && (item.link_to || item.label)) {
      const linkTarget = item.link_to || item.label;
      let targetUrl = `/app/${encodeURIComponent(linkTarget)}`;

      if (item.link_type === "Workspace" || item.label === "Home") {
        const wsTarget = item.link_to || activeWorkspace;
        targetUrl = `/workspace/${encodeURIComponent(wsTarget)}`;
      } else if (item.link_type === "Dashboard" || item.label === "Dashboard") {
        targetUrl = `/workspace/${encodeURIComponent(activeWorkspace)}?view=dashboard`;
      } else if (
        item.link_type === "Report" ||
        item.link_type === "Query Report" ||
        item.link_type === "Script Report"
      ) {
        targetUrl = `/report/${encodeURIComponent(linkTarget)}`;
      } else if (item.link_type === "Page") {
        targetUrl = `/page/${encodeURIComponent(linkTarget)}`;
      } else if (item.label === "Repost Accounting Ledger Settings" || linkTarget === "Repost Accounting Ledger Settings") {
        targetUrl = `/app/Repost%20Accounting%20Ledger`;
      } else if (item.label === "Credit Note" && linkTarget === "Sales Invoice") {
        targetUrl = `/app/Sales%20Invoice?is_return=1&title=Credit%20Note`;
      } else if (item.label === "Debit Note" && linkTarget === "Purchase Invoice") {
        targetUrl = `/app/Purchase%20Invoice?is_return=1&title=Debit%20Note`;
      } else if (item.label === "Subcontracting Delivery" && linkTarget === "Stock Entry") {
        targetUrl = `/app/Stock%20Entry?purpose=Send%20to%20Subcontractor&title=Subcontracting%20Delivery`;
      } else if (item.label === "Tree of Procedures" && linkTarget === "Quality Procedure") {
        targetUrl = `/app/Quality%20Procedure?view=Tree&title=Tree%20of%20Procedures`;
      }

      const itemKey = `${item.label}::${targetUrl}`;
      if (!seenKeys.has(itemKey)) {
        seenKeys.add(itemKey);
        currentGroup.links.push({
          label: item.label,
          url: targetUrl,
          link_type: item.link_type,
        });
      }
    }
  });

  if (currentGroup.links.length > 0) {
    menuGroups.push(currentGroup);
  }

  // Ensure there is always a Home link
  const hasWorkspaceOverview = Array.from(seenKeys).some((k) =>
    k.includes(`/workspace/${encodeURIComponent(activeWorkspace)}`)
  );
  if (!hasWorkspaceOverview) {
    const workspaceUrl = `/workspace/${encodeURIComponent(activeWorkspace)}`;
    if (menuGroups.length > 0 && menuGroups[0].sectionTitle === "OVERVIEW") {
      menuGroups[0].links.unshift({
        label: "Home",
        url: workspaceUrl,
        link_type: "Workspace",
      });
    } else {
      menuGroups.unshift({
        sectionTitle: "OVERVIEW",
        links: [
          {
            label: "Home",
            url: workspaceUrl,
            link_type: "Workspace",
          },
        ],
      });
    }
  }

  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  const toggleSection = (title: string) => {
    setCollapsedSections((prev) => ({ ...prev, [title]: !prev[title] }));
  };

  const isLinkActive = (linkUrl: string) => {
    const currentPathDecoded = decodeURIComponent(location.pathname);
    const currentSearch = location.search || "";
    const linkUrlDecoded = decodeURIComponent(linkUrl);

    const [linkPath, linkQuery] = linkUrlDecoded.split("?");

    // 1. If link has query params (e.g. ?view=dashboard or ?is_return=1)
    if (linkQuery) {
      return currentPathDecoded === linkPath && currentSearch.includes(linkQuery);
    }

    // 2. If exact path match
    if (currentPathDecoded === linkPath) {
      // If current search has ?view=dashboard, do not mark Home / overview link as active
      if (linkPath.startsWith("/workspace/") && currentSearch.includes("view=dashboard")) {
        return false;
      }
      return true;
    }

    // 3. If nested doc under doctype (e.g. /app/Buying Settings/Buying Settings or /app/Customer/CUST-001)
    if (currentPathDecoded.startsWith(linkPath + "/") && linkPath !== "/app") {
      return true;
    }

    // 4. If current is /workspace/WorkspaceName and link is Home
    if (linkPath === `/workspace/${activeWorkspace}` && currentPathDecoded === `/workspace/${activeWorkspace}` && !currentSearch.includes("view=dashboard")) {
      return true;
    }

    return false;
  };

  return (
    <aside
      className={`fixed lg:static top-0 left-0 z-50 flex h-screen w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-dark transition-all duration-300 ease-in-out ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200 dark:border-gray-800">
        <Link to="/home" className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-brand-500 text-white font-bold text-base shadow-theme-xs">
            LF
          </div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight truncate max-w-[130px]">
              {activeWorkspace}
            </h1>
            <p className="text-[10px] text-gray-500 font-medium">Lotus Fin Core</p>
          </div>
        </Link>

        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden text-gray-500 hover:text-gray-900 dark:hover:text-white"
        >
          <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Nav Menu */}
      <div className="no-scrollbar flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {menuGroups.length === 0 && loadingSidebar ? (
          <div className="space-y-4 py-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-20 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
                <div className="h-8 w-full bg-gray-100 dark:bg-gray-800/60 rounded-lg animate-pulse" />
              </div>
            ))}
          </div>
        ) : (
          menuGroups.map((group, gIdx) => {
            const isCollapsed = !!collapsedSections[group.sectionTitle];
            return (
              <div key={gIdx}>
                <div
                  onClick={() => toggleSection(group.sectionTitle)}
                  className="flex items-center justify-between cursor-pointer px-3 py-1.5 text-[11px] font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-200 transition-colors select-none"
                >
                  <span>{group.sectionTitle}</span>
                  <svg
                    className={`size-3 text-gray-400 transition-transform duration-200 ${
                      isCollapsed ? "-rotate-90" : "rotate-0"
                    }`}
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>

                {!isCollapsed && (
                  <ul className="mt-1 space-y-0.5">
                    {group.links.map((link, lIdx) => {
                      const isActive = isLinkActive(link.url);

                      return (
                        <li key={lIdx}>
                          <Link
                            to={link.url}
                            className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                              isActive
                                ? "bg-brand-500 text-white font-semibold shadow-theme-xs hover:bg-brand-600 dark:bg-brand-500"
                                : "text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                            }`}
                          >
                            <span className="truncate">{link.label}</span>
                            {link.link_type === "Report" && (
                              <span
                                className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-normal ${
                                  isActive
                                    ? "bg-white/20 text-white"
                                    : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                                }`}
                              >
                                REP
                              </span>
                            )}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
