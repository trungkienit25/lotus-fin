/**
 * Lotus Fin — Presentation Layer Brand Formatting Utilities
 *
 * Converts internal engine terms (such as "ERPNext", "Frappe") into
 * official customer-facing Lotus Fin brand terminology on the UI.
 *
 * NOTE: This function only formats DISPLAY strings on the frontend.
 * It NEVER modifies underlying database DocTypes, API routes, or schema keys.
 */

import { SANITIZATION_PATTERNS } from "../constants/executiveDictionary";

export function formatBrandText(text: string | null | undefined): string {
  if (!text) return "";

  // 1. Direct Whole-Phrase Mappings
  const phraseMap: Record<string, string> = {
    "ERPNext Settings": "Lotus Fin Settings",
    "ERPNext Integrations": "Lotus Fin Integrations",
    "ERPNext Desk": "Lotus Fin Desk",
    "ERPNext Portal": "Lotus Fin Portal",
    "ERPNext": "Lotus Fin",
  };

  if (phraseMap[text]) {
    return phraseMap[text];
  }

  // 2. Substring Brand Replacement for user-facing headers & labels
  let cleaned = text.replace(/\bERPNext\b/gi, "Lotus Fin");

  // 3. Automated Executive Sanitization Gate (Client-side safety)
  for (const { pattern, replacement } of SANITIZATION_PATTERNS) {
    cleaned = cleaned.replace(pattern, replacement);
  }

  return cleaned.trim();
}


