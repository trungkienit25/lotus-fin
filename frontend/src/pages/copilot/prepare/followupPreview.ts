// Contract-exact types and pure preview generation for L3 local reminder preview.
// Strictly pure logic: no clock, no storage, no clipboard, no ERP calls.

export const EXPECTED_FOLLOWUP_TEMPLATE =
  "Xin chào,\n\nTôi muốn trao đổi về nội dung cần theo dõi. Khi thuận tiện, vui lòng phản hồi để chúng ta xác nhận thông tin và bước tiếp theo.\n\nCảm ơn.";

export const MAX_UNICODE_SCALARS = 2000;
export const MAX_UTF8_BYTES = 8192;

export interface PrepareRequest {
  contract_version: "l3.followup.local.v0.1";
  capability: "followup.prepare_text";
  template_id: "followup.neutral.vi.v1";
  locale: "vi-VN";
}

export type PreviewProvenance = "SUGGESTED" | "USER_ENTERED";

export interface PreviewData {
  template_id: "followup.neutral.vi.v1";
  locale: "vi-VN";
  body: string;
  provenance: PreviewProvenance;
  facts_verified: false;
  persisted: false;
  delivery: "NONE";
  side_effects: [];
  financial_source: null;
}

export type PrepareStatus =
  | "PREVIEW_READY"
  | "INVALID_INPUT"
  | "CONTEXT_UNAVAILABLE"
  | "EXPIRED";

export interface PrepareResult {
  status: PrepareStatus;
  contract_version?: "l3.followup.local.v0.1";
  capability?: "followup.prepare_text";
  preview: PreviewData | null;
  user_message: string;
}

export interface EditValidationResult {
  valid: boolean;
  normalizedText: string;
  scalarCount: number;
  byteCount: number;
  errorCode:
    | "EMPTY_TEXT"
    | "EXCEEDS_MAX_SCALARS"
    | "EXCEEDS_MAX_BYTES"
    | "FORBIDDEN_CONTROL_CHAR"
    | "FORBIDDEN_BIDI_CONTROL"
    | null;
}

// oxlint-disable-next-line eslint(no-control-regex)
const FORBIDDEN_C0_C1_DEL = /[\u0000-\u0009\u000B\u000C\u000E-\u001F\u007F-\u009F]/;
const FORBIDDEN_BIDI = /[\u202A-\u202E\u2066-\u2069]/;

export function prepareFollowupPreview(req: unknown): PrepareResult {
  if (!req || typeof req !== "object") {
    return {
      status: "INVALID_INPUT",
      preview: null,
      user_message: "Yêu cầu không hợp lệ.",
    };
  }

  const keys = Object.keys(req);
  if (keys.length !== 4) {
    return {
      status: "INVALID_INPUT",
      preview: null,
      user_message: "Yêu cầu chứa trường không được phép hoặc thiếu trường.",
    };
  }

  const r = req as Record<string, unknown>;
  if (
    r.contract_version !== "l3.followup.local.v0.1" ||
    r.capability !== "followup.prepare_text" ||
    r.template_id !== "followup.neutral.vi.v1" ||
    r.locale !== "vi-VN"
  ) {
    return {
      status: "INVALID_INPUT",
      preview: null,
      user_message: "Tham số hợp đồng không hợp lệ.",
    };
  }

  return {
    status: "PREVIEW_READY",
    contract_version: "l3.followup.local.v0.1",
    capability: "followup.prepare_text",
    preview: {
      template_id: "followup.neutral.vi.v1",
      locale: "vi-VN",
      body: EXPECTED_FOLLOWUP_TEMPLATE,
      provenance: "SUGGESTED",
      facts_verified: false,
      persisted: false,
      delivery: "NONE",
      side_effects: [],
      financial_source: null,
    },
    user_message: "Sẵn sàng bản xem trước.",
  };
}

export function normalizeAndValidateUserEdit(rawInput: string): EditValidationResult {
  if (typeof rawInput !== "string") {
    return {
      valid: false,
      normalizedText: "",
      scalarCount: 0,
      byteCount: 0,
      errorCode: "EMPTY_TEXT",
    };
  }

  // 1. CRLF -> LF, then Unicode NFC
  const normalized = rawInput.replace(/\r\n/g, "\n").replace(/\r/g, "\n").normalize("NFC");

  if (normalized.trim().length === 0) {
    return {
      valid: false,
      normalizedText: normalized,
      scalarCount: 0,
      byteCount: 0,
      errorCode: "EMPTY_TEXT",
    };
  }

  // 2. Control character checks (C0 except LF (\n = \u000A), DEL, C1)
  if (FORBIDDEN_C0_C1_DEL.test(normalized)) {
    return {
      valid: false,
      normalizedText: normalized,
      scalarCount: 0,
      byteCount: 0,
      errorCode: "FORBIDDEN_CONTROL_CHAR",
    };
  }

  // 3. Unicode Bidi override / isolate controls
  if (FORBIDDEN_BIDI.test(normalized)) {
    return {
      valid: false,
      normalizedText: normalized,
      scalarCount: 0,
      byteCount: 0,
      errorCode: "FORBIDDEN_BIDI_CONTROL",
    };
  }

  // 4. Scalar count (Unicode code points)
  const scalarCount = Array.from(normalized).length;
  if (scalarCount > MAX_UNICODE_SCALARS) {
    return {
      valid: false,
      normalizedText: normalized,
      scalarCount,
      byteCount: 0,
      errorCode: "EXCEEDS_MAX_SCALARS",
    };
  }

  // 5. UTF-8 byte count
  const byteCount = new TextEncoder().encode(normalized).length;
  if (byteCount > MAX_UTF8_BYTES) {
    return {
      valid: false,
      normalizedText: normalized,
      scalarCount,
      byteCount,
      errorCode: "EXCEEDS_MAX_BYTES",
    };
  }

  return {
    valid: true,
    normalizedText: normalized,
    scalarCount,
    byteCount,
    errorCode: null,
  };
}
