import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { TailAdminHeader } from "../tailadmin/Header";
import { TailAdminSidebar, SidebarItem } from "../tailadmin/Sidebar";
import { LotusCopilotDrawer } from "../copilot/LotusCopilotDrawer";

const MODULE_TO_WORKSPACE: Record<string, string> = {
  Accounts: "Invoicing",
  Invoicing: "Invoicing",
  Buying: "Buying",
  Selling: "Selling",
  Stock: "Stock",
  Manufacturing: "Manufacturing",
  CRM: "CRM",
  Assets: "Assets",
  Projects: "Projects",
  "Quality Management": "Quality",
  Quality: "Quality",
  Subcontracting: "Subcontracting",
  Core: "Build",
  Custom: "Build",
  Customization: "Build",
  Workflow: "Build",
  Automation: "Build",
  Printing: "Build",
  "Data Migration": "Build",
  Desk: "Build",
  Setup: "ERPNext Settings",
  Email: "ERPNext Settings",
  Geo: "ERPNext Settings",
  Settings: "ERPNext Settings",
  "ERPNext Settings": "ERPNext Settings",
  Website: "Website",
  Support: "Support",
  Integrations: "Integrations",
  "Lotus Fin AI": "Lotus Fin AI",
  lotus_fin_ai: "Lotus Fin AI",
  "lotus-copilot": "Lotus Fin AI",
  "financial-health": "Lotus Fin AI",
  "cash-forecast": "Lotus Fin AI",
  "risk-signal": "Lotus Fin AI",
  "what-if-studio": "Lotus Fin AI",
  "financing-copilot": "Lotus Fin AI",
  "repayment-schedule": "Lotus Fin AI",
  copilot: "Lotus Fin AI",
  ai: "Lotus Fin AI",
  Users: "Users",
  HR: "HR",
  HRMS: "HR",
  Payroll: "HR",
  Loan: "Invoicing",
};

// Global in-memory cache for Sidebar items per Workspace
const sidebarCache = new Map<string, SidebarItem[]>();

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarItems, setSidebarItems] = useState<SidebarItem[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);
  const [doctypes, setDoctypes] = useState<{ name: string; module?: string }[]>([]);
  const [searchDocType, setSearchDocType] = useState("");

  const currentPath = location.pathname;
  const isHomePage = currentPath === "/" || currentPath === "/home";
  const isAIPage =
    currentPath === "/ai" ||
    currentPath === "/copilot" ||
    currentPath.startsWith("/workspace/Lotus%20Fin%20AI") ||
    currentPath.startsWith("/workspace/Lotus Fin AI") ||
    currentPath.startsWith("/page/lotus-copilot") ||
    currentPath.startsWith("/page/financial-health") ||
    currentPath.startsWith("/page/cash-forecast") ||
    currentPath.startsWith("/page/risk-signal") ||
    currentPath.startsWith("/page/what-if-studio") ||
    currentPath.startsWith("/page/financing-copilot") ||
    currentPath.startsWith("/page/repayment-schedule");

  // Quản lý activeWorkspace linh hoạt theo ngữ cảnh người dùng đang xem
  const [activeWorkspace, setActiveWorkspace] = useState<string>(() => {
    if (isAIPage) return "Lotus Fin AI";
    return sessionStorage.getItem("lotus_active_workspace") || "Invoicing";
  });

  // 1. Tự động xác định Active Workspace từ URL & DocType Module (với bảo lưu Workspace hiện tại)
  useEffect(() => {
    if (isHomePage) return;

    if (isAIPage) {
      if (activeWorkspace !== "Lotus Fin AI") {
        setActiveWorkspace("Lotus Fin AI");
        sessionStorage.setItem("lotus_active_workspace", "Lotus Fin AI");
      }
      return;
    }

    if (currentPath.startsWith("/workspace/")) {
      const wsName = decodeURIComponent(currentPath.replace("/workspace/", "").split("?")[0]);
      if (wsName && wsName !== activeWorkspace) {
        setActiveWorkspace(wsName);
        sessionStorage.setItem("lotus_active_workspace", wsName);
      }
    } else if (currentPath.startsWith("/app/")) {
      const rawDoc = currentPath.replace("/app/", "").split("/")[0].split("?")[0];
      const currentDocType = decodeURIComponent(rawDoc);

      // Nếu DocType đang xem đã tồn tại trong danh mục Sidebar của Workspace hiện tại -> Giữ nguyên Workspace!
      const existsInCurrentSidebar = sidebarItems.some(
        (item) => item.link_to === currentDocType || item.label === currentDocType
      );
      if (existsInCurrentSidebar) return;

      // Tra cứu module của DocType hiện tại để tìm đúng Workspace
      axios
        .get(`/api/resource/DocType/${encodeURIComponent(currentDocType)}?fields=["name","module"]`)
        .then((res) => {
          const mod = res.data?.data?.module;
          if (mod) {
            const mappedWs = MODULE_TO_WORKSPACE[mod] || (mod in MODULE_TO_WORKSPACE ? MODULE_TO_WORKSPACE[mod] : null);
            if (mappedWs && mappedWs !== activeWorkspace) {
              setActiveWorkspace(mappedWs);
              sessionStorage.setItem("lotus_active_workspace", mappedWs);
            }
          }
        })
        .catch(() => {});
    } else if (currentPath.startsWith("/report/")) {
      const rawReport = currentPath.replace("/report/", "").split("?")[0];
      const currentReport = decodeURIComponent(rawReport);

      const existsInCurrentSidebar = sidebarItems.some(
        (item) => item.link_to === currentReport || item.label === currentReport
      );
      if (existsInCurrentSidebar) return;

      axios
        .get(`/api/resource/Report/${encodeURIComponent(currentReport)}?fields=["name","module"]`)
        .then((res) => {
          const mod = res.data?.data?.module;
          if (mod) {
            const mappedWs = MODULE_TO_WORKSPACE[mod] || (mod in MODULE_TO_WORKSPACE ? MODULE_TO_WORKSPACE[mod] : null);
            if (mappedWs && mappedWs !== activeWorkspace) {
              setActiveWorkspace(mappedWs);
              sessionStorage.setItem("lotus_active_workspace", mappedWs);
            }
          }
        })
        .catch(() => {});
    } else if (currentPath.startsWith("/page/")) {
      const rawPage = currentPath.replace("/page/", "").split("?")[0];
      const currentPage = decodeURIComponent(rawPage);

      const existsInCurrentSidebar = sidebarItems.some(
        (item) => item.link_to === currentPage || item.label === currentPage
      );
      if (existsInCurrentSidebar) return;

      axios
        .get(`/api/resource/Page/${encodeURIComponent(currentPage)}?fields=["name","module"]`)
        .then((res) => {
          const mod = res.data?.data?.module;
          if (mod) {
            const mappedWs = MODULE_TO_WORKSPACE[mod] || (mod in MODULE_TO_WORKSPACE ? MODULE_TO_WORKSPACE[mod] : null);
            if (mappedWs && mappedWs !== activeWorkspace) {
              setActiveWorkspace(mappedWs);
              sessionStorage.setItem("lotus_active_workspace", mappedWs);
            }
          }
        })
        .catch(() => {});
    }
  }, [currentPath, isHomePage, isAIPage, sidebarItems, activeWorkspace]);

  // 2. Tải danh mục Sidebar chuẩn từ Workspace Sidebar (với SWR In-Memory Cache)
  useEffect(() => {
    if (isHomePage || isAIPage || !activeWorkspace) return;

    if (sidebarCache.has(activeWorkspace)) {
      setSidebarItems(sidebarCache.get(activeWorkspace)!);
      setLoadingSidebar(false);
    } else {
      setLoadingSidebar(true);
    }

    axios
      .get(`/api/resource/Workspace Sidebar/${encodeURIComponent(activeWorkspace)}`)
      .then((res) => {
        const items = res.data?.data?.items || [];
        sidebarCache.set(activeWorkspace, items);
        setSidebarItems(items);
      })
      .catch(() => {
        axios.get(`/api/resource/Workspace/${encodeURIComponent(activeWorkspace)}`).then((res) => {
          const links = res.data?.data?.links || [];
          const converted = links.map((l: any) => ({
            label: l.label,
            type: l.type === "Card Break" ? "Section Break" : "Link",
            link_to: l.link_to || l.label,
            link_type: l.link_type,
          }));
          sidebarCache.set(activeWorkspace, converted);
          setSidebarItems(converted);
        });
      })
      .finally(() => setLoadingSidebar(false));
  }, [activeWorkspace, isHomePage]);

  // 3. Tải danh sách DocType phục vụ tìm kiếm nhanh (Ctrl+K)
  useEffect(() => {
    axios
      .get('/api/resource/DocType?fields=["name","module"]&limit_page_length=1000')
      .then((res) => setDoctypes(res.data?.data || []))
      .catch(() => {});
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900 font-satoshi text-gray-700 dark:text-gray-300">
      {/* TailAdmin Modern Sidebar (Shown for ERP modules, hidden for Home & Dedicated AI Workspace) */}
      {!isHomePage && !isAIPage && (
        <TailAdminSidebar
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          activeWorkspace={activeWorkspace}
          sidebarItems={sidebarItems}
          loadingSidebar={loadingSidebar}
        />
      )}

      {/* Main Content Area */}
      <div className="relative flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
        {/* TailAdmin Modern Header (ERPNext Style Navigation) */}
        <TailAdminHeader
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          activeWorkspace={activeWorkspace}
          searchDocType={searchDocType}
          setSearchDocType={setSearchDocType}
          onSelectDocType={(doc) => navigate(`/app/${encodeURIComponent(doc)}`)}
          doctypes={doctypes}
        />

        {/* Content Container */}
        <main className={`flex-1 ${isAIPage ? "p-0 overflow-hidden" : "p-4 sm:p-6 lg:p-8"}`}>
          <div className={isAIPage ? "h-full w-full" : "mx-auto max-w-7xl"}>{children}</div>
        </main>
      </div>

      {/* Floating AI Copilot Widget (Hidden on dedicated AI page) */}
      {!isAIPage && <LotusCopilotDrawer />}
    </div>
  );
};
