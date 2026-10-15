import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import dayjs from "dayjs";
import { useTranslation } from "../../i18n";
import { formatBrandText } from "../../utils/brand";
import { LotusCopilotPage } from "../copilot/LotusCopilotPage";

interface FunnelStage {
  title: string;
  value: number;
  color?: string;
}

export const UniversalPageView: React.FC = () => {
  const { t } = useTranslation();
  const { pageName: rawPageName } = useParams<{ pageName: string }>();
  const pageName = rawPageName ? decodeURIComponent(rawPageName) : "";
  const navigate = useNavigate();

  // If page is an AI Feature Page, render LotusCopilotPage directly
  if (
    [
      "financial-health",
      "cash-forecast",
      "risk-signal",
      "what-if-studio",
      "lotus-copilot",
      "financing-copilot",
      "repayment-schedule",
      "ai",
    ].includes(pageName)
  ) {
    return <LotusCopilotPage />;
  }

  const [pageDoc, setPageDoc] = useState<{ title?: string; name: string; module?: string; icon?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sales Funnel Filters
  const [companies, setCompanies] = useState<string[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("Lotus-fin (Demo)");
  const [fromDate, setFromDate] = useState<string>(dayjs().startOf("year").format("YYYY-MM-DD"));
  const [toDate, setToDate] = useState<string>(dayjs().endOf("year").format("YYYY-MM-DD"));

  // Funnel Data
  const [funnelData, setFunnelData] = useState<FunnelStage[]>([
    { title: "Active Leads", value: 0, color: "#3B82F6" },
    { title: "Opportunities", value: 0, color: "#F59E0B" },
    { title: "Quotations", value: 0, color: "#8B5CF6" },
    { title: "Converted", value: 0, color: "#10B981" },
  ]);

  // Permission Manager Data
  const [doctypes, setDoctypes] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedDocType, setSelectedDocType] = useState<string>("Sales Invoice");
  const [selectedRole, setSelectedRole] = useState<string>("Sales User");
  const [permissions, setPermissions] = useState<any[]>([]);

  // POS Data
  const [posProfiles, setPosProfiles] = useState<any[]>([]);
  const [posInvoicesCount, setPosInvoicesCount] = useState<number>(0);

  const fetchFunnelData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(
        `/api/method/erpnext.selling.page.sales_funnel.sales_funnel.get_funnel_data`,
        {
          params: {
            company: selectedCompany,
            from_date: fromDate,
            to_date: toDate,
          },
        }
      );
      if (Array.isArray(res.data?.message)) {
        setFunnelData(res.data.message);
      }
    } catch (err: any) {
      try {
        const [leadsRes, oppsRes, quotesRes, custRes] = await Promise.all([
          axios.get("/api/method/frappe.client.get_count?doctype=Lead"),
          axios.get("/api/method/frappe.client.get_count?doctype=Opportunity"),
          axios.get("/api/method/frappe.client.get_count?doctype=Quotation"),
          axios.get("/api/method/frappe.client.get_count?doctype=Customer"),
        ]);

        setFunnelData([
          { title: "Active Leads", value: leadsRes.data?.message || 0, color: "#3B82F6" },
          { title: "Opportunities", value: oppsRes.data?.message || 0, color: "#F59E0B" },
          { title: "Quotations", value: quotesRes.data?.message || 0, color: "#8B5CF6" },
          { title: "Converted", value: custRes.data?.message || 0, color: "#10B981" },
        ]);
      } catch (fallbackErr: any) {
        setError(fallbackErr.message || "Error loading sales funnel data");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPermissionData = async () => {
    setLoading(true);
    try {
      const [dtRes, rRes, permRes] = await Promise.all([
        axios.get('/api/resource/DocType?fields=["name"]&limit_page_length=200'),
        axios.get('/api/resource/Role?fields=["name"]&limit_page_length=200'),
        axios.get(
          `/api/resource/Custom DocPerm?filters=[["parent","=","${selectedDocType}"],["role","=","${selectedRole}"]]&fields=["*"]`
        ),
      ]);
      setDoctypes((dtRes.data?.data || []).map((d: any) => d.name));
      setRoles((rRes.data?.data || []).map((r: any) => r.name));
      setPermissions(permRes.data?.data || []);
    } catch (err: any) {
      console.warn("Error loading permissions:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPosData = async () => {
    setLoading(true);
    try {
      const [profRes, countRes] = await Promise.all([
        axios.get('/api/resource/POS Profile?fields=["*"]&limit_page_length=20'),
        axios.get('/api/method/frappe.client.get_count?doctype=POS Invoice'),
      ]);
      setPosProfiles(profRes.data?.data || []);
      setPosInvoicesCount(countRes.data?.message || 0);
    } catch (err: any) {
      console.warn("Error loading POS data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    axios
      .get(`/api/resource/Page/${encodeURIComponent(pageName || "")}`)
      .then((res) => {
        setPageDoc(res.data?.data || null);
      })
      .catch(() => {});

    axios
      .get("/api/resource/Company?limit_page_length=50")
      .then((res) => {
        const list = (res.data?.data || []).map((c: any) => c.name);
        setCompanies(list);
        if (list.length > 0 && !list.includes(selectedCompany)) {
          setSelectedCompany(list[0]);
        }
      })
      .catch(() => {});

    if (pageName === "sales-funnel") {
      fetchFunnelData();
    } else if (pageName === "permission-manager") {
      fetchPermissionData();
    } else if (pageName === "point-of-sale" || pageName === "pos") {
      fetchPosData();
    } else {
      setLoading(false);
    }
  }, [pageName]);

  const maxVal = Math.max(...funnelData.map((d) => d.value), 1);
  const totalLeads = funnelData[0]?.value || 0;
  const converted = funnelData[3]?.value || 0;
  const overallConversionRate = totalLeads > 0 ? ((converted / totalLeads) * 100).toFixed(1) : "0.0";

  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
            {pageDoc?.title ||
              (pageName === "sales-funnel"
                ? t("funnel.title")
                : pageName === "point-of-sale" || pageName === "pos"
                ? t("pos.title")
                : pageName === "permission-manager"
                ? t("permissions.title")
                : pageName)}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {pageName === "sales-funnel"
              ? t("funnel.subtitle")
              : pageName === "point-of-sale" || pageName === "pos"
              ? t("pos.subtitle")
              : pageName === "permission-manager"
              ? t("permissions.subtitle")
              : t("workspace.manageAndLookUp", { name: pageName })}
          </p>
        </div>

        {pageName === "sales-funnel" && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate("/app/Lead/new")}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-brand-500 px-3.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 transition-colors"
            >
              <span>{t("funnel.addLead")}</span>
            </button>
            <button
              onClick={() => navigate("/app/Opportunity/new")}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3.5 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 transition-colors"
            >
              <span>{t("funnel.addOpportunity")}</span>
            </button>
          </div>
        )}

        {(pageName === "point-of-sale" || pageName === "pos") && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate("/app/POS%20Invoice/new")}
              className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] px-3.5 text-xs font-semibold text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98] transition-all"
            >
              <span>{t("pos.newInvoice")}</span>
            </button>
            <button
              onClick={() => navigate("/app/POS%20Opening%20Entry/new")}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3.5 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 transition-colors"
            >
              <span>{t("pos.openShift")}</span>
            </button>
          </div>
        )}
      </div>

      {/* 2. Content for SALES FUNNEL */}
      {pageName === "sales-funnel" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                fetchFunnelData();
              }}
              className="flex flex-wrap items-center gap-4 text-xs"
            >
              <div className="flex-1 min-w-[200px]">
                <label className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{t("report.company")}</label>
                <select
                  value={selectedCompany}
                  onChange={(e) => setSelectedCompany(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-transparent py-2 px-3 text-xs text-gray-800 dark:border-gray-700 dark:text-white"
                >
                  {companies.map((c) => (
                    <option key={c} value={c} className="dark:bg-gray-900">
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="min-w-[150px]">
                <label className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{t("report.fromDate")}</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-transparent py-2 px-3 text-xs text-gray-800 dark:border-gray-700 dark:text-white"
                />
              </div>

              <div className="min-w-[150px]">
                <label className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{t("report.toDate")}</label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-transparent py-2 px-3 text-xs text-gray-800 dark:border-gray-700 dark:text-white"
                />
              </div>

              <div className="self-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex h-9 items-center justify-center rounded-xl bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] px-5 text-xs font-semibold text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98] disabled:opacity-50 transition-all"
                >
                  {loading ? t("common.loading") : t("report.filterResults")}
                </button>
              </div>
            </form>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {funnelData.map((stage, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{stage.title}</span>
                  <span
                    className="size-3 rounded-full"
                    style={{ backgroundColor: stage.color || "#3B82F6" }}
                  />
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">{stage.value}</span>
                  <span className="text-[11px] text-gray-400">{t("funnel.records")}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-6">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-4">
              <h2 className="text-base font-bold text-gray-900 dark:text-white">{t("funnel.conversionFlow")}</h2>
              <span className="text-xs font-medium text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 px-3 py-1 rounded-full">
                {t("funnel.overallConversionRate")}: {overallConversionRate}%
              </span>
            </div>

            <div className="space-y-5 max-w-3xl mx-auto py-2">
              {funnelData.map((stage, idx) => {
                const widthPct = Math.max(Math.round((stage.value / maxVal) * 100), 12);
                const prevVal = idx > 0 ? funnelData[idx - 1].value : null;
                const stageConversion =
                  prevVal && prevVal > 0 ? ((stage.value / prevVal) * 100).toFixed(1) : null;

                return (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-gray-800 dark:text-gray-200">
                        {idx + 1}. {stage.title}
                      </span>
                      <div className="flex items-center gap-3">
                        {stageConversion && (
                          <span className="text-gray-400 text-[11px]">
                            {t("funnel.retentionRate")}: <span className="font-medium text-gray-700 dark:text-gray-300">{stageConversion}%</span>
                          </span>
                        )}
                        <span className="font-bold text-gray-900 dark:text-white">{stage.value}</span>
                      </div>
                    </div>

                    <div className="h-9 w-full bg-gray-100 dark:bg-gray-800 rounded-xl overflow-hidden p-1">
                      <div
                        className="h-full rounded-lg transition-all duration-500 flex items-center justify-end pr-3 text-[11px] font-bold text-white shadow-sm"
                        style={{
                          width: `${stage.value === 0 ? 8 : widthPct}%`,
                          backgroundColor: stage.color || "#3B82F6",
                        }}
                      >
                        {stage.value > 0 && `${stage.value}`}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 3. Content for POINT OF SALE (POS) */}
      {(pageName === "point-of-sale" || pageName === "pos") && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
              <span className="text-xs font-medium text-gray-500">{t("pos.profiles")}</span>
              <div className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {posProfiles.length}
              </div>
              <p className="mt-1 text-[11px] text-gray-400">{t("pos.registeredRegisters")}</p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
              <span className="text-xs font-medium text-gray-500">{t("pos.totalInvoices")}</span>
              <div className="mt-2 text-2xl font-bold text-brand-500">
                {posInvoicesCount}
              </div>
              <p className="mt-1 text-[11px] text-gray-400">{t("pos.issuedInvoices")}</p>
            </div>

            <div className="rounded-2xl border border-brand-200 bg-brand-50/50 p-5 shadow-theme-xs dark:border-brand-500/20 dark:bg-brand-500/5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-brand-700 dark:text-brand-300">{t("pos.title")}</span>
                <p className="mt-1 text-xs text-brand-600/80 dark:text-brand-400">{t("pos.subtitle")}</p>
              </div>
              <button
                onClick={() => navigate("/app/POS%20Invoice/new")}
                className="mt-3 inline-flex h-9 items-center justify-center rounded-xl bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] px-4 text-xs font-semibold text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98] transition-all"
              >
                {t("pos.createInvoice")}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-4">
              <h2 className="text-sm font-bold text-gray-900 dark:text-white">{t("pos.posProfilesList")}</h2>
              <button
                onClick={() => navigate("/app/POS%20Profile/new")}
                className="text-xs font-medium text-[#1E63B7] hover:underline"
              >
                {t("pos.addProfile")}
              </button>
            </div>

            {posProfiles.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-400">
                {t("pos.noProfilesFound")}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {posProfiles.map((p) => (
                  <div
                    key={p.name}
                    onClick={() => navigate(`/app/POS%20Profile/${encodeURIComponent(p.name)}`)}
                    className="p-4 rounded-xl border border-gray-200 hover:border-[#1E63B7] hover:bg-[#E8F2FB]/30 dark:border-gray-800 cursor-pointer transition-colors space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-900 dark:text-white">{p.name}</span>
                      <span className="text-[10px] bg-[#E8F2FB] text-[#1E63B7] px-2 py-0.5 rounded font-semibold">
                        {p.company}
                      </span>
                    </div>
                    <div className="text-[11px] text-gray-500">
                      {t("pos.warehouse")}: {p.warehouse || "Default"} | {t("pos.priceList")}: {p.selling_price_list || "Standard Selling"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. Content for PERMISSION MANAGER */}
      {pageName === "permission-manager" && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{t("permissions.doctype")}</label>
                <select
                  value={selectedDocType}
                  onChange={(e) => {
                    setSelectedDocType(e.target.value);
                    fetchPermissionData();
                  }}
                  className="w-full rounded-lg border border-gray-300 bg-transparent py-2 px-3 text-xs text-gray-800 dark:border-gray-700 dark:text-white"
                >
                  {doctypes.map((dt) => (
                    <option key={dt} value={dt} className="dark:bg-gray-900">
                      {dt}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block font-medium text-gray-700 dark:text-gray-300">{t("permissions.role")}</label>
                <select
                  value={selectedRole}
                  onChange={(e) => {
                    setSelectedRole(e.target.value);
                    fetchPermissionData();
                  }}
                  className="w-full rounded-lg border border-gray-300 bg-transparent py-2 px-3 text-xs text-gray-800 dark:border-gray-700 dark:text-white"
                >
                  {roles.map((r) => (
                    <option key={r} value={r} className="dark:bg-gray-900">
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-4">
              <h2 className="text-sm font-bold text-gray-900 dark:text-white">
                {t("permissions.rolePermissionsFor", { role: selectedRole, doctype: selectedDocType })}
              </h2>
              <button
                onClick={() => navigate(`/app/DocType/${encodeURIComponent(selectedDocType)}`)}
                className="text-xs font-medium text-[#1E63B7] hover:underline"
              >
                {t("permissions.viewDocTypeStructure")}
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {["read", "write", "create", "delete", "submit", "cancel", "amend", "print", "email", "report"].map((perm) => (
                <div
                  key={perm}
                  className="flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900"
                >
                  <span className="capitalize text-gray-700 dark:text-gray-300 font-medium">{perm}</span>
                  <span className="flex size-2 rounded-full bg-success-500" />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 5. Content for GENERIC PAGE */}
      {!["sales-funnel", "point-of-sale", "pos", "permission-manager"].includes(pageName) && (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark text-center space-y-4">
          <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            <svg className="size-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-900 dark:text-white">{formatBrandText(pageDoc?.title || pageName)}</h2>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Module interface for {formatBrandText(pageDoc?.module || "ERPNext")}.
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={() => navigate(-1)}
              className="inline-flex h-9 items-center rounded-lg bg-gray-100 px-4 text-xs font-medium text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 transition-colors"
            >
              {t("common.goBack")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
