import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Badge from "../../components/ui/badge/Badge";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "../../components/ui/table";
import { FieldMeta } from "../../engine/RefineComponentRegistry";
import { TailAdminEmptyState } from "../../components/tailadmin/EmptyState";
import { useTranslation } from "../../i18n";

interface FilterCondition {
  field: string;
  operator: string;
  value: any;
}

// Global in-memory cache for DocType schemas & records
const schemaCache = new Map<string, { fields: FieldMeta[]; title_field?: string }>();
const recordsCache = new Map<string, { records: any[]; totalCount: number }>();

export const UniversalListView: React.FC = () => {
  const { t } = useTranslation();
  const { doctype: rawDocType } = useParams<{ doctype: string }>();
  const doctype = rawDocType ? decodeURIComponent(rawDocType) : "";
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const pageTitle = searchParams.get("title") || doctype;

  const [schema, setSchema] = useState<{ fields: FieldMeta[]; title_field?: string } | null>(
    () => (doctype && schemaCache.has(doctype) ? schemaCache.get(doctype)! : null)
  );
  const [loadingSchema, setLoadingSchema] = useState(!schemaCache.has(doctype));
  const [schemaError, setSchemaError] = useState<string | null>(null);

  // Dữ liệu bảng nạp độc lập từ API (với SWR In-Memory Cache)
  const initialCacheKey = `${doctype}::1::10::::::::${searchParams.toString()}`;
  const initialCached = recordsCache.get(initialCacheKey);

  const [records, setRecords] = useState<any[]>(initialCached?.records || []);
  const [totalCount, setTotalCount] = useState<number>(initialCached?.totalCount || 0);
  const [loadingData, setLoadingData] = useState<boolean>(!initialCached);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Tìm kiếm nhanh & Bộ lọc
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [showFilterPanel, setShowFilterPanel] = useState<boolean>(false);
  const [filterValues, setFilterValues] = useState<Record<string, any>>({});
  const [customFilters, setCustomFilters] = useState<FilterCondition[]>([]);
  const [showAdvancedModal, setShowAdvancedModal] = useState<boolean>(false);
  const [tempCustomFilters, setTempCustomFilters] = useState<FilterCondition[]>([]);

  // Sắp xếp
  const [sortField, setSortField] = useState<string>("creation");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Chọn dòng (Bulk Selection)
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());

  // Menu dòng (...)
  const [openRowMenu, setOpenRowMenu] = useState<string | null>(null);
  const rowMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (rowMenuRef.current && !rowMenuRef.current.contains(e.target as Node)) {
        setOpenRowMenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 1. Tải Metadata Schema từ Frappe API (với SWR In-Memory Cache)
  useEffect(() => {
    if (!doctype) return;

    if (schemaCache.has(doctype)) {
      setSchema(schemaCache.get(doctype)!);
      setLoadingSchema(false);
    } else {
      setLoadingSchema(true);
    }

    setSchemaError(null);
    setFilterValues({});
    setCustomFilters([]);
    setSearchTerm("");
    setSelectedRows(new Set());
    setCurrentPage(1);

    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(doctype)}`)
      .then((res) => {
        const docList = res.data?.docs || [];
        const currentDoc = docList.find((d: any) => d.name === doctype) || docList[0];
        if (currentDoc) {
          // Nếu là Single DocType (như Accounts Settings, System Settings, POS Settings...) -> Chuyển trực tiếp sang Form View!
          if (currentDoc.issingle) {
            navigate(`/app/${encodeURIComponent(doctype)}/${encodeURIComponent(doctype)}`, { replace: true });
            return;
          }
          schemaCache.set(doctype, currentDoc);
          setSchema(currentDoc);
        } else {
          setSchemaError(`DocType definition not found for "${doctype}"`);
        }
      })
      .catch(async (err) => {
        try {
          const reportCheck = await axios.get(`/api/resource/Report/${encodeURIComponent(doctype)}`);
          if (reportCheck.data?.data) {
            navigate(`/report/${encodeURIComponent(doctype)}`, { replace: true });
            return;
          }
        } catch (_) {}

        try {
          const pageCheck = await axios.get(`/api/resource/Page/${encodeURIComponent(doctype)}`);
          if (pageCheck.data?.data) {
            navigate(`/page/${encodeURIComponent(doctype)}`, { replace: true });
            return;
          }
        } catch (_) {}

        // Fallback for DocTypes ending with " Settings" (like Repost Accounting Ledger Settings -> Repost Accounting Ledger)
        if (doctype.endsWith(" Settings")) {
          const fallbackName = doctype.replace(/ Settings$/, "");
          try {
            const fallbackCheck = await axios.get(
              `/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(fallbackName)}`
            );
            if (fallbackCheck.data?.docs) {
              navigate(`/app/${encodeURIComponent(fallbackName)}`, { replace: true });
              return;
            }
          } catch (_) {}
        }

        setSchemaError(err.response?.data?.message || `Error loading schema for DocType "${doctype}"`);
      })
      .finally(() => {
        setLoadingSchema(false);
      });
  }, [doctype]);

  // 2. Tải Dữ liệu bản ghi thực tế từ Frappe REST API kèm Filters & Sort
  const fetchRecords = async (page: number, size: number) => {
    if (!doctype) return;

    const cacheKey = `${doctype}::${page}::${size}::${searchTerm}::${JSON.stringify(filterValues)}::${JSON.stringify(customFilters)}::${sortField}::${sortOrder}::${searchParams.toString()}`;
    if (recordsCache.has(cacheKey)) {
      const cached = recordsCache.get(cacheKey)!;
      setRecords(cached.records);
      setTotalCount(cached.totalCount);
      setLoadingData(false);
    } else {
      setLoadingData(true);
    }

    const start = (page - 1) * size;
    const apiFilters: [string, string, any][] = [];

    // 2.1 URL Query Params (như is_return=1, purpose=...)
    const reservedParams = new Set(["page", "pageSize", "search", "title", "view"]);
    searchParams.forEach((value, key) => {
      if (!reservedParams.has(key)) {
        if (key === "is_return") {
          apiFilters.push([key, "=", parseInt(value, 10)]);
        } else {
          apiFilters.push([key, "=", value]);
        }
      }
    });

    // 2.2 Inline Filters
    Object.entries(filterValues).forEach(([f, val]) => {
      if (val !== "" && val !== undefined && val !== null) {
        if (f === "name") {
          apiFilters.push([f, "like", `%${val}%`]);
        } else {
          apiFilters.push([f, "=", val]);
        }
      }
    });

    // 2.3 Search Term (nếu có gõ vào ô Search)
    if (searchTerm.trim()) {
      apiFilters.push(["name", "like", `%${searchTerm.trim()}%`]);
    }

    // 2.4 Custom Advanced Filters
    customFilters.forEach((cf) => {
      if (cf.field && cf.value !== "" && cf.value !== undefined) {
        const op = cf.operator === "like" ? "like" : cf.operator;
        const v = cf.operator === "like" ? `%${cf.value}%` : cf.value;
        apiFilters.push([cf.field, op, v]);
      }
    });

    try {
      const params: any = {
        fields: '["*"]',
        limit_start: start,
        limit_page_length: size,
        order_by: `${sortField} ${sortOrder}`,
      };
      if (apiFilters.length > 0) {
        params.filters = JSON.stringify(apiFilters);
      }

      const res = await axios.get(`/api/resource/${encodeURIComponent(doctype)}`, { params });
      const items = res.data?.data || [];

      const countParams: any = { doctype };
      if (apiFilters.length > 0) {
        countParams.filters = JSON.stringify(apiFilters);
      }

      const countRes = await axios.get(`/api/method/frappe.client.get_count`, {
        params: countParams,
      });
      const count =
        typeof countRes.data?.message === "number"
          ? countRes.data?.message
          : items.length;

      setRecords(items);
      setTotalCount(count);
      recordsCache.set(cacheKey, { records: items, totalCount: count });
    } catch (err) {
      console.error("Lỗi tải dữ liệu bảng:", err);
    } finally {
      setLoadingData(false);
    }
  };

  // Immediate fetch for navigation & sorting, debounced for typing in search/filter
  const isTyping = useRef(false);
  useEffect(() => {
    if (isTyping.current) {
      const timer = setTimeout(() => {
        fetchRecords(currentPage, pageSize);
        isTyping.current = false;
      }, 250);
      return () => clearTimeout(timer);
    } else {
      fetchRecords(currentPage, pageSize);
    }
  }, [doctype, searchParams, searchTerm, filterValues, customFilters, sortField, sortOrder, currentPage, pageSize]);

  // Đổi thứ tự sắp xếp theo cột
  const handleSortColumn = (field: string) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
    setCurrentPage(1);
  };

  // Xuất CSV
  const handleExportCsv = () => {
    if (records.length === 0) return;

    const exportData = selectedRows.size > 0
      ? records.filter((r) => selectedRows.has(r.name))
      : records;

    const visibleFields = listFields.map((f) => f.fieldname);
    const headers = ["ID / Name", ...listFields.map((f) => f.label || f.fieldname)];

    const csvRows: string[] = [headers.join(",")];

    exportData.forEach((row) => {
      const values = [
        `"${row.name || ""}"`,
        ...visibleFields.map((f) => `"${(row[f] ?? "").toString().replace(/"/g, '""')}"`),
      ];
      csvRows.push(values.join(","));
    });

    const csvContent = "\uFEFF" + csvRows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${doctype}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Xóa hàng loạt
  const handleBulkDelete = async () => {
    if (selectedRows.size === 0) return;
    const confirmDelete = window.confirm(
      t("common.bulkDeleteConfirm", { count: selectedRows.size })
    );
    if (!confirmDelete) return;

    setLoadingData(true);
    try {
      for (const name of Array.from(selectedRows)) {
        await axios.delete(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`);
      }
      setSelectedRows(new Set());
      fetchRecords(currentPage, pageSize);
    } catch (err: any) {
      alert(`${t("common.error")}: ${err.response?.data?.message || err.message}`);
    } finally {
      setLoadingData(false);
    }
  };

  const toggleSelectAll = () => {
    if (selectedRows.size === records.length && records.length > 0) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(records.map((r) => r.name)));
    }
  };

  const toggleSelectRow = (name: string) => {
    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const activeFilterCount =
    Object.values(filterValues).filter((v) => v !== "" && v !== undefined).length +
    customFilters.length +
    (searchTerm ? 1 : 0);

  if (loadingSchema && !schema) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
          <div className="h-4 w-32 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-5">
          <div className="flex justify-between items-center pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="space-y-2">
              <div className="h-5 w-40 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
              <div className="h-3 w-64 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
            </div>
            <div className="h-9 w-28 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
          </div>
          <div className="space-y-3 pt-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 w-full bg-gray-50 dark:bg-gray-800/50 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (schemaError) {
    return (
      <div className="rounded-2xl border border-error-500/20 bg-error-50 p-6 text-center dark:bg-error-500/10">
        <h3 className="text-sm font-semibold text-error-600">{t("common.schemaError")}</h3>
        <p className="mt-1 text-xs text-gray-500">{schemaError}</p>
      </div>
    );
  }

  const nonFilterableTypes = new Set([
    "Section Break",
    "Column Break",
    "Tab Break",
    "Fold",
    "Heading",
    "HTML",
    "Table",
    "Table MultiSelect",
    "Button",
    "Image",
    "Barcode",
    "Password",
    "Attach",
    "Attach Image",
  ]);

  const filterableFields: { fieldname: string; label: string }[] = [
    { fieldname: "name", label: `${t("common.nameOrId")} (name)` },
    ...(schema?.fields || [])
      .filter((f: any) => !f.hidden && f.fieldname && !nonFilterableTypes.has(f.fieldtype))
      .map((f: any) => ({
        fieldname: f.fieldname,
        label: f.label ? `${f.label} (${f.fieldname})` : f.fieldname,
      })),
  ];

  const standardFilterFields = (schema?.fields || []).filter(
    (f: any) =>
      !f.hidden &&
      f.fieldname &&
      !nonFilterableTypes.has(f.fieldtype) &&
      (f.in_standard_filter ||
        ["status", "company", "customer", "supplier", "posting_date"].includes(f.fieldname))
  );

  const titleFieldName = schema?.title_field;

  let listFields = (schema?.fields || []).filter(
    (f: any) =>
      !f.hidden &&
      !["Section Break", "Column Break", "Table", "HTML", "Password"].includes(f.fieldtype) &&
      (f.in_list_view || f.fieldname === titleFieldName)
  );

  if (listFields.length === 0) {
    const ignoredFields = new Set([
      "naming_series",
      "amended_from",
      "conversion_factor",
      "currency",
      "price_list_currency",
      "plc_conversion_rate",
      "price_list",
    ]);
    listFields = (schema?.fields || [])
      .filter(
        (f: any) =>
          !f.hidden &&
          !ignoredFields.has(f.fieldname) &&
          !["Section Break", "Column Break", "Table", "HTML", "Password"].includes(f.fieldtype)
      )
      .slice(0, 5);
  }

  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const isAllSelected = records.length > 0 && selectedRows.size === records.length;

  return (
    <div className="space-y-6">
      {/* 1. Top Page Header (Outside Card) */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
          {pageTitle}
        </h1>
        <div className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1.5">
          <span className="hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer" onClick={() => navigate("/home")}>
            {t("common.home")}
          </span>
          <span>&gt;</span>
          <span className="text-gray-600 dark:text-gray-300 font-medium">{pageTitle}</span>
        </div>
      </div>

      {/* 2. Single Unified White Card (Exact TailAdmin Product List Style) */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark space-y-5">
        {/* 2.1 Card Header (Title & Actions) */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              {pageTitle}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {t("workspace.manageAndLookUp", { name: pageTitle })}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Export Button */}
            <button
              onClick={handleExportCsv}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-gray-300 bg-white px-4 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
            >
              <span>{t("common.export")}</span>
              <svg className="size-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>

            {/* Primary Add Button */}
            <button
              onClick={() => navigate(`/app/${encodeURIComponent(doctype || "")}/new`)}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-500 px-4 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 transition-colors"
            >
              <svg className="size-4 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
              <span>{t("common.addNew", { name: pageTitle })}</span>
            </button>
          </div>
        </div>

        {/* 2.2 Toolbar (Search Input on left, Filter Toggle Button on right) */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
          {/* Search Box */}
          <div className="relative flex-1 max-w-sm">
            <input
              type="text"
              placeholder={`${t("common.search")}...`}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full rounded-lg border border-gray-200 bg-white py-2.5 pl-9 pr-4 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder-gray-500 transition-colors"
            />
            <span className="absolute left-3 top-3 text-gray-400">
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Filter Toggle Button */}
            <button
              onClick={() => setShowFilterPanel((p) => !p)}
              className={`inline-flex h-10 items-center gap-2 rounded-lg border px-3.5 text-xs font-medium transition-colors ${
                showFilterPanel || activeFilterCount > 0
                  ? "border-brand-500 bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"
                  : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              }`}
            >
              <svg className="size-4 fill-current" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
              </svg>
              <span>{t("common.filters")}</span>
              {activeFilterCount > 0 && (
                <span className="flex size-4 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* 2.3 Collapsible Filter Panel */}
        {showFilterPanel && (
          <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-800/40 animate-in fade-in duration-150">
            <div className="flex flex-wrap items-center gap-3">
              {standardFilterFields.map((field) => {
                if (field.fieldtype === "Select" && field.options) {
                  const options = typeof field.options === "string" ? field.options.split("\n").filter(Boolean) : [];
                  return (
                    <div key={field.fieldname} className="min-w-[150px]">
                      <select
                        value={filterValues[field.fieldname] || ""}
                        onChange={(e) => {
                          setFilterValues((p) => ({ ...p, [field.fieldname]: e.target.value }));
                          setCurrentPage(1);
                        }}
                        className="h-9 w-full rounded-lg border border-gray-300 bg-white px-3 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                      >
                        <option value="">{field.label}: {t("common.total")}</option>
                        {options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                }

                if (field.fieldtype === "Date") {
                  return (
                    <div key={field.fieldname} className="min-w-[140px]">
                      <input
                        type="date"
                        title={field.label}
                        value={filterValues[field.fieldname] || ""}
                        onChange={(e) => {
                          setFilterValues((p) => ({ ...p, [field.fieldname]: e.target.value }));
                          setCurrentPage(1);
                        }}
                        className="h-9 w-full rounded-lg border border-gray-300 bg-white px-3 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                      />
                    </div>
                  );
                }

                return (
                  <div key={field.fieldname} className="min-w-[150px]">
                    <input
                      type="text"
                      placeholder={`${field.label}...`}
                      value={filterValues[field.fieldname] || ""}
                      onChange={(e) => {
                        setFilterValues((p) => ({ ...p, [field.fieldname]: e.target.value }));
                        setCurrentPage(1);
                      }}
                      className="h-9 w-full rounded-lg border border-gray-300 bg-white px-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                    />
                  </div>
                );
              })}

              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => {
                    setFilterValues({});
                    setCustomFilters([]);
                    setSearchTerm("");
                    setCurrentPage(1);
                  }}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
                >
                  {t("common.clearFilters")}
                </button>
                <button
                  onClick={() => {
                    setTempCustomFilters(
                      customFilters.length > 0
                        ? [...customFilters]
                        : [{ field: filterableFields[0]?.fieldname || "name", operator: "=", value: "" }]
                    );
                    setShowAdvancedModal(true);
                  }}
                  className="rounded-lg bg-gray-900 px-3 py-2 text-xs font-medium text-white hover:bg-black dark:bg-brand-500 dark:hover:bg-brand-600 transition-colors"
                >
                  {t("filter.addCondition")}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 2.4 Clean Table (Exact TailAdmin BasicTableOne Flush Style) */}
        <div className="max-w-full overflow-x-auto">
          <Table className="min-w-full">
            {/* Table Header: Clean, border-b only, no heavy gray */}
            <TableHeader className="border-b border-gray-100 dark:border-gray-800">
              <TableRow>
                {/* Row Checkbox */}
                <TableCell isHeader className="w-10 px-4 py-3.5 text-start">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={toggleSelectAll}
                    className="size-4 rounded border-gray-300 text-brand-500 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 cursor-pointer"
                  />
                </TableCell>

                {/* ID Column */}
                <TableCell
                  isHeader
                  className="px-4 py-3.5 text-start text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap cursor-pointer select-none hover:text-gray-900 dark:hover:text-white"
                  onClick={() => handleSortColumn("name")}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{t("common.nameOrId")}</span>
                    <span className="text-[10px] text-gray-400">
                      {sortField === "name" ? (sortOrder === "asc" ? "▲" : "▼") : "⇅"}
                    </span>
                  </div>
                </TableCell>

                {/* Dynamic Columns */}
                {listFields.map((field) => (
                  <TableCell
                    key={field.fieldname}
                    isHeader
                    className="px-4 py-3.5 text-start text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap cursor-pointer select-none hover:text-gray-900 dark:hover:text-white"
                    onClick={() => handleSortColumn(field.fieldname)}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{field.label || field.fieldname}</span>
                      <span className="text-[10px] text-gray-400">
                        {sortField === field.fieldname ? (sortOrder === "asc" ? "▲" : "▼") : "⇅"}
                      </span>
                    </div>
                  </TableCell>
                ))}

                {/* Actions Column */}
                <TableCell
                  isHeader
                  className="px-4 py-3.5 text-end text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap"
                >
                  {t("common.actions")}
                </TableCell>
              </TableRow>
            </TableHeader>

            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800/80">
              {loadingData && records.length === 0 ? (
                Array.from({ length: 6 }).map((_, rIdx) => (
                  <TableRow key={rIdx} className="animate-pulse">
                    <TableCell className="w-10 px-4 py-4">
                      <div className="size-4 bg-gray-200 dark:bg-gray-800 rounded" />
                    </TableCell>
                    <TableCell className="px-4 py-4">
                      <div className="h-4 w-28 bg-gray-200 dark:bg-gray-800 rounded" />
                    </TableCell>
                    {listFields.map((_, fIdx) => (
                      <TableCell key={fIdx} className="px-4 py-4">
                        <div
                          className={`h-4 bg-gray-100 dark:bg-gray-800/60 rounded ${
                            fIdx % 2 === 0 ? "w-24" : "w-16"
                          }`}
                        />
                      </TableCell>
                    ))}
                    <TableCell className="px-4 py-4 text-end">
                      <div className="size-6 bg-gray-100 dark:bg-gray-800/60 rounded-lg inline-block" />
                    </TableCell>
                  </TableRow>
                ))
              ) : records.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={listFields.length + 3}>
                    <TailAdminEmptyState
                      title={pageTitle}
                      hasFilters={activeFilterCount > 0}
                      onClearFilters={() => {
                        setFilterValues({});
                        setCustomFilters([]);
                        setSearchTerm("");
                        setCurrentPage(1);
                      }}
                      onCreateNew={() => navigate(`/app/${encodeURIComponent(doctype || "")}/new`)}
                    />
                  </TableCell>
                </TableRow>
              ) : (
                records.map((record) => {
                  const isSelected = selectedRows.has(record.name);
                  return (
                    <TableRow
                      key={record.name}
                      className={`hover:bg-gray-50/60 dark:hover:bg-white/[0.02] transition-colors ${
                        isSelected ? "bg-brand-50/20 dark:bg-brand-500/5" : ""
                      }`}
                    >
                      {/* Row Checkbox */}
                      <TableCell className="w-10 px-4 py-4 text-start">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectRow(record.name)}
                          className="size-4 rounded border-gray-300 text-brand-500 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 cursor-pointer"
                        />
                      </TableCell>

                      {/* ID / Name */}
                      <TableCell className="px-4 py-4 whitespace-nowrap text-xs font-medium text-gray-800 dark:text-white/90">
                        <span
                          onClick={() =>
                            navigate(
                              `/app/${encodeURIComponent(doctype || "")}/${encodeURIComponent(record.name)}`
                            )
                          }
                          className="cursor-pointer hover:text-brand-500 hover:underline transition-colors"
                        >
                          {record.name}
                        </span>
                      </TableCell>

                      {/* Dynamic Columns */}
                      {listFields.map((field) => {
                        const value = record[field.fieldname];
                        const isCurrency = field.fieldtype === "Currency" || field.fieldtype === "Float";
                        const num = Number(value);

                        return (
                          <TableCell
                            key={field.fieldname}
                            className="px-4 py-4 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 text-start"
                          >
                            {value === null || value === undefined || value === "" ? (
                              <span className="text-gray-300 dark:text-gray-600">-</span>
                            ) : field.fieldtype === "Check" ? (
                              <Badge color={value ? "success" : "light"} size="sm">
                                {value ? "Yes" : "No"}
                              </Badge>
                            ) : isCurrency && !isNaN(num) ? (
                              <span className="font-medium text-gray-800 dark:text-white/90">
                                {num.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                              </span>
                            ) : field.fieldtype === "Link" && typeof value === "string" && field.options ? (
                              <span
                                onClick={() =>
                                  navigate(`/app/${encodeURIComponent(field.options || "")}/${encodeURIComponent(value)}`)
                                }
                                className="text-gray-700 hover:text-brand-500 hover:underline cursor-pointer dark:text-gray-300"
                              >
                                {value}
                              </span>
                            ) : field.fieldname === "status" || field.fieldname === "workflow_state" ? (
                              <Badge
                                color={
                                  ["Paid", "Submitted", "Active", "Enabled", "Completed", "In Stock"].includes(String(value))
                                    ? "success"
                                    : ["Draft", "Pending", "Unpaid"].includes(String(value))
                                    ? "warning"
                                    : ["Overdue", "Cancelled", "Closed", "Out of Stock"].includes(String(value))
                                    ? "error"
                                    : "light"
                                }
                                size="sm"
                              >
                                {String(value)}
                              </Badge>
                            ) : (
                              <span>{String(value)}</span>
                            )}
                          </TableCell>
                        );
                      })}

                      {/* Row Action Dropdown / Button */}
                      <TableCell className="px-4 py-4 whitespace-nowrap text-end text-xs font-medium">
                        <div className="relative inline-block text-start">
                          <button
                            onClick={() => setOpenRowMenu((p) => (p === record.name ? null : record.name))}
                            className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                          >
                            <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                              <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
                            </svg>
                          </button>

                          {openRowMenu === record.name && (
                            <div
                              ref={rowMenuRef}
                              className="absolute right-0 z-40 mt-1 w-36 rounded-xl border border-gray-100 bg-white p-1.5 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900 animate-in fade-in duration-100 text-start"
                            >
                              <button
                                onClick={() => {
                                  navigate(`/app/${encodeURIComponent(doctype || "")}/${encodeURIComponent(record.name)}`);
                                  setOpenRowMenu(null);
                                }}
                                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                              >
                                {t("common.viewOrEdit")}
                              </button>
                              <button
                                onClick={async () => {
                                  if (window.confirm(t("common.deleteConfirm", { name: record.name }))) {
                                    await axios.delete(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(record.name)}`);
                                    fetchRecords(currentPage, pageSize);
                                  }
                                  setOpenRowMenu(null);
                                }}
                                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-error-600 hover:bg-error-50 dark:text-error-400 dark:hover:bg-error-500/10"
                              >
                                {t("common.deleteRecord")}
                              </button>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* 2.5 Floating Bulk Selection Toolbar */}
        {selectedRows.size > 0 && (
          <div className="sticky bottom-0 z-30 flex items-center justify-between rounded-xl border border-brand-200 bg-brand-50/95 px-5 py-3 backdrop-blur-sm dark:border-brand-500/20 dark:bg-gray-900/95 animate-in slide-in-from-bottom duration-150">
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-700 dark:text-brand-400">
              <span className="flex size-5 items-center justify-center rounded-full bg-brand-500 text-[10px] text-white">
                {selectedRows.size}
              </span>
              <span>{t("common.selectedCount", { count: selectedRows.size })}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleExportCsv}
                className="inline-flex items-center gap-1.5 rounded-lg border border-brand-300 bg-white px-3 py-1.5 text-xs font-medium text-brand-700 shadow-theme-xs hover:bg-brand-50 dark:border-brand-500/30 dark:bg-gray-800 dark:text-brand-300"
              >
                {t("common.exportCsv")}
              </button>

              <button
                onClick={handleBulkDelete}
                className="inline-flex items-center gap-1.5 rounded-lg bg-error-500 px-3 py-1.5 text-xs font-medium text-white shadow-theme-xs hover:bg-error-600"
              >
                {t("common.deleteSelected")}
              </button>

              <button
                onClick={() => setSelectedRows(new Set())}
                className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 px-2 cursor-pointer"
              >
                {t("common.deselect")}
              </button>
            </div>
          </div>
        )}

        {/* 2.6 TailAdmin Standard Pagination Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 text-xs text-gray-500 dark:text-gray-400">
          <div>
            {t("common.showingRecords", { count: records.length, total: totalCount })}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (currentPage > 1) setCurrentPage((p) => p - 1);
              }}
              disabled={currentPage === 1}
              className="flex h-9 items-center justify-center rounded-lg border border-gray-300 bg-white px-3.5 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 disabled:opacity-40 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-white/5 cursor-pointer disabled:cursor-not-allowed transition-colors"
            >
              {t("common.previous")}
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                .map((page, idx, arr) => (
                  <React.Fragment key={page}>
                    {idx > 0 && page - arr[idx - 1] > 1 && <span className="px-1 text-gray-400">...</span>}
                    <button
                      onClick={() => setCurrentPage(page)}
                      className={`flex h-9 w-9 items-center justify-center rounded-lg text-xs font-medium transition-colors ${
                        currentPage === page
                          ? "bg-brand-500 text-white shadow-theme-xs"
                          : "text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                      }`}
                    >
                      {page}
                    </button>
                  </React.Fragment>
                ))}
            </div>

            <button
              onClick={() => {
                if (currentPage < totalPages) setCurrentPage((p) => p + 1);
              }}
              disabled={currentPage >= totalPages}
              className="flex h-9 items-center justify-center rounded-lg border border-gray-300 bg-white px-3.5 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 disabled:opacity-40 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-white/5 cursor-pointer disabled:cursor-not-allowed transition-colors"
            >
              {t("common.next")}
            </button>
          </div>
        </div>
      </div>

      {/* Advanced Filter Modal (Clean TailAdmin Modal, No horizontal scrollbar) */}
      {showAdvancedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-2xl rounded-2xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-800 dark:bg-gray-900 animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
              <div className="flex items-center gap-2.5">
                <div className="flex size-8 items-center justify-center rounded-lg bg-brand-50 text-brand-500 dark:bg-brand-500/10">
                  <svg className="size-4 fill-current" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                    {t("filter.title")}
                  </h3>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    {t("filter.subtitle")}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowAdvancedModal(false)}
                className="flex size-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Filter Condition Rows */}
            <div className="mt-4 max-h-80 overflow-y-auto overflow-x-hidden space-y-3 pr-1">
              {tempCustomFilters.length === 0 ? (
                <div className="py-8 text-center text-xs text-gray-400">
                  {t("common.noRecordsMatch")}
                </div>
              ) : (
                tempCustomFilters.map((cond, idx) => (
                  <div key={idx} className="flex items-center gap-2.5">
                    {/* Field Selection */}
                    <select
                      value={cond.field}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTempCustomFilters((prev) =>
                          prev.map((item, i) => (i === idx ? { ...item, field: val } : item))
                        );
                      }}
                      className="h-9.5 w-52 shrink-0 rounded-lg border border-gray-300 bg-white px-3 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                    >
                      {filterableFields.map((f) => (
                        <option key={f.fieldname} value={f.fieldname}>
                          {f.label}
                        </option>
                      ))}
                    </select>

                    {/* Operator */}
                    <select
                      value={cond.operator}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTempCustomFilters((prev) =>
                          prev.map((item, i) => (i === idx ? { ...item, operator: val } : item))
                        );
                      }}
                      className="h-9.5 w-28 shrink-0 rounded-lg border border-gray-300 bg-white px-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white font-mono"
                    >
                      <option value="=">{t("filter.operators.equals")}</option>
                      <option value="like">{t("filter.operators.like")}</option>
                      <option value="!=">{t("filter.operators.notEquals")}</option>
                      <option value=">">{t("filter.operators.greaterThan")}</option>
                      <option value="<">{t("filter.operators.lessThan")}</option>
                      <option value=">=">{t("filter.operators.greaterOrEqual")}</option>
                      <option value="<=">{t("filter.operators.lessOrEqual")}</option>
                      <option value="in">{t("filter.operators.in")}</option>
                    </select>

                    {/* Value */}
                    <input
                      type="text"
                      placeholder={`${t("filter.value")}...`}
                      value={cond.value}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTempCustomFilters((prev) =>
                          prev.map((item, i) => (i === idx ? { ...item, value: val } : item))
                        );
                      }}
                      className="h-9.5 flex-1 min-w-[140px] rounded-lg border border-gray-300 bg-white px-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                    />

                    {/* Remove Condition */}
                    <button
                      onClick={() => setTempCustomFilters((prev) => prev.filter((_, i) => i !== idx))}
                      title={t("filter.removeCondition")}
                      className="flex size-9 shrink-0 items-center justify-center rounded-lg text-gray-400 hover:bg-error-50 hover:text-error-500 dark:hover:bg-error-500/10 transition-colors"
                    >
                      <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Modal Actions */}
            <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4 dark:border-gray-800">
              <button
                onClick={() =>
                  setTempCustomFilters((p) => [
                    ...p,
                    { field: filterableFields[0]?.fieldname || "name", operator: "=", value: "" },
                  ])
                }
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-500 hover:text-brand-600 transition-colors"
              >
                <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{t("filter.addCondition")}</span>
              </button>

              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => {
                    setTempCustomFilters([]);
                    setCustomFilters([]);
                    setShowAdvancedModal(false);
                  }}
                  className="rounded-lg border border-gray-300 px-3.5 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
                >
                  {t("common.reset")}
                </button>
                <button
                  onClick={() => {
                    setCustomFilters(tempCustomFilters.filter((f) => f.field && f.value !== ""));
                    setShowAdvancedModal(false);
                    setCurrentPage(1);
                  }}
                  className="rounded-lg bg-brand-500 px-4 py-2 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 transition-colors"
                >
                  {t("filter.applyFilters")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
