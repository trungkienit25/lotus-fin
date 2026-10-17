import { parseInvoiceIntent } from "./invoiceActionPresentation.ts";

export type IntegratedIntent = { kind: "L0" | "L1" | "L2" | "L3" | "L4" | "CONFIRM" | "L5" | "V1" | "CLARIFY"; message?: string };

/** Bounded language routing selects a view, never grants execution authority. */
export function routeCopilotIntent(text: string): IntegratedIntent {
  const normalized = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase();
  if (/xac nhan.*task|confirm.*task/.test(normalized)) return { kind: "CONFIRM", message: "Please review the proposal and use the dedicated confirmation button. Chat messages do not grant execution authority." };
  if (/gui email|send email|submit|cancel|thanh toan|payment|scheduler/.test(normalized)) return { kind: "L5" };
  if (/qua han cuoi|past.?final.?due/.test(normalized)) return { kind: "V1" };
  if (/tao task|create task|task theo doi/.test(normalized)) return { kind: "L4" };
  if (/soan.*nhac|soan thu|nhac no|reminder|follow.?up|draft email/.test(normalized)) return { kind: "L3" };
  if (/mo hoa don|open invoice/.test(normalized)) return { kind: "L2", message: "Please select an invoice from the search results and click Open; target entity cannot be guessed from text." };
  if (/tim hoa don|find invoice|search invoice|tra cuu hoa don|tra cuu chung tu|chung tu erp|co so du lieu erp/.test(normalized)) return { kind: "L1" };
  const invoice = parseInvoiceIntent(text);
  if (invoice.kind === "clarify") return { kind: "CLARIFY", message: invoice.questions.join("\n\n") };
  if (invoice.kind === "search") return { kind: "L1" };
  if (/\b(tao|mo|gui|xac nhan)\b/.test(normalized)) return { kind: "CLARIFY", message: "Which action and target entity would you like to perform? Please select a specific target." };
  return { kind: "L0" };
}
