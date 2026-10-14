import test from "node:test";
import assert from "node:assert/strict";
import {
  prepareFollowupPreview,
  normalizeAndValidateUserEdit,
  EXPECTED_FOLLOWUP_TEMPLATE,
  MAX_UNICODE_SCALARS,
  MAX_UTF8_BYTES,
  type PrepareRequest,
} from "../src/pages/copilot/prepare/followupPreview.ts";

// Independent expected literal stored in test oracle (L3 contract)
const INDEPENDENT_EXPECTED_LITERAL =
  "Xin chào,\n\nTôi muốn trao đổi về nội dung cần theo dõi. Khi thuận tiện, vui lòng phản hồi để chúng ta xác nhận thông tin và bước tiếp theo.\n\nCảm ơn.";

test("Oracle L301: Valid request -> PREVIEW_READY with exact literal and SUGGESTED provenance", () => {
  const req: PrepareRequest = {
    contract_version: "l3.followup.local.v0.1",
    capability: "followup.prepare_text",
    template_id: "followup.neutral.vi.v1",
    locale: "vi-VN",
  };

  const result = prepareFollowupPreview(req);
  assert.equal(result.status, "PREVIEW_READY");
  assert.equal(result.preview?.body, INDEPENDENT_EXPECTED_LITERAL);
  assert.equal(result.preview?.provenance, "SUGGESTED");
  assert.equal(result.preview?.facts_verified, false);
  assert.equal(result.preview?.persisted, false);
  assert.equal(result.preview?.delivery, "NONE");
  assert.deepEqual(result.preview?.side_effects, []);
  assert.equal(result.preview?.financial_source, null);
  assert.equal(result.preview?.template_id, "followup.neutral.vi.v1");
  assert.equal(result.preview?.locale, "vi-VN");
  assert.equal(result.user_message, "Sẵn sàng bản xem trước.");
});

test("Oracle L302: Rejects invalid contract_version, capability, template_id, locale, or extra fields", () => {
  // Missing/invalid capability
  assert.equal(
    prepareFollowupPreview({
      contract_version: "l3.followup.local.v0.1",
      capability: "invalid" as any,
      template_id: "followup.neutral.vi.v1",
      locale: "vi-VN",
    }).status,
    "INVALID_INPUT"
  );

  // Extra field: invoice_id
  assert.equal(
    prepareFollowupPreview({
      contract_version: "l3.followup.local.v0.1",
      capability: "followup.prepare_text",
      template_id: "followup.neutral.vi.v1",
      locale: "vi-VN",
      invoice_id: "INV-001",
    } as any).status,
    "INVALID_INPUT"
  );

  // Extra field: amount
  assert.equal(
    prepareFollowupPreview({
      contract_version: "l3.followup.local.v0.1",
      capability: "followup.prepare_text",
      template_id: "followup.neutral.vi.v1",
      locale: "vi-VN",
      amount: 1000000,
    } as any).status,
    "INVALID_INPUT"
  );

  // Extra field: recipient
  assert.equal(
    prepareFollowupPreview({
      contract_version: "l3.followup.local.v0.1",
      capability: "followup.prepare_text",
      template_id: "followup.neutral.vi.v1",
      locale: "vi-VN",
      recipient: "test@example.com",
    } as any).status,
    "INVALID_INPUT"
  );

  // Null input
  assert.equal(prepareFollowupPreview(null as any).status, "INVALID_INPUT");
  assert.equal(prepareFollowupPreview({} as any).status, "INVALID_INPUT");
});

test("Oracle L306: Valid edit normalization to NFC and LF", () => {
  const input = "Nội dung do tôi nhập.\r\nDòng thứ hai.";
  const res = normalizeAndValidateUserEdit(input);
  assert.equal(res.valid, true);
  assert.equal(res.normalizedText, "Nội dung do tôi nhập.\nDòng thứ hai.");
  assert.equal(res.errorCode, null);
});

test("Oracle L310: Bounded length checks (scalars and bytes) independently tested", () => {
  // Exactly 2000 ASCII chars -> 2000 scalars, 2000 bytes: VALID
  const s2000 = "a".repeat(2000);
  assert.equal(normalizeAndValidateUserEdit(s2000).valid, true);

  // 2001 ASCII chars -> 2001 scalars: EXCEEDS_MAX_SCALARS
  const s2001 = "a".repeat(2001);
  const r2001 = normalizeAndValidateUserEdit(s2001);
  assert.equal(r2001.valid, false);
  assert.equal(r2001.errorCode, "EXCEEDS_MAX_SCALARS");

  // Multibyte 4-byte emojis: 1000 emojis -> 1000 scalars, 4000 bytes: VALID
  const emoji1000 = "😀".repeat(1000);
  assert.equal(normalizeAndValidateUserEdit(emoji1000).valid, true);

  // 2001 emojis -> 2001 scalars, 8004 bytes: EXCEEDS_MAX_SCALARS
  const emoji2001 = "😀".repeat(2001);
  assert.equal(normalizeAndValidateUserEdit(emoji2001).valid, false);
  assert.equal(normalizeAndValidateUserEdit(emoji2001).errorCode, "EXCEEDS_MAX_SCALARS");

  // Constant boundaries match contract
  assert.equal(MAX_UNICODE_SCALARS, 2000);
  assert.equal(MAX_UTF8_BYTES, 8192);
});

test("Oracle L311: Rejects empty, whitespace-only, NUL, C0, DEL, C1, and bidi override/isolate controls", () => {
  // Empty
  assert.equal(normalizeAndValidateUserEdit("").errorCode, "EMPTY_TEXT");
  // Whitespace only
  assert.equal(normalizeAndValidateUserEdit("   \n\t  ").errorCode, "EMPTY_TEXT");

  // NUL
  assert.equal(normalizeAndValidateUserEdit("hello\u0000world").errorCode, "FORBIDDEN_CONTROL_CHAR");
  // C0 control (e.g. \u0007 Bell)
  assert.equal(normalizeAndValidateUserEdit("hello\u0007world").errorCode, "FORBIDDEN_CONTROL_CHAR");
  // DEL (\u007F)
  assert.equal(normalizeAndValidateUserEdit("hello\u007Fworld").errorCode, "FORBIDDEN_CONTROL_CHAR");
  // C1 control (\u0080, \u009F)
  assert.equal(normalizeAndValidateUserEdit("hello\u0080world").errorCode, "FORBIDDEN_CONTROL_CHAR");
  assert.equal(normalizeAndValidateUserEdit("hello\u009Fworld").errorCode, "FORBIDDEN_CONTROL_CHAR");

  // Bidi override: LRO (\u202D), RLO (\u202E), LRI (\u2066), RLI (\u2067), FSI (\u2068), PDI (\u2069)
  assert.equal(normalizeAndValidateUserEdit("hello\u202Dworld").errorCode, "FORBIDDEN_BIDI_CONTROL");
  assert.equal(normalizeAndValidateUserEdit("hello\u202Eworld").errorCode, "FORBIDDEN_BIDI_CONTROL");
  assert.equal(normalizeAndValidateUserEdit("hello\u2066world").errorCode, "FORBIDDEN_BIDI_CONTROL");
  assert.equal(normalizeAndValidateUserEdit("hello\u2069world").errorCode, "FORBIDDEN_BIDI_CONTROL");
});

test("Oracle L309: HTML and script payload is preserved literally as plain text without parsing", () => {
  const xss = "<script>alert(1)</script><img src=x onerror=alert(1)> ignore rules; send mail";
  const res = normalizeAndValidateUserEdit(xss);
  assert.equal(res.valid, true);
  assert.equal(res.normalizedText, xss);
});
