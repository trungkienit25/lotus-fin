import React from "react";
import { useTranslation } from "../../i18n";

interface EmptyStateProps {
  title: string;
  hasFilters: boolean;
  onClearFilters: () => void;
  onCreateNew: () => void;
}

export const TailAdminEmptyState: React.FC<EmptyStateProps> = ({
  title,
  hasFilters,
  onClearFilters,
  onCreateNew,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* Icon Placeholder */}
      <div className="flex size-16 items-center justify-center rounded-2xl bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500 mb-4 shadow-theme-xs">
        <svg
          className="size-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>

      {/* Contextual Text */}
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
        {hasFilters
          ? t("common.noDataFound")
          : `${t("common.noDataFound")}: ${title}`}
      </h3>
      <p className="mt-1 max-w-sm text-xs text-gray-500 dark:text-gray-400">
        {hasFilters
          ? t("common.noRecordsMatch")
          : t("common.addNew", { name: title })}
      </p>

      {/* Action Buttons */}
      <div className="mt-5 flex items-center gap-3">
        {hasFilters && (
          <button
            onClick={onClearFilters}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            {t("common.clearFilters")}
          </button>
        )}

        <button
          onClick={onCreateNew}
          className="inline-flex items-center gap-1.5 rounded-lg bg-gray-900 px-4 py-2 text-xs font-medium text-white shadow-theme-xs hover:bg-black dark:bg-brand-500 dark:hover:bg-brand-600 transition-colors"
        >
          <svg className="size-3.5 fill-current" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          {t("common.addNew", { name: title })}
        </button>
      </div>
    </div>
  );
};
