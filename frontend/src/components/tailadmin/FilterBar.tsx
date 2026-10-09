import React, { useState, useMemo } from "react";
import { FieldMeta } from "../../engine/RefineComponentRegistry";
import { useTranslation } from "../../i18n";
import { SortOption, buildSortOptions } from "./sortUtils";

export type { SortOption };

export interface FilterCondition {
  field: string;
  operator: string; // "=" | "!=" | "like" | ">" | "<" | ">=" | "<=" | "in"
  value: any;
}

interface FilterBarProps {
  standardFields: FieldMeta[];
  allFields: FieldMeta[];
  filterValues: Record<string, any>;
  onFilterChange: (field: string, value: any) => void;
  customFilters: FilterCondition[];
  onApplyCustomFilters: (filters: FilterCondition[]) => void;
  onClearAllFilters: () => void;
  activeFilterCount: number;
  currentSort: SortOption;
  onSortChange: (sort: SortOption) => void;
}

export const TailAdminFilterBar: React.FC<FilterBarProps> = ({
  standardFields,
  allFields,
  filterValues,
  onFilterChange,
  customFilters,
  onApplyCustomFilters,
  onClearAllFilters,
  activeFilterCount,
  currentSort,
  onSortChange,
}) => {
  const { t } = useTranslation();
  const [showAdvancedModal, setShowAdvancedModal] = useState(false);
  const [tempCustomFilters, setTempCustomFilters] = useState<FilterCondition[]>([]);

  const sortOptions = useMemo(
    () => buildSortOptions(allFields, t),
    [allFields, t]
  );

  const openAdvancedModal = () => {
    setTempCustomFilters(
      customFilters.length > 0
        ? [...customFilters]
        : [{ field: allFields[0]?.fieldname || "name", operator: "=", value: "" }]
    );
    setShowAdvancedModal(true);
  };

  const handleAddTempFilter = () => {
    setTempCustomFilters((prev) => [
      ...prev,
      { field: allFields[0]?.fieldname || "name", operator: "=", value: "" },
    ]);
  };

  const handleRemoveTempFilter = (index: number) => {
    setTempCustomFilters((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSaveAdvancedFilters = () => {
    const validFilters = tempCustomFilters.filter(
      (f) => f.field && f.value !== "" && f.value !== undefined
    );
    onApplyCustomFilters(validFilters);
    setShowAdvancedModal(false);
  };

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      {/* Inline Standard Filters */}
      {/* 1. ID Filter Pill */}
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder={`${t("common.nameOrId")}...`}
          value={filterValues["name"] || ""}
          onChange={(e) => onFilterChange("name", e.target.value)}
          className="h-8.5 rounded-lg border border-gray-200 bg-gray-50/80 px-3 pr-7 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder-gray-500 dark:focus:border-brand-500 transition-all w-32 focus:w-44"
        />
        <span className="absolute right-2.5 text-[10px] font-mono text-gray-400 select-none pointer-events-none">
          ≈
        </span>
      </div>

      {/* 2. Dynamic Standard Fields from Schema */}
      {standardFields.slice(0, 5).map((field) => {
        if (field.fieldname === "name") return null;

        if (field.fieldtype === "Select" && field.options) {
          const options = typeof field.options === "string" ? field.options.split("\n").filter(Boolean) : [];
          return (
            <div key={field.fieldname} className="relative">
              <select
                value={filterValues[field.fieldname] || ""}
                onChange={(e) => onFilterChange(field.fieldname, e.target.value)}
                className="h-8.5 rounded-lg border border-gray-200 bg-gray-50/80 pl-3 pr-8 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:focus:border-brand-500 transition-all cursor-pointer"
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
            <div key={field.fieldname} className="relative">
              <input
                type="date"
                title={field.label}
                value={filterValues[field.fieldname] || ""}
                onChange={(e) => onFilterChange(field.fieldname, e.target.value)}
                className="h-8.5 rounded-lg border border-gray-200 bg-gray-50/80 px-2.5 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:focus:border-brand-500 transition-all"
              />
            </div>
          );
        }

        // Default Data/Link field
        return (
          <div key={field.fieldname} className="relative flex items-center">
            <input
              type="text"
              placeholder={`${field.label}...`}
              value={filterValues[field.fieldname] || ""}
              onChange={(e) => onFilterChange(field.fieldname, e.target.value)}
              className="h-8.5 rounded-lg border border-gray-200 bg-gray-50/80 px-3 pr-7 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder-gray-500 dark:focus:border-brand-500 transition-all w-32 focus:w-44"
            />
            <span className="absolute right-2.5 text-[10px] font-mono text-gray-400 select-none pointer-events-none">
              ≈
            </span>
          </div>
        );
      })}

      {/* 3. Advanced Filter Button Pill */}
      <div className="flex items-center">
        <button
          onClick={openAdvancedModal}
          className={`inline-flex h-8.5 items-center gap-1.5 rounded-l-lg border border-gray-200 px-3 text-xs font-medium transition-colors ${
            activeFilterCount > 0
              ? "bg-brand-50 text-brand-600 border-brand-200 dark:bg-brand-500/15 dark:text-brand-400 dark:border-brand-500/30"
              : "bg-gray-50/80 text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800/80 dark:text-gray-300 dark:hover:bg-gray-700"
          }`}
        >
          <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z"
              clipRule="evenodd"
            />
          </svg>
          <span>{t("common.filters")}</span>
          {activeFilterCount > 0 && (
            <span className="flex size-4 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
              {activeFilterCount}
            </span>
          )}
        </button>

        {activeFilterCount > 0 && (
          <button
            onClick={onClearAllFilters}
            title={t("common.clearFilters")}
            className="flex h-8.5 items-center justify-center rounded-r-lg border border-l-0 border-brand-200 bg-brand-50 px-2 text-brand-600 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/15 dark:text-brand-400 dark:hover:bg-brand-500/25 transition-colors"
          >
            <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>

      {/* 4. Sort Selector Dropdown */}
      <div className="ml-auto flex items-center gap-1.5">
        <span className="text-xs text-gray-400 hidden sm:inline">{t("sort.sortBy")}:</span>
        <select
          value={`${currentSort.field}:${currentSort.direction}`}
          onChange={(e) => {
            const [field, direction] = e.target.value.split(":");
            const selectedOpt = sortOptions.find(
              (o) => o.field === field && o.direction === direction
            );
            if (selectedOpt) onSortChange(selectedOpt);
          }}
          className="h-8.5 rounded-lg border border-gray-200 bg-gray-50/80 pl-3 pr-8 text-xs font-medium text-gray-700 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-gray-300 dark:focus:border-brand-500 transition-all cursor-pointer"
        >
          {sortOptions.map((opt, idx) => (
            <option key={idx} value={`${opt.field}:${opt.direction}`}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Advanced Filter Modal */}
      {showAdvancedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-800 dark:bg-gray-900 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
              <div className="flex items-center gap-2">
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
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>

            {/* Filter Rows */}
            <div className="mt-4 max-h-72 overflow-y-auto space-y-3 pr-1">
              {tempCustomFilters.length === 0 ? (
                <div className="py-6 text-center text-xs text-gray-400">
                  {t("common.noRecordsMatch")}
                </div>
              ) : (
                tempCustomFilters.map((cond, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    {/* Field Selection */}
                    <select
                      value={cond.field}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTempCustomFilters((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, field: val } : item
                          )
                        );
                      }}
                      className="h-8.5 flex-1 rounded-lg border border-gray-300 bg-white px-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                    >
                      {allFields.map((f) => (
                        <option key={f.fieldname} value={f.fieldname}>
                          {f.label || f.fieldname}
                        </option>
                      ))}
                    </select>

                    {/* Operator */}
                    <select
                      value={cond.operator}
                      onChange={(e) => {
                        const val = e.target.value;
                        setTempCustomFilters((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, operator: val } : item
                          )
                        );
                      }}
                      className="h-8.5 w-28 rounded-lg border border-gray-300 bg-white px-2 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white font-mono"
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
                          prev.map((item, i) =>
                            i === idx ? { ...item, value: val } : item
                          )
                        );
                      }}
                      className="h-8.5 flex-1 rounded-lg border border-gray-300 bg-white px-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                    />

                    {/* Remove button */}
                    <button
                      onClick={() => handleRemoveTempFilter(idx)}
                      title={t("filter.removeCondition")}
                      className="flex size-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-error-500 dark:hover:bg-gray-800"
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
            <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-4 dark:border-gray-800">
              <button
                onClick={handleAddTempFilter}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1E63B7] hover:text-[#174f96] transition-colors"
              >
                <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
                {t("filter.addCondition")}
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setTempCustomFilters([]);
                    onApplyCustomFilters([]);
                    setShowAdvancedModal(false);
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
                >
                  {t("common.reset")}
                </button>
                <button
                  onClick={handleSaveAdvancedFilters}
                  className="rounded-xl bg-gradient-to-r from-[#1E63B7] via-[#6EC1F6] to-[#2FB29A] px-4 py-1.5 text-xs font-semibold text-white shadow-theme-xs hover:opacity-95 active:scale-[0.98] transition-all"
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
