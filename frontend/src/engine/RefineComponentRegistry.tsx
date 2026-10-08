import React from "react";
import { RefineLinkControl } from "./controls/RefineLinkControl";
import { SubTableControl } from "./controls/SubTableControl";

export interface FieldMeta {
  fieldname: string;
  fieldtype: string;
  label: string;
  options?: string;
  reqd?: number;
  read_only?: number;
  description?: string;
  default?: any;
  hidden?: number | boolean;
  in_list_view?: number;
}

export interface FieldComponentProps {
  value?: any;
  onChange?: (val: any) => void;
  disabled?: boolean;
  fieldMeta: FieldMeta;
}

export const REFINE_COMPONENT_REGISTRY: Record<string, React.FC<FieldComponentProps>> = {
  // 1. Standard Text Inputs
  Data: ({ value, onChange, disabled, fieldMeta }) => (
    <input
      type="text"
      placeholder={`Enter ${fieldMeta.label || fieldMeta.fieldname}...`}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  Password: ({ value, onChange, disabled, fieldMeta }) => (
    <input
      type="password"
      placeholder={`Enter ${fieldMeta.label || fieldMeta.fieldname}...`}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  "Read Only": ({ value, fieldMeta }) => (
    <div className="flex h-10 w-full items-center rounded-lg border border-gray-200 bg-gray-100/70 px-3 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-300">
      {value ?? <span className="text-gray-400 italic">None</span>}
    </div>
  ),

  Code: ({ value, onChange, disabled, fieldMeta }) => (
    <textarea
      placeholder={`Enter code for ${fieldMeta.label || fieldMeta.fieldname}...`}
      rows={4}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full font-mono rounded-lg border border-gray-200 bg-gray-50/70 p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  SmallText: ({ value, onChange, disabled, fieldMeta }) => (
    <textarea
      placeholder={`Enter ${fieldMeta.label || fieldMeta.fieldname}...`}
      rows={2}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full rounded-lg border border-gray-200 bg-gray-50/70 p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  Text: ({ value, onChange, disabled, fieldMeta }) => (
    <textarea
      placeholder={`Enter ${fieldMeta.label || fieldMeta.fieldname}...`}
      rows={4}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full rounded-lg border border-gray-200 bg-gray-50/70 p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  "Long Text": ({ value, onChange, disabled, fieldMeta }) => (
    <textarea
      placeholder={`Enter ${fieldMeta.label || fieldMeta.fieldname}...`}
      rows={6}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full rounded-lg border border-gray-200 bg-gray-50/70 p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  "Text Editor": ({ value, onChange, disabled, fieldMeta }) => (
    <textarea
      placeholder={`Compose ${fieldMeta.label || fieldMeta.fieldname}...`}
      rows={5}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full rounded-lg border border-gray-200 bg-gray-50/70 p-3 text-xs text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white dark:placeholder:text-gray-500 transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  // 2. Numeric and Currency
  Currency: ({ value, onChange, disabled, fieldMeta }) => (
    <div className="relative">
      <input
        type="number"
        step="0.01"
        placeholder={`0.00`}
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value === "" ? "" : Number(e.target.value))}
        disabled={disabled}
        className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
          disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
        }`}
      />
    </div>
  ),

  Int: ({ value, onChange, disabled, fieldMeta }) => (
    <input
      type="number"
      step="1"
      placeholder={`0`}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value === "" ? "" : parseInt(e.target.value, 10))}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  Float: ({ value, onChange, disabled, fieldMeta }) => (
    <input
      type="number"
      step="0.01"
      placeholder={`0.00`}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value === "" ? "" : parseFloat(e.target.value))}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  Percent: ({ value, onChange, disabled, fieldMeta }) => (
    <div className="relative flex items-center">
      <input
        type="number"
        step="0.1"
        placeholder={`0`}
        value={value ?? ""}
        onChange={(e) => onChange?.(e.target.value === "" ? "" : parseFloat(e.target.value))}
        disabled={disabled}
        className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 pl-3 pr-8 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
          disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
        }`}
      />
      <span className="pointer-events-none absolute right-3 text-xs font-medium text-gray-400 dark:text-gray-500">
        %
      </span>
    </div>
  ),

  // 3. Select Dropdown
  Select: ({ value, onChange, disabled, fieldMeta }) => {
    const rawOptions = fieldMeta.options || "";
    const options = rawOptions
      .split("\n")
      .map((opt) => opt.trim())
      .filter(Boolean);

    return (
      <div className="relative">
        <select
          value={value ?? ""}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={disabled}
          className={`h-10 w-full appearance-none rounded-lg border border-gray-200 bg-gray-50/70 px-3 pr-8 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors cursor-pointer ${
            disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
          }`}
        >
          <option value="">Select {fieldMeta.label || fieldMeta.fieldname}...</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
          <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      </div>
    );
  },

  // 4. Boolean / Checkbox (styled switch toggle)
  Check: ({ value, onChange, disabled, fieldMeta }) => {
    const isChecked = !!value && value !== 0 && value !== "0";
    return (
      <label className={`inline-flex items-center gap-2.5 ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}>
        <div className="relative inline-flex items-center">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={(e) => onChange?.(e.target.checked ? 1 : 0)}
            disabled={disabled}
            className="peer sr-only"
          />
          <div className="h-5 w-9 rounded-full bg-gray-200 peer-checked:bg-brand-500 peer-focus:outline-none dark:bg-gray-700 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
        </div>
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 select-none">
          {isChecked ? "Enabled" : "Disabled"}
        </span>
      </label>
    );
  },

  // 5. Date & Datetime
  Date: ({ value, onChange, disabled }) => (
    <input
      type="date"
      value={value ? String(value).slice(0, 10) : ""}
      onChange={(e) => onChange?.(e.target.value || null)}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  Datetime: ({ value, onChange, disabled }) => (
    <input
      type="datetime-local"
      value={value ? String(value).replace(" ", "T").slice(0, 19) : ""}
      onChange={(e) => onChange?.(e.target.value ? e.target.value.replace("T", " ") : null)}
      disabled={disabled}
      className={`h-10 w-full rounded-lg border border-gray-200 bg-gray-50/70 px-3 text-xs text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-gray-700 dark:bg-gray-800/80 dark:text-white transition-colors ${
        disabled ? "opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800" : ""
      }`}
    />
  ),

  // 6. Foreign Key Link
  Link: ({ value, onChange, disabled, fieldMeta }) => (
    <RefineLinkControl
      targetDocType={fieldMeta.options || ""}
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={`Select ${fieldMeta.label || fieldMeta.fieldname}...`}
    />
  ),

  // 7. Child Table
  Table: ({ value, onChange, disabled, fieldMeta }) => (
    <SubTableControl
      value={value}
      onChange={onChange}
      disabled={disabled}
      fieldMeta={fieldMeta}
    />
  ),
};
