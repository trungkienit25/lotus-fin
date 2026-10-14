/**
 * Pure decoders and contract validators for Sales Invoice outcomes.
 *
 * Implements strict schema validation, source verification, and pinning
 * for P2-B findings (F01, F02, F03).
 */
import type {
  InvoiceVm,
  MetaVm,
  ParseOptions,
} from "./invoiceActionTypes.ts";
import { MESSAGES } from "./invoiceActionTypes.ts";
import {
  bad,
  failUnavailable,
  hasOnly,
  isObj,
  parseSource,
  str,
} from "./invoiceActionDecoderHelpers.ts";
import {
  parseContextData,
  parseOpenData,
  parseSearchData,
} from "./invoiceActionPayloadDecoders.ts";

export { isObj, hasOnly, safeText, isCalendarDate, isCanonicalUtc, parseSource, parseRow } from "./invoiceActionDecoderHelpers.ts";
export { parseSearchData, parseOpenData, parseContextData } from "./invoiceActionPayloadDecoders.ts";

const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const STATUS_REASONS: Record<string, readonly string[]> = {
  OK: ["RESULTS_FOUND", "EMPTY_RESULT", "DOCUMENT_READY", "CONTEXT_READY"],
  PARTIAL: ["COVERAGE_INCOMPLETE"],
  FORBIDDEN: ["AUTH_REQUIRED", "CSRF_OR_ORIGIN_DENIED", "COMPANY_DENIED", "CAPABILITY_DENIED", "ACCESS_DENIED"],
  SOURCE_ERROR: ["SOURCE_FAILURE", "INVALID_PROVIDER_RESPONSE"],
  TIMEOUT: ["DEADLINE_EXCEEDED"],
  NOT_AVAILABLE: [
    "INVALID_REQUEST", "CONTEXT_REQUIRED", "CONTEXT_CHANGED", "STALE_SELECTION", "STALE_CURSOR",
    "DOCUMENT_UNAVAILABLE", "PROJECTION_UNAVAILABLE", "TARGET_UNQUALIFIED", "CAPABILITY_DISABLED",
    "UNSUPPORTED_INTENT", "INVALID_OUTCOME",
  ],
};
const EXPIRED_REASONS = new Set(["CONTEXT_CHANGED", "STALE_SELECTION", "STALE_CURSOR", "CONTEXT_REQUIRED"]);

const ENV_KEYS = [
  "contract_version", "status", "reason_code", "correlation_id", "request_id", "capability",
  "source", "context_version", "data", "user_message",
];

export function parseInvoiceOutcome(raw: unknown, opts: ParseOptions): InvoiceVm {
  let cid: string | null = null;
  try {
    if (opts.httpStatus === 401 || opts.httpStatus === 403) {
      return { kind: "denied", reason: "ACCESS_DENIED", message: MESSAGES.DENIED, cid: null };
    }
    if (opts.httpStatus === 400 && isObj(raw) && raw.exc_type === "CSRFTokenError"
        && !("message" in raw && isObj(raw.message))) {
      return { kind: "denied", reason: "CSRF_OR_ORIGIN_DENIED",
        message: "Your session could not be verified. Sign in again and retry.", cid: null };
    }
    let env = raw;
    if (isObj(env) && Object.keys(env).length === 1 && "message" in env) env = env.message;
    if (!isObj(env) || !hasOnly(env, ENV_KEYS, [
      "contract_version", "status", "reason_code", "correlation_id",
      "request_id", "capability", "user_message",
    ])) return bad();

    if (typeof env.correlation_id === "string" && UUID4.test(env.correlation_id)) cid = env.correlation_id;

    const status = env.status;
    const reason = env.reason_code;
    if (typeof status !== "string" || typeof reason !== "string" || !STATUS_REASONS[status]?.includes(reason)) return bad();
    if (status === "FORBIDDEN") {
      return { kind: "denied", reason, message: MESSAGES.DENIED, cid };
    }
    if (env.contract_version !== "p1.invoice.v1" || cid === null || typeof env.request_id !== "string"
      || !UUID4.test(env.request_id) || env.request_id.toLowerCase() !== opts.requestId.toLowerCase()
      || env.capability !== opts.capability || typeof env.user_message !== "string") return bad();
    if (opts.cidHeader !== undefined && opts.cidHeader !== null && String(opts.cidHeader).toLowerCase() !== cid.toLowerCase()) return bad();

    if (status === "OK" || status === "PARTIAL") {
      if (typeof env.context_version !== "string" || !str(env.context_version, 128)) return bad();
      if (opts.httpStatus !== undefined && opts.httpStatus !== 200) return bad();
      if (env.data == null) return bad();

      // F03 rule: If expectedContext is given, outer context_version must match expectedContext.contextVersion
      if (opts.expectedContext) {
        if (env.context_version !== opts.expectedContext.contextVersion) return bad();
      }

      const src = parseSource(env.source, status === "OK" ? "PAGE_COMPLETE" : "INCOMPLETE", opts.allowDemoSource === true);

      // F03 rule: If expectedContext is given, source anchors must match expectedContext source
      if (opts.expectedContext) {
        if (src.siteRef !== opts.expectedContext.siteRef
          || src.productRef !== opts.expectedContext.productRef
          || src.connectionRef !== opts.expectedContext.connectionRef
          || src.connectionVersion !== opts.expectedContext.connectionVersion
          || src.sourceMode !== opts.expectedContext.sourceMode
          || src.timezone !== opts.expectedContext.timezone) {
          return bad();
        }
      }

      const meta: MetaVm = { cid, requestId: env.request_id, ...src };
      if (opts.capability === "invoice.context") {
        return status === "OK" && reason === "CONTEXT_READY"
          ? parseContextData(env.data, meta, env.context_version as string | null | undefined)
          : bad();
      }
      if (opts.capability === "invoice.open") {
        return status === "OK" && reason === "DOCUMENT_READY"
          ? parseOpenData(env.data, meta, opts.expectedContext)
          : bad();
      }
      return parseSearchData(env.data, status, reason, meta);
    }

    // failure statuses must not carry data/source
    if (env.data != null || env.source != null) return bad();
    if (status === "SOURCE_ERROR") return failUnavailable("SOURCE_ERROR", cid);
    if (status === "TIMEOUT") return failUnavailable("TIMEOUT", cid);
    if (EXPIRED_REASONS.has(reason)) return { kind: "expired", reason, message: MESSAGES.EXPIRED, cid };
    if (reason === "INVALID_REQUEST") return failUnavailable("INVALID_REQUEST", cid);
    if (reason === "CAPABILITY_DISABLED") return failUnavailable("DISABLED", cid);
    return failUnavailable("NOT_AVAILABLE", cid);
  } catch {
    return failUnavailable("INVALID_RESPONSE", cid);
  }
}
