import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import Badge from "../../components/ui/badge/Badge";
import { REFINE_COMPONENT_REGISTRY, FieldMeta } from "../../engine/RefineComponentRegistry";

interface DocTypeSchema {
  name: string;
  module?: string;
  issingle?: number | boolean;
  is_submittable?: number | boolean;
  title_field?: string;
  fields: FieldMeta[];
}

interface FormSection {
  title: string;
  description?: string;
  fields: FieldMeta[];
}

export const UniversalFormView: React.FC = () => {
  const { doctype: rawDocType, id: rawId } = useParams<{ doctype: string; id?: string }>();
  const doctype = rawDocType ? decodeURIComponent(rawDocType) : "";
  const id = rawId ? decodeURIComponent(rawId) : "";
  const navigate = useNavigate();

  const [schema, setSchema] = useState<DocTypeSchema | null>(null);
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [schemaError, setSchemaError] = useState<string | null>(null);

  const [formData, setFormData] = useState<Record<string, any>>({});
  const [originalData, setOriginalData] = useState<Record<string, any>>({});
  const [loadingData, setLoadingData] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [docMeta, setDocMeta] = useState<any>(null);

  const isSingle = Boolean(schema?.issingle || id === doctype);
  const isCreate = !isSingle && (!id || id === "new");

  // 1. Fetch DocType Schema Definition
  useEffect(() => {
    if (!doctype) return;
    setLoadingSchema(true);
    setSchemaError(null);

    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(doctype)}`)
      .then((res) => {
        const docList = res.data?.docs || [];
        const currentDoc = docList.find((d: any) => d.name === doctype) || docList[0];
        if (currentDoc) {
          setSchema(currentDoc);
        } else {
          setSchemaError(`DocType definition not found for "${doctype}"`);
        }
      })
      .catch((err) => {
        setSchemaError(err.response?.data?.message || `Error loading schema for "${doctype}"`);
      })
      .finally(() => {
        setLoadingSchema(false);
      });
  }, [doctype]);

  // 2. Fetch Document Data or Initialize Defaults
  const fetchDocData = () => {
    if (!schema) return;

    if (isCreate) {
      // Initialize default values from schema
      const initial: Record<string, any> = {};
      schema.fields.forEach((f) => {
        if (f.default !== undefined && f.default !== null) {
          initial[f.fieldname] = f.default;
        } else if (f.fieldtype === "Check") {
          initial[f.fieldname] = 0;
        } else if (f.fieldtype === "Table") {
          initial[f.fieldname] = [];
        }
      });
      setFormData(initial);
      setOriginalData(initial);
      setDocMeta(null);
      setLoadingData(false);
      return;
    }

    // Load existing document data
    const docName = isSingle ? doctype : id;
    setLoadingData(true);
    setSaveError(null);

    // Try standard resource endpoint or desk load
    axios
      .get(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(docName)}`)
      .then((res) => {
        const data = res.data?.data || res.data?.docs?.[0] || {};
        setFormData(data);
        setOriginalData(data);
        setDocMeta({
          modified: data.modified,
          creation: data.creation,
          owner: data.owner,
          docstatus: data.docstatus,
        });
      })
      .catch(() => {
        // Fallback to desk.form.load.getdoc
        axios
          .get(`/api/method/frappe.desk.form.load.getdoc?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(docName)}`)
          .then((res) => {
            const data = res.data?.docs?.[0] || {};
            setFormData(data);
            setOriginalData(data);
            setDocMeta({
              modified: data.modified,
              creation: data.creation,
              owner: data.owner,
              docstatus: data.docstatus,
            });
          })
          .catch((err) => {
            console.error("Error loading document data:", err);
            setSaveError(err.response?.data?.message || "Failed to load document data.");
          });
      })
      .finally(() => {
        setLoadingData(false);
      });
  };

  useEffect(() => {
    if (schema) {
      fetchDocData();
    }
  }, [schema, id, doctype]);

  // Handle Field Value Changes
  const handleFieldChange = (fieldname: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [fieldname]: value,
    }));
    setSaveSuccess(false);
    setSaveError(null);
  };

  // Group fields into Sections
  const sections = useMemo<FormSection[]>(() => {
    if (!schema?.fields) return [];

    const result: FormSection[] = [];
    let currentSection: FormSection = {
      title: "General Settings",
      fields: [],
    };

    schema.fields.forEach((field) => {
      if (field.fieldtype === "Section Break") {
        if (currentSection.fields.length > 0) {
          result.push(currentSection);
        }
        currentSection = {
          title: field.label || "Details",
          description: field.description,
          fields: [],
        };
      } else if (field.fieldtype === "Column Break" || field.fieldtype === "Tab Break" || field.hidden) {
        // Skip layout columns and hidden fields
      } else {
        currentSection.fields.push(field);
      }
    });

    if (currentSection.fields.length > 0) {
      result.push(currentSection);
    }

    return result;
  }, [schema]);

  // Has unsaved changes check
  const isDirty = useMemo(() => {
    return JSON.stringify(formData) !== JSON.stringify(originalData);
  }, [formData, originalData]);

  // Handle Save
  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      if (isSingle) {
        // Save Single DocType
        await axios.put(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(doctype)}`, formData);
      } else if (isCreate) {
        // Create new record
        const res = await axios.post(`/api/resource/${encodeURIComponent(doctype)}`, formData);
        const newRecordName = res.data?.data?.name;
        if (newRecordName) {
          navigate(`/app/${encodeURIComponent(doctype)}/${encodeURIComponent(newRecordName)}`, { replace: true });
        }
      } else {
        // Update existing record
        await axios.put(`/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(id)}`, formData);
      }

      setOriginalData(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      console.error("Save failed:", err);
      const msg = err.response?.data?._server_messages
        ? JSON.parse(err.response.data._server_messages).join("\n")
        : err.response?.data?.message || err.message || "An error occurred while saving.";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    setFormData(originalData);
    setSaveError(null);
    setSaveSuccess(false);
  };

  // Determine Page Title & Subtitle
  const pageTitle = isSingle
    ? doctype
    : isCreate
    ? `New ${doctype}`
    : formData[schema?.title_field || "name"] || id;

  if (loadingSchema) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3">
        <svg className="size-8 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Loading form schema...</span>
      </div>
    );
  }

  if (schemaError) {
    return (
      <div className="m-6 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
        <div className="flex items-center gap-2 font-semibold">
          <svg className="size-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Schema Loading Error
        </div>
        <p className="mt-2 text-xs">{schemaError}</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-xs font-medium text-white hover:bg-red-700 transition"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl pb-16">
      {/* 1. Header Toolbar */}
      <div className="sticky top-0 z-30 mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-gray-200/80 bg-gray-50/90 py-3.5 backdrop-blur dark:border-gray-800/80 dark:bg-gray-900/90">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => (isSingle ? navigate(-1) : navigate(`/app/${encodeURIComponent(doctype)}`))}
            className="flex size-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 hover:border-brand-500 hover:text-brand-500 dark:border-gray-800 dark:bg-gray-dark dark:text-gray-400 dark:hover:text-white transition shadow-theme-xs"
            title="Back"
          >
            <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
          </button>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                {schema?.module || "Form"} / {doctype}
              </span>
              {isSingle ? (
                <Badge size="sm" color="info">Single Doc</Badge>
              ) : isCreate ? (
                <Badge size="sm" color="warning">New</Badge>
              ) : docMeta?.docstatus === 1 ? (
                <Badge size="sm" color="success">Submitted</Badge>
              ) : (
                <Badge size="sm" color="light">Saved</Badge>
              )}
            </div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              {pageTitle}
            </h1>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={fetchDocData}
            disabled={loadingData || saving}
            className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3.5 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-800 dark:bg-gray-dark dark:text-gray-300 dark:hover:bg-white/5 transition shadow-theme-xs"
          >
            <svg className={`size-3.5 ${loadingData ? "animate-spin text-brand-500" : ""}`} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
            Refresh
          </button>

          {isDirty && (
            <button
              type="button"
              onClick={handleDiscard}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3.5 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 hover:text-red-600 dark:border-gray-800 dark:bg-gray-dark dark:text-gray-300 dark:hover:bg-white/5 transition shadow-theme-xs"
            >
              Discard Changes
            </button>
          )}

          <button
            type="button"
            onClick={() => handleSave()}
            disabled={saving || (!isDirty && !isCreate)}
            className={`inline-flex items-center gap-2 rounded-xl px-5 py-2 text-xs font-semibold text-white shadow-theme-xs transition ${
              saving || (!isDirty && !isCreate)
                ? "bg-brand-400 opacity-60 cursor-not-allowed"
                : "bg-brand-500 hover:bg-brand-600 active:scale-[0.98]"
            }`}
          >
            {saving ? (
              <>
                <svg className="size-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {saveSuccess && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-medium text-emerald-800 dark:border-emerald-800/50 dark:bg-emerald-950/30 dark:text-emerald-300 animate-in fade-in duration-200">
          <svg className="size-4 shrink-0 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          Document saved successfully!
        </div>
      )}

      {saveError && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-medium text-rose-800 dark:border-rose-800/50 dark:bg-rose-950/30 dark:text-rose-300 animate-in fade-in duration-200">
          <svg className="size-4 shrink-0 text-rose-500 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div className="flex-1 whitespace-pre-line">{saveError}</div>
        </div>
      )}

      {/* 2. Main Form Card Container */}
      <form onSubmit={handleSave} className="space-y-6">
        {sections.map((section, idx) => (
          <div
            key={section.title + idx}
            className="rounded-2xl border border-gray-200 bg-white p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-dark"
          >
            {/* Section Header */}
            <div className="border-b border-gray-100 pb-3 mb-5 dark:border-gray-800">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {section.title}
              </h3>
              {section.description && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {section.description}
                </p>
              )}
            </div>

            {/* Form Fields Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
              {section.fields.map((field) => {
                const FieldComponent = REFINE_COMPONENT_REGISTRY[field.fieldtype] || REFINE_COMPONENT_REGISTRY.Data;
                const isFullWidth = [
                  "Text",
                  "Text Editor",
                  "SmallText",
                  "Long Text",
                  "Table",
                  "Code",
                  "HTML Editor",
                  "Markdown Editor",
                ].includes(field.fieldtype);

                return (
                  <div
                    key={field.fieldname}
                    className={`space-y-1.5 ${isFullWidth ? "col-span-full" : "col-span-1"}`}
                  >
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        {field.label || field.fieldname}
                        {field.reqd ? <span className="ml-1 text-rose-500">*</span> : null}
                      </label>
                      {field.read_only ? (
                        <span className="text-[10px] text-gray-400 uppercase tracking-wider">Read Only</span>
                      ) : null}
                    </div>

                    <FieldComponent
                      value={formData[field.fieldname]}
                      onChange={(val) => handleFieldChange(field.fieldname, val)}
                      disabled={!!field.read_only || saving}
                      fieldMeta={field}
                    />

                    {field.description && (
                      <p className="text-[11px] text-gray-400 dark:text-gray-500">
                        {field.description}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </form>
    </div>
  );
};
