import { routeCopilotIntent } from "../actions/copilotIntentRouter.ts";
import { getSessionScopeSnapshot } from "../../../providers/sessionScope.ts";
import type { AttachedFile, ChatMessage, ChatPanelMode } from "./VercelChatPanelTypes.ts";
import type { AuthenticatedActionScope } from "../../../providers/sessionScope.ts";
import type { SafePresentationResult } from "./copilotPresentation.ts";

interface SenderOptions {
  input: string; files: AttachedFile[]; loading: boolean; scope: AuthenticatedActionScope;
  profile: "CORE" | "DEMO"; currentProfile: () => "CORE" | "DEMO";
  append: (message: ChatMessage) => void; clearInput: () => void;
  selectMode: (mode: ChatPanelMode) => void;
  selectFeature: (feature: "L4" | "L5" | "V1") => void;
  sendRequest: (query: string, files: string[]) => Promise<SafePresentationResult>;
}

export function createCopilotMessageSender(options: SenderOptions) {
  return async (suppliedText?: string) => {
    const text = (typeof suppliedText === "string" ? suppliedText : options.input).trim();
    if ((!text && options.files.length === 0) || options.loading) return;
    const intent = routeCopilotIntent(text);
    if (["L1", "L2", "L3", "L4", "CONFIRM", "L5", "V1"].includes(intent.kind)) {
      if (options.scope.state !== "VERIFIED") return;
      if (intent.kind === "L1" || intent.kind === "L2") options.selectMode("invoices");
      else if (intent.kind === "L3") options.selectMode("followup");
      else options.selectFeature(intent.kind === "CONFIRM" ? "L4" : intent.kind as "L4" | "L5" | "V1");
      options.clearInput();
      return; // Text, including "confirm", cannot execute a mutation.
    }
    const admitted = getSessionScopeSnapshot();
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    options.append({ id: `user-${crypto.randomUUID()}`, sender: "user", content: text || "Attached files",
      timestamp, attachments: options.files.length ? [...options.files] : undefined });
    options.clearInput();
    const reply = (content: string, sourceLabel: string, correlationId?: string) => options.append({
      id: `asst-${crypto.randomUUID()}`, sender: "assistant", content, timestamp, sourceLabel, correlationId });
    if (intent.kind === "CLARIFY") { reply(intent.message || "Hãy làm rõ yêu cầu.", "L0 Clarification"); return; }
    if (/(giải thích|explain|là gì|help|xin chào)/i.test(text)) {
      reply("Lotus Fin hỗ trợ tìm và mở hóa đơn theo lựa chọn rõ ràng; soạn lời nhắc cục bộ; xem đề xuất Task trước khi xác nhận riêng; kiểm tra chính sách hành động tác động cao. PastFinalDue nghĩa là hóa đơn đã qua hạn cuối, đã submit và còn dư nợ dương. CORE chờ nguồn và chính sách được duyệt; DEMO dùng dữ liệu giả. Không gửi email hay thanh toán tự động.", "L0 Deterministic Explanation");
      return;
    }
    const result = await options.sendRequest(text, options.files.map(f => f.name));
    const current = getSessionScopeSnapshot();
    if (current.generation !== admitted.generation || current.state !== "VERIFIED" ||
        options.currentProfile() !== options.profile || !result.userFacingText) return;
    reply(result.userFacingText, result.sourceLabel, result.correlationId);
  };
}
