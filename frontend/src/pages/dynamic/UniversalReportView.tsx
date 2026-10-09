import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import dayjs from "dayjs";
import Button from "../../components/ui/button/Button";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "../../components/ui/table";

interface ReportColumn {
  label: string;
  fieldname: string;
  fieldtype: string;
  width?: number | string;
  options?: string;
  hidden?: number;
}

interface FilterDef {
  fieldname: string;
  label: string;
  fieldtype: string;
  options: string[];
  default?: any;
}

function parseReportFilters(script: string) {
  const filters: Record<string, any> = {};
  const filterDefinitions: FilterDef[] = [];
  if (!script) return { filters, filterDefinitions };

  const parts = script.split(/fieldname\s*:\s*["']/);
  for (let i = 1; i < parts.length; i++) {
    const part = parts[i];
    const fnMatch = part.match(/^([^"']+)/);
    if (!fnMatch) continue;
    const fn = fnMatch[1];

    const objText = part.slice(0, 1200);

    const defaultMatch = objText.match(/default\s*:\s*(?:["']([^"']+)["']|([0-9.]+)|(true|false))/i);
    const optionsArrayMatch = objText.match(/options\s*:\s*\[([^\]]+)\]/);
    const optionsStrMatch = objText.match(/options\s*:\s*["']([\s\S]*?)["']/);
    const labelMatch = objText.match(/label\s*:\s*(?:__\(["']([^"']+)["']\)|["']([^"']+)["'])/);
    const fieldtypeMatch = objText.match(/fieldtype\s*:\s*["']([^"']+)["']/);

    const fieldtype = fieldtypeMatch ? fieldtypeMatch[1] : "Data";
    let defaultVal: any = defaultMatch ? (defaultMatch[1] ?? defaultMatch[2] ?? defaultMatch[3]) : undefined;
    let options: string[] = [];

    if (fieldtype === "Select") {
      if (optionsArrayMatch) {
        options = optionsArrayMatch[1]
          .split(",")
          .map((s) => s.replace(/["'\s]/g, ""))
          .filter(Boolean);
        if (defaultVal === undefined && options.length > 0) defaultVal = options[0];
      } else if (optionsStrMatch) {
        options = optionsStrMatch[1]
          .split(/\n|\\n/)
          .map((s) => s.trim())
          .filter(Boolean);
        if (defaultVal === undefined && options.length > 0) defaultVal = options[0];
      }
    } else if (fieldtype === "Int" || fieldtype === "Check") {
      if (defaultVal !== undefined) {
        defaultVal = parseInt(String(defaultVal), 10);
        if (isNaN(defaultVal)) defaultVal = 0;
      }
    } else if (fieldtype === "Float" || fieldtype === "Currency") {
      if (defaultVal !== undefined) {
        defaultVal = parseFloat(String(defaultVal));
        if (isNaN(defaultVal)) defaultVal = 0;
      }
    }

    if (defaultVal !== undefined) {
      filters[fn] = defaultVal;
    }

    if (!["company", "from_date", "to_date", "fiscal_year"].includes(fn)) {
      filterDefinitions.push({
        fieldname: fn,
        label: labelMatch ? labelMatch[1] || labelMatch[2] : fn,
        fieldtype,
        options,
        default: defaultVal,
      });
    }
  }

  // Safety fallback for common ERPNext CRM reports
  if (filters["lead_age"] === undefined) {
    filters["lead_age"] = 60;
  }

  return { filters, filterDefinitions };
}

export const UniversalReportView: React.FC = () => {
  const { reportName: rawReportName } = useParams<{ reportName: string }>();
  const reportName = rawReportName ? decodeURIComponent(rawReportName) : "";
  const navigate = useNavigate();

  const [columns, setColumns] = useState<ReportColumn[]>([]);
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Lists for standard filters
  const [companies, setCompanies] = useState<string[]>([]);
  const [fiscalYears, setFiscalYears] = useState<string[]>([]);

  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [selectedFiscalYear, setSelectedFiscalYear] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>(dayjs().startOf("year").format("YYYY-MM-DD"));
  const [toDate, setToDate] = useState<string>(dayjs().endOf("year").format("YYYY-MM-DD"));

  // Dynamic Report Filters
  const [dynamicFilterDefs, setDynamicFilterDefs] = useState<FilterDef[]>([]);
  const [dynamicFilterValues, setDynamicFilterValues] = useState<Record<string, any>>({});

  // 1. Fetch Company, Fiscal Year and Report Script
  useEffect(() => {
    Promise.all([
      axios.get("/api/resource/Company?limit_page_length=100"),
      axios.get("/api/resource/Fiscal Year?limit_page_length=50"),
      axios.post("/api/method/frappe.desk.query_report.get_script", { report_name: reportName }),
    ])
      .then(([compRes, fyRes, scriptRes]) => {
        const compList = (compRes.data?.data || []).map((c: any) => c.name);
        const fyList = (fyRes.data?.data || []).map((f: any) => f.name);
        setCompanies(compList);
        setFiscalYears(fyList);

        const defaultCompany =
          compList.find((c: string) => c.includes("Demo")) || compList[0] || "Lotus-fin";
        const currentYear = new Date().getFullYear();
        const defaultFy =
          fyList.find((f: string) => f.includes(String(currentYear))) ||
          fyList[0] ||
          "2026";

        setSelectedCompany(defaultCompany);
        setSelectedFiscalYear(defaultFy);

        const { filters: extractedFilters, filterDefinitions } = parseReportFilters(
          scriptRes.data?.message?.script || ""
        );
        setDynamicFilterDefs(filterDefinitions);
        setDynamicFilterValues(extractedFilters);

        executeReport({
          company: defaultCompany,
          fiscal_year: defaultFy,
          from_date: fromDate,
          to_date: toDate,
          ...extractedFilters,
        }, filterDefinitions);
      })
      .catch((err) => {
        console.error("Error loading report metadata:", err);
        executeReport({
          company: "Lotus-fin (Demo)",
          fiscal_year: "2026",
          from_date: "2025-01-01",
          to_date: "2026-12-31",
          periodicity: "Yearly",
          group_by: "Invoice",
          based_on: "Cost Center",
          lead_age: 60,
        });
      });
  }, [reportName]);

  // 2. Report Execution
  const executeReport = async (filters: any, currentDefs?: FilterDef[]) => {
    if (!reportName) return;
    setLoading(true);
    setError(null);

    const activeDefs = currentDefs || dynamicFilterDefs;

    const rawCombinedFilters: Record<string, any> = {
      company: selectedCompany || "Lotus-fin (Demo)",
      fiscal_year: selectedFiscalYear || "2026",
      from_date: fromDate,
      to_date: toDate,
      periodicity: "Yearly",
      group_by: "Invoice",
      based_on: "Cost Center",
      order_by: "Delivery Date",
      range: "Monthly",
      status: "Open",
      chart_type: "Bar",
      lead_age: 60,
      ...dynamicFilterValues,
      ...filters,
    };

    // Sanitize and type-cast for Python backend compatibility
    const sanitizedFilters: Record<string, any> = {};
    for (const [key, val] of Object.entries(rawCombinedFilters)) {
      if (val === undefined || val === null) continue;

      const def = activeDefs.find((d) => d.fieldname === key);
      if (def) {
        if (def.fieldtype === "Int" || def.fieldtype === "Check") {
          sanitizedFilters[key] = parseInt(String(val), 10) || 0;
          continue;
        }
        if (def.fieldtype === "Float" || def.fieldtype === "Currency") {
          sanitizedFilters[key] = parseFloat(String(val)) || 0;
          continue;
        }
      }

      if (key === "lead_age" || key === "age" || key === "days") {
        sanitizedFilters[key] = parseInt(String(val), 10) || 60;
        continue;
      }

      sanitizedFilters[key] = val;
    }

    try {
      const res = await axios.post("/api/method/frappe.desk.query_report.run", {
        report_name: reportName,
        filters: sanitizedFilters,
      });

      const message = res.data?.message;
      if (!message) {
        throw new Error("No data returned from report execution.");
      }

      const cols: ReportColumn[] = (message.columns || []).map((col: any) => {
        if (typeof col === "string") {
          const parts = col.split(":");
          return {
            label: parts[0] || col,
            fieldname: (parts[0] || col).toLowerCase().replace(/\s+/g, "_"),
            fieldtype: parts[1] || "Data",
            width: parts[2] ? parseInt(parts[2]) : undefined,
          };
        }
        return col;
      });

      setColumns(cols.filter((c) => !c.hidden));
      setDataSource(message.result || []);
    } catch (err: any) {
      console.error(`Report execution error for ${reportName}:`, err);
      let errMsg =
        err.response?.data?.message ||
        err.response?.data?.exc ||
        err.message ||
        `Error executing report "${reportName}"`;

      if (err.response?.data?._server_messages) {
        try {
          const smsgs = JSON.parse(err.response.data._server_messages);
          const first = JSON.parse(smsgs[0]);
          if (first?.message) {
            errMsg = first.message.replace(/<[^>]+>/g, "");
          }
        } catch (_) {}
      }

      if (typeof errMsg === "string" && errMsg.includes("Traceback (most recent call last)")) {
        const lines = errMsg.trim().split("\n");
        const lastLine = lines[lines.length - 1] || "";
        errMsg = lastLine.replace(/["\\]/g, "");
      }

      setError(typeof errMsg === "string" ? errMsg : JSON.stringify(errMsg));
    } finally {
      setLoading(false);
    }
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeReport({
      company: selectedCompany,
      fiscal_year: selectedFiscalYear,
      from_date: fromDate,
      to_date: toDate,
      ...dynamicFilterValues,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-stroke bg-white text-black shadow-card-2 hover:bg-gray dark:border-strokedark dark:bg-boxdark dark:text-white"
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-black dark:text-white tracking-tight">
              {reportName}
            </h1>
            <p className="text-xs text-bodydark2">Financial & Operational Management Report (Script & Query Report)</p>
          </div>
        </div>

        <Button
          size="sm"
          onClick={() => {
            executeReport({
              company: selectedCompany,
              fiscal_year: selectedFiscalYear,
              from_date: fromDate,
              to_date: toDate,
            });
          }}
          disabled={loading}
          startIcon={
            <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          }
        >
          {loading ? "Loading..." : "Refresh Data"}
        </Button>
      </div>

      {/* TailAdmin Filter Toolbar */}
      <div className="rounded-2xl border border-stroke bg-white p-5 shadow-default dark:border-strokedark dark:bg-boxdark">
        <form onSubmit={handleFilterSubmit} className="flex flex-wrap items-center gap-4">
          {/* Company */}
          <div className="w-full sm:w-auto flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs font-medium text-black dark:text-white">
              Company
            </label>
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
            >
              {companies.map((c) => (
                <option key={c} value={c} className="dark:bg-boxdark">
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Fiscal Year */}
          <div className="w-full sm:w-auto min-w-[140px]">
            <label className="mb-1 block text-xs font-medium text-black dark:text-white">
              Fiscal Year
            </label>
            <select
              value={selectedFiscalYear}
              onChange={(e) => setSelectedFiscalYear(e.target.value)}
              className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
            >
              {fiscalYears.map((fy) => (
                <option key={fy} value={fy} className="dark:bg-boxdark">
                  {fy}
                </option>
              ))}
            </select>
          </div>

          {/* From Date */}
          <div className="w-full sm:w-auto min-w-[140px]">
            <label className="mb-1 block text-xs font-medium text-black dark:text-white">
              From Date
            </label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
            />
          </div>

          {/* To Date */}
          <div className="w-full sm:w-auto min-w-[140px]">
            <label className="mb-1 block text-xs font-medium text-black dark:text-white">
              To Date
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
            />
          </div>

          {/* Dynamic Report Filters (Select, Number, Check, Data) */}
          {dynamicFilterDefs.map((filter) => {
            if (filter.fieldtype === "Select" && filter.options.length > 0) {
              return (
                <div key={filter.fieldname} className="w-full sm:w-auto min-w-[140px]">
                  <label className="mb-1 block text-xs font-medium text-black dark:text-white">
                    {filter.label}
                  </label>
                  <select
                    value={dynamicFilterValues[filter.fieldname] ?? filter.default ?? filter.options[0]}
                    onChange={(e) =>
                      setDynamicFilterValues((prev) => ({
                        ...prev,
                        [filter.fieldname]: e.target.value,
                      }))
                    }
                    className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
                  >
                    {filter.options.map((opt) => (
                      <option key={opt} value={opt} className="dark:bg-boxdark">
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>
              );
            }

            if (filter.fieldtype === "Int" || filter.fieldtype === "Float" || filter.fieldtype === "Currency") {
              return (
                <div key={filter.fieldname} className="w-full sm:w-auto min-w-[120px]">
                  <label className="mb-1 block text-xs font-medium text-black dark:text-white">
                    {filter.label}
                  </label>
                  <input
                    type="number"
                    value={dynamicFilterValues[filter.fieldname] ?? filter.default ?? 0}
                    onChange={(e) => {
                      const val = filter.fieldtype === "Int" ? parseInt(e.target.value, 10) : parseFloat(e.target.value);
                      setDynamicFilterValues((prev) => ({
                        ...prev,
                        [filter.fieldname]: isNaN(val) ? 0 : val,
                      }));
                    }}
                    className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
                  />
                </div>
              );
            }

            if (filter.fieldtype === "Check") {
              return (
                <div key={filter.fieldname} className="w-full sm:w-auto flex items-center gap-2 pt-5">
                  <input
                    type="checkbox"
                    id={`filter-${filter.fieldname}`}
                    checked={Boolean(dynamicFilterValues[filter.fieldname] ?? filter.default)}
                    onChange={(e) =>
                      setDynamicFilterValues((prev) => ({
                        ...prev,
                        [filter.fieldname]: e.target.checked ? 1 : 0,
                      }))
                    }
                    className="rounded border-stroke text-primary focus:ring-primary dark:border-strokedark"
                  />
                  <label htmlFor={`filter-${filter.fieldname}`} className="text-xs font-medium text-black dark:text-white cursor-pointer">
                    {filter.label}
                  </label>
                </div>
              );
            }

            return (
              <div key={filter.fieldname} className="w-full sm:w-auto min-w-[140px]">
                <label className="mb-1 block text-xs font-medium text-black dark:text-white">
                  {filter.label}
                </label>
                <input
                  type="text"
                  value={dynamicFilterValues[filter.fieldname] ?? filter.default ?? ""}
                  onChange={(e) =>
                    setDynamicFilterValues((prev) => ({
                      ...prev,
                      [filter.fieldname]: e.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-stroke bg-transparent py-2 px-3 text-xs text-black focus:border-primary focus:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white"
                />
              </div>
            );
          })}

          {/* Submit Button */}
          <div className="w-full sm:w-auto self-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] py-2 px-5 text-xs font-semibold text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98] transition-all"
            >
              Filter Results
            </button>
          </div>
        </form>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-2xl border border-warning/30 bg-warning/10 p-4 text-xs text-warning dark:border-warning/20">
          <span className="font-semibold">Report Message:</span> {error}
        </div>
      )}

      {/* TailAdmin Dynamic Report Table */}
      <div className="overflow-hidden rounded-2xl border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
        <div className="max-w-full overflow-x-auto max-h-[600px] overflow-y-auto">
          <Table>
            <TableHeader className="sticky top-0 z-10 border-b border-stroke bg-gray-2 dark:border-strokedark dark:bg-meta-4">
              <TableRow>
                {columns.map((col) => (
                  <TableCell
                    key={col.fieldname}
                    isHeader
                    className="px-4 py-3.5 text-start text-xs font-semibold text-black dark:text-white whitespace-nowrap"
                  >
                    {col.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHeader>

            <TableBody className="divide-y divide-stroke dark:divide-strokedark">
              {loading ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length || 1}
                    className="px-4 py-12 text-center text-xs text-bodydark2"
                  >
                    Loading report data...
                  </TableCell>
                </TableRow>
              ) : dataSource.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length || 1}
                    className="px-4 py-12 text-center text-xs text-bodydark2"
                  >
                    No records found for the selected criteria.
                  </TableCell>
                </TableRow>
              ) : (
                dataSource.map((record, index) => {
                  const isTotal =
                    record.account?.includes("Total") ||
                    record.account?.includes("Opening") ||
                    record.account?.includes("Closing");

                  return (
                    <TableRow
                      key={record.name || record.gl_entry || `row-${index}`}
                      className={`hover:bg-gray-2/50 dark:hover:bg-strokedark/30 transition-colors ${
                        isTotal
                          ? "bg-gray-2/70 dark:bg-meta-4/60 font-semibold"
                          : ""
                      }`}
                    >
                      {columns.map((col) => {
                        const val = record[col.fieldname];
                        const isCurrency = col.fieldtype === "Currency" || col.fieldtype === "Float";
                        const num = Number(val);

                        return (
                          <TableCell
                            key={col.fieldname}
                            className="px-4 py-2.5 text-start text-xs text-black dark:text-bodydark whitespace-nowrap"
                          >
                            {val === null || val === undefined || val === "" ? (
                              <span className="text-bodydark2">-</span>
                            ) : isCurrency && !isNaN(num) ? (
                              <span
                                className={`font-mono ${
                                  num < 0 ? "text-danger" : isTotal ? "font-bold text-black dark:text-white" : ""
                                }`}
                              >
                                {num.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                              </span>
                            ) : col.fieldtype === "Link" && typeof val === "string" && col.options ? (
                              <span
                                onClick={() => navigate(`/app/${encodeURIComponent(col.options || "")}/${encodeURIComponent(val)}`)}
                                className="text-[#1E63B7] hover:underline cursor-pointer"
                              >
                                {val}
                              </span>
                            ) : (
                              <span>{String(val)}</span>
                            )}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Footer Summary */}
        <div className="border-t border-stroke px-5 py-3 text-xs text-bodydark2 dark:border-strokedark">
          Total: <span className="font-semibold text-black dark:text-white">{dataSource.length}</span> records
        </div>
      </div>
    </div>
  );
};
