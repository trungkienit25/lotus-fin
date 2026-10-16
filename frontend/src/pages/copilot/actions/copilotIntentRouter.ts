import { parseInvoiceIntent } from "./invoiceActionPresentation.ts";

export type IntegratedIntent = { kind: "L0" | "L1" | "L2" | "L3" | "L4" | "CONFIRM" | "L5" | "V1" | "CLARIFY"; message?: string };

/** Bounded language routing selects a view, never grants execution authority. */
export function routeCopilotIntent(text: string): IntegratedIntent {
  const normalized = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase();
  if (/xac nhan.*task|confirm.*task/.test(normalized)) return { kind: "CONFIRM", message: "Xem đề xuất và dùng nút xác nhận riêng. Tin nhắn không cấp quyền thực thi." };
  if (/gui email|send email|submit|cancel|thanh toan|payment|scheduler/.test(normalized)) return { kind: "L5" };
  if (/qua han cuoi|past.?final.?due/.test(normalized)) return { kind: "V1" };
  if (/tao task|create task|task theo doi/.test(normalized)) return { kind: "L4" };
  if (/soan.*nhac|soan thu|nhac no|reminder|follow.?up|draft email/.test(normalized)) return { kind: "L3" };
  if (/mo hoa don|open invoice/.test(normalized)) return { kind: "L2", message: "Chọn đúng một hóa đơn trong kết quả rồi bấm Open; không đoán mục tiêu từ lời nhắn." };
  if (/tim hoa don|find invoice|search invoice|tra cuu hoa don|tra cuu chung tu|chung tu erp|co so du lieu erp/.test(normalized)) return { kind: "L1" };
  const invoice = parseInvoiceIntent(text);
  if (invoice.kind === "clarify") return { kind: "CLARIFY", message: invoice.questions.join("\n\n") };
  if (invoice.kind === "search") return { kind: "L1" };
  if (/\b(tao|mo|gui|xac nhan)\b/.test(normalized)) return { kind: "CLARIFY", message: "Bạn muốn thao tác nào và với đối tượng nào? Hãy chọn một mục tiêu cụ thể." };
  return { kind: "L0" };
}
