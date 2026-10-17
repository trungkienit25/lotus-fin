/**
 * Lotus Fin - Executive Presentation Dictionary (English Standard)
 * Centralized mapping of technical keys and database flags to natural business English.
 */

export const TECHNICAL_KEY_DICTIONARY: Record<string, string> = {
  STRICT_BASELINE_V1: "Standardized figures based on verified commercial invoices issued",
  has_constituent_deficit: "Constituent bank account deficit condition",
  shortfall_events: "Cash shortfall risk alerts",
  NO_CONFIRMED_SETTLEMENT_EVENTS: "No confirmed settlement schedule recorded in this period",
  FORECAST_UNAVAILABLE: "Cash flow data does not meet forecasting qualification criteria",
  TRADE_ONLY: "Independent commercial accounting scope",
  VALIDATION_ERROR: "Ledger reconciliation variance",
  INCONSISTENT_DATA: "Ledger figures not fully synchronized",
  UNAVAILABLE: "Temporarily unavailable",
  AWAITING_DATA: "Awaiting ledger data synchronization",
};

export const SANITIZATION_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /\(?\bhas_constituent_deficit:\s*(?:true|false|None)\)?\.?/gi, replacement: "" },
  { pattern: /\(?\bconstituent_deficit:\s*(?:true|false|None)\)?\.?/gi, replacement: "" },
  { pattern: /\(?\bopening_cash_deficit:\s*(?:true|false|None)\)?\.?/gi, replacement: "" },
  { pattern: /\(?\bshortfall_events:\s*\[\s*\]\)?\.?/gi, replacement: "" },
  { pattern: /\(?\bshortfall_events\b\)?/gi, replacement: "" },
  { pattern: /\(?\bSTRICT_BASELINE_V1\)?\.?/g, replacement: "" },
  { pattern: /\(?\bTRADE_ONLY\)?\.?/g, replacement: "" },
  { pattern: /\(?\bNO_CONFIRMED_SETTLEMENT_EVENTS\)?\.?/g, replacement: "" },
  { pattern: /\(?\bFORECAST_UNAVAILABLE\)?\.?/g, replacement: "" },
  { pattern: /\(?\bVALIDATION_ERROR\)?\.?/g, replacement: "" },
  { pattern: /\(?\bINCONSISTENT_DATA\)?\.?/g, replacement: "" },
  { pattern: /\(\s*\)/g, replacement: "" },
  { pattern: /[ \t]{2,}/g, replacement: " " },
  { pattern: /\s+\./g, replacement: "." },
  { pattern: /\s+,/g, replacement: "," },
];
