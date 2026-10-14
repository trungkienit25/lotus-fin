/**
 * B1S_UI_SAFETY_V1: Response Normalization & Presentation Safety
 * Enforces deterministic fail-closed rules and separates transport from business outcomes.
 */

export type TransportOutcome = "SUCCESS" | "HTTP_ERROR" | "TIMEOUT" | "NETWORK_ERROR";

export type NormalizedStatus =
  | "OK"
  | "PARTIAL"
  | "FORBIDDEN"
  | "SOURCE_ERROR"
  | "TIMEOUT"
  | "NOT_AVAILABLE";

export interface SafePresentationResult {
  status: NormalizedStatus;
  userFacingText: string;
  sourceLabel: string;
  allowFinancialWidgets: boolean;
  correlationId?: string;
}

const CID_REGEX = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$/;

export function sanitizeCorrelationId(cidHeader?: unknown): string | undefined {
  if (typeof cidHeader !== "string") return undefined;
  const trimmed = cidHeader.trim();
  if (trimmed.includes(",")) return undefined; // reject conflicting multi-valued CIDs
  return CID_REGEX.test(trimmed) ? trimmed : undefined;
}

export function isFinancialOrSourceDependent(obj: Record<string, unknown>): boolean {
  if (typeof obj.tool_called === "string" && obj.tool_called.trim() !== "") return true;
  if ("tool_called" in obj && obj.tool_called !== undefined && obj.tool_called !== null) return true;
  if (Array.isArray(obj.executed_tools) && obj.executed_tools.length > 0) return true;
  if ("tool_output" in obj && obj.tool_output !== undefined && obj.tool_output !== null) return true;
  if ("ui_widget" in obj && obj.ui_widget !== undefined && obj.ui_widget !== null) return true;
  if ("result" in obj && obj.result !== undefined && obj.result !== null) return true;
  if ("suggestedActions" in obj && obj.suggestedActions !== undefined && obj.suggestedActions !== null) return true;
  if ("source" in obj && typeof obj.source === "string" && obj.source.trim() !== "") return true;
  return false;
}

export const SAFE_STATUS_MESSAGES: Record<NormalizedStatus, string> = {
  FORBIDDEN: "Bạn không có quyền thực hiện yêu cầu này.",
  SOURCE_ERROR: "Không thể truy cập nguồn dữ liệu. Vui lòng thử lại.",
  TIMEOUT: "Yêu cầu đã hết thời gian chờ.",
  NOT_AVAILABLE: "Chưa đủ ngữ cảnh hoặc nguồn đã xác minh để thực hiện yêu cầu này.",
  OK: "",
  PARTIAL: "Dữ liệu chỉ khả dụng một phần.",
};

const RECOGNIZED = new Set(["OK", "PARTIAL", "FORBIDDEN", "SOURCE_ERROR", "TIMEOUT", "NOT_AVAILABLE"]);

function extractStatus(val: unknown): string | null | undefined {
  if (val === undefined || val === null) return undefined;
  if (typeof val !== "string" && typeof val !== "number") return null;
  const s = String(val).trim().toUpperCase();
  return s === "ERROR" ? "SOURCE_ERROR" : s === "SUCCESS" ? "OK" : s;
}

function makeRes(status: NormalizedStatus, text: string, label: string, cid?: string): SafePresentationResult {
  return { status, userFacingText: text, sourceLabel: label, allowFinancialWidgets: false, correlationId: cid };
}

export function normalizeCopilotResponse(
  rawInput: unknown,
  transportStatus?: number,
  correlationIdHeader?: unknown
): SafePresentationResult {
  const correlationId = sanitizeCorrelationId(correlationIdHeader);

  // 1. Direct transport-level HTTP denial check
  if (transportStatus === 401 || transportStatus === 403) {
    return makeRes("FORBIDDEN", SAFE_STATUS_MESSAGES.FORBIDDEN, "Quyền truy cập bị từ chối", correlationId);
  }

  // 2. Inspect payload objects (if any)
  const rootObj = (rawInput && typeof rawInput === "object") ? (rawInput as Record<string, unknown>) : null;
  const msgObj = (rootObj?.message && typeof rootObj.message === "object")
    ? (rootObj.message as Record<string, unknown>)
    : rootObj;
  const toolOut = (msgObj?.tool_output && typeof msgObj.tool_output === "object")
    ? (msgObj.tool_output as Record<string, unknown>)
    : undefined;

  const rawStatuses = [
    rootObj ? extractStatus(rootObj.status) : undefined,
    msgObj ? extractStatus(msgObj.status) : undefined,
    toolOut ? extractStatus(toolOut.status) : undefined,
  ].filter((s) => s !== undefined);

  // 3. FORBIDDEN in body takes absolute priority (even over HTTP 500/504 and invalid status)
  if (rawStatuses.includes("FORBIDDEN")) {
    return makeRes("FORBIDDEN", SAFE_STATUS_MESSAGES.FORBIDDEN, "Quyền truy cập bị từ chối", correlationId);
  }

  // 4. Remaining HTTP transport errors
  if (transportStatus === 408 || transportStatus === 504) {
    return makeRes("TIMEOUT", SAFE_STATUS_MESSAGES.TIMEOUT, "Hết thời gian chờ", correlationId);
  }
  if (transportStatus && transportStatus >= 500) {
    return makeRes("SOURCE_ERROR", SAFE_STATUS_MESSAGES.SOURCE_ERROR, "Lỗi nguồn dữ liệu", correlationId);
  }

  // 5. Check for invalid or unrecognized statuses
  if (rawStatuses.some((s) => s === null || !RECOGNIZED.has(s))) {
    return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Không khả dụng", correlationId);
  }

  const validStatuses = rawStatuses as string[];

  // 6. Conflicting terminal failure pairs -> NOT_AVAILABLE
  const hasSourceError = !!rootObj?.error || !!msgObj?.error || (toolOut ? !!toolOut.error : false) || validStatuses.includes("SOURCE_ERROR");
  const hasTimeout = validStatuses.includes("TIMEOUT");
  const hasNotAvailable = validStatuses.includes("NOT_AVAILABLE");

  const terminalCount = (hasSourceError ? 1 : 0) + (hasTimeout ? 1 : 0) + (hasNotAvailable ? 1 : 0);
  if (terminalCount > 1) {
    return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Không khả dụng", correlationId);
  }

  if (hasSourceError) return makeRes("SOURCE_ERROR", SAFE_STATUS_MESSAGES.SOURCE_ERROR, "Lỗi nguồn dữ liệu", correlationId);
  if (hasTimeout) return makeRes("TIMEOUT", SAFE_STATUS_MESSAGES.TIMEOUT, "Hết thời gian chờ", correlationId);
  if (hasNotAvailable) return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Không khả dụng", correlationId);
  if (validStatuses.includes("PARTIAL")) return makeRes("PARTIAL", SAFE_STATUS_MESSAGES.PARTIAL, "Nguồn một phần", correlationId);

  // 7. Non-object primitive response
  if (!rootObj) {
    if (typeof rawInput === "string" && rawInput.trim()) {
      return makeRes("OK", rawInput.trim(), "Nguồn chưa xác minh", correlationId);
    }
    return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Không khả dụng", correlationId);
  }

  // 8. Financial / source dependency check
  if (isFinancialOrSourceDependent(rootObj) || (msgObj && isFinancialOrSourceDependent(msgObj))) {
    return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Chưa đủ ngữ cảnh", correlationId);
  }

  // 9. Benign reply extraction
  const rawReply = msgObj?.reply || msgObj?.content || rootObj.reply;
  if (typeof rawReply === "string" && rawReply.trim()) {
    return makeRes("OK", rawReply.trim(), "Nguồn chưa xác minh", correlationId);
  }

  return makeRes("NOT_AVAILABLE", SAFE_STATUS_MESSAGES.NOT_AVAILABLE, "Không khả dụng", correlationId);
}
