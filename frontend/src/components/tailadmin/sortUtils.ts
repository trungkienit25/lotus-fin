import { FieldMeta } from "../../engine/RefineComponentRegistry";

export interface SortOption {
  field: string;
  direction: "asc" | "desc";
  label: string;
}

export type TranslateFn = (key: string, params?: Record<string, string | number>) => string;

/**
 * Builds standard and schema-specific sort options with i18n support.
 * Decoupled from component presentation to adhere to Single Responsibility Principle.
 */
export function buildSortOptions(
  allFields: FieldMeta[] = [],
  t: TranslateFn
): SortOption[] {
  const options: SortOption[] = [
    { field: "creation", direction: "desc", label: t("sort.newest") },
    { field: "creation", direction: "asc", label: t("sort.oldest") },
    { field: "modified", direction: "desc", label: t("sort.recentlyModified") },
    { field: "name", direction: "asc", label: t("sort.nameAsc") },
    { field: "name", direction: "desc", label: t("sort.nameDesc") },
  ];

  // Dynamically include sort options for currency, date, numeric fields
  const extraSortFields = allFields
    .filter(
      (f) =>
        ["Currency", "Float", "Date", "Datetime"].includes(f.fieldtype) &&
        !["creation", "modified"].includes(f.fieldname)
    )
    .slice(0, 3);

  for (const f of extraSortFields) {
    const fieldLabel = f.label || f.fieldname;
    options.push({
      field: f.fieldname,
      direction: "desc",
      label: t("sort.descending", { field: fieldLabel }),
    });
    options.push({
      field: f.fieldname,
      direction: "asc",
      label: t("sort.ascending", { field: fieldLabel }),
    });
  }

  return options;
}

