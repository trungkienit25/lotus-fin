import React, { useEffect, useState } from "react";
import axios from "axios";
import { REFINE_COMPONENT_REGISTRY, FieldMeta } from "../RefineComponentRegistry";

interface SubTableControlProps {
  value?: any[];
  onChange?: (val: any[]) => void;
  disabled?: boolean;
  fieldMeta: FieldMeta;
}

export const SubTableControl: React.FC<SubTableControlProps> = ({
  value = [],
  onChange,
  disabled,
  fieldMeta,
}) => {
  const childDocType = fieldMeta.options || "";
  const [childSchema, setChildSchema] = useState<FieldMeta[]>([]);
  const [loading, setLoading] = useState(false);

  // Load Child DocType Metadata Schema
  useEffect(() => {
    if (!childDocType) return;
    setLoading(true);
    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(childDocType)}`)
      .then((res) => {
        const childFields: FieldMeta[] = res.data?.docs?.[0]?.fields || [];
        const visibleFields = childFields.filter(
          (f: any) =>
            !f.hidden &&
            !["Section Break", "Column Break"].includes(f.fieldtype) &&
            (f.in_list_view || f.reqd)
        );
        setChildSchema(visibleFields.length > 0 ? visibleFields : childFields.slice(0, 5));
      })
      .catch((err) => {
        console.error("Error loading child doctype schema:", err);
      })
      .finally(() => setLoading(false));
  }, [childDocType]);

  const handleCellChange = (rowIndex: number, fieldname: string, cellVal: any) => {
    const updated = [...value];
    updated[rowIndex] = {
      ...updated[rowIndex],
      [fieldname]: cellVal,
    };
    onChange?.(updated);
  };

  const handleAddRow = () => {
    const newRow: any = { idx: value.length + 1 };
    onChange?.([...value, newRow]);
  };

  const handleDeleteRow = (rowIndex: number) => {
    const updated = value.filter((_, idx) => idx !== rowIndex);
    onChange?.(updated);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50/50 p-4 dark:border-gray-800 dark:bg-gray-900/40">
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-dark">
        <table className="w-full text-left text-xs text-gray-700 dark:text-gray-300">
          <thead className="border-b border-gray-200 bg-gray-50/80 text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:border-gray-800 dark:bg-gray-800/60 dark:text-gray-400">
            <tr>
              <th className="w-12 px-3 py-2.5 text-center">#</th>
              {childSchema.map((f) => (
                <th key={f.fieldname} className="min-w-[140px] px-3 py-2.5">
                  {f.label || f.fieldname}
                  {f.reqd ? <span className="ml-1 text-red-500">*</span> : null}
                </th>
              ))}
              {!disabled && <th className="w-16 px-3 py-2.5 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={childSchema.length + 2} className="py-6 text-center text-gray-400">
                  <div className="inline-flex items-center gap-2">
                    <svg className="size-4 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Loading schema...
                  </div>
                </td>
              </tr>
            ) : value.length === 0 ? (
              <tr>
                <td colSpan={childSchema.length + 2} className="py-6 text-center text-gray-400 italic">
                  No rows added yet.
                </td>
              </tr>
            ) : (
              value.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50/50 dark:hover:bg-white/[0.02] transition-colors">
                  <td className="px-3 py-2 text-center font-medium text-gray-400">{rowIndex + 1}</td>
                  {childSchema.map((f) => {
                    const Comp = REFINE_COMPONENT_REGISTRY[f.fieldtype] || REFINE_COMPONENT_REGISTRY.Data;
                    return (
                      <td key={f.fieldname} className="px-2 py-1.5">
                        <Comp
                          value={row[f.fieldname]}
                          onChange={(val) => handleCellChange(rowIndex, f.fieldname, val)}
                          disabled={disabled || !!f.read_only}
                          fieldMeta={f}
                        />
                      </td>
                    );
                  })}
                  {!disabled && (
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteRow(rowIndex)}
                        className="inline-flex size-7 items-center justify-center rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors"
                        title="Delete row"
                      >
                        <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                          <path
                            fillRule="evenodd"
                            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!disabled && (
        <button
          type="button"
          onClick={handleAddRow}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-dashed border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:border-brand-500 hover:bg-brand-50/50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500 dark:hover:bg-brand-500/10 dark:hover:text-brand-400 transition-all shadow-theme-xs w-full justify-center"
        >
          <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          Add Row to {fieldMeta.label || fieldMeta.fieldname}
        </button>
      )}
    </div>
  );
};
