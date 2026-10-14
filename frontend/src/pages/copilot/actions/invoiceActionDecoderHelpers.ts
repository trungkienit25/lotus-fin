/**
 * Pure decoder helpers: source parsing, row parsing and primitives.
 */
import type {
  InvoiceRowVm,
  SourceEvidence,
  UnavailableVm,
} from "./invoiceActionTypes.ts";
import { MESSAGES } from "./invoiceActionTypes.ts";

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f-\u009f]/g;

type Obj = Record<string, unknown>;
export const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
export const hasOnly = (o: Obj, allowed: readonly string[], required: readonly string[] = allowed) =>
  Object.keys(o).every((k) => allowed.includes(k)) && required.every((k) => k in o);

export function safeText(value: unknown, max = 128): string {
  if (typeof value !== "string") return "";
  return value.replace(CONTROL, "").slice(0, max);
}

export function isCalendarDate(s: unknown): s is string {
  if (typeof s !== "string" || !ISO_DATE.test(s)) return false;
  const d = new Date(s + "T00:00:00Z");
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}

export function isCanonicalUtc(s: unknown): s is string {
  if (typeof s !== "string") return false;
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|\+00:00)$/.test(s)) return false;
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return false;
  const iso = d.toISOString();
  return iso === s || iso.replace(".000Z", "Z") === s || iso.replace(".000Z", "+00:00") === s;
}

export const dayNumber = (s: string) => Math.floor(Date.parse(s + "T00:00:00Z") / 86400000);
export const str = (v: unknown, max: number): v is string => typeof v === "string" && v.length >= 1 && v.length <= max;

export class Invalid extends Error {}
export const bad = (): never => { throw new Invalid("invalid"); };

export function failUnavailable(reason: string, cid: string | null = null): UnavailableVm {
  const message = (MESSAGES as Record<string, string>)[reason] ?? MESSAGES.NOT_AVAILABLE;
  return { kind: "unavailable", reason, message, cid };
}

export function isObservationUtc(s: unknown): s is string {
  if (typeof s !== "string") return false;
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|\+00:00)$/.exec(s);
  if (!m) return false;
  const year = parseInt(m[1], 10);
  const month = parseInt(m[2], 10);
  const day = parseInt(m[3], 10);
  const hour = parseInt(m[4], 10);
  const minute = parseInt(m[5], 10);
  const second = parseInt(m[6], 10);
  if (month < 1 || month > 12) return false;
  if (day < 1 || day > 31) return false;
  if (hour > 23 || minute > 59 || second > 59) return false;
  const d = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
  if (d.getUTCFullYear() !== year || (d.getUTCMonth() + 1) !== month || d.getUTCDate() !== day) return false;
  return true;
}

const SOURCE_KEYS = [
  "mode", "verification", "product_ref", "site_ref", "connection_ref", "connection_version",
  "projection_version", "observed_at", "timezone", "coverage", "consistency",
] as const;

export function parseSource(raw: unknown, coverage: "PAGE_COMPLETE" | "INCOMPLETE", allowDemo: boolean): SourceEvidence {
  if (!isObj(raw) || !hasOnly(raw, SOURCE_KEYS)) return bad();
  if (raw.mode !== "ERP_READ" && !(allowDemo && raw.mode === "DEMO_ISOLATED")) return bad();
  if (raw.verification !== "AUTHORIZED_READ" || raw.projection_version !== "invoice.min.v1"
    || raw.consistency !== "LIVE_KEYSET" || raw.coverage !== coverage) return bad();
  for (const k of ["product_ref", "site_ref", "connection_ref"] as const) if (!str(raw[k], 128)) return bad();
  if (!str(raw.connection_version, 64) || !str(raw.observed_at, 64) || !str(raw.timezone, 64)) return bad();
  if (!isObservationUtc(raw.observed_at)) return bad();
  return {
    sourceMode: raw.mode as string,
    observedAt: safeText(raw.observed_at, 64),
    timezone: safeText(raw.timezone, 64),
    siteRef: raw.site_ref as string,
    productRef: raw.product_ref as string,
    connectionRef: raw.connection_ref as string,
    connectionVersion: raw.connection_version as string,
  };
}

const ROW_KEYS = ["invoice_type", "invoice_id", "posting_date", "docstatus", "record_version", "selection_ref"] as const;
export const DOC_KEYS = ["invoice_type", "invoice_id", "posting_date", "docstatus", "record_version"] as const;

export function parseCore(o: unknown, keys: readonly string[], required: readonly string[]) {
  if (!isObj(o) || !hasOnly(o, keys, required)) return bad();
  if (o.invoice_type !== "SALES" || !str(o.invoice_id, 128) || !isCalendarDate(o.posting_date)
    || (o.docstatus !== 0 && o.docstatus !== 1) || !str(o.record_version, 64)) return bad();
  return o as Obj & { invoice_id: string; posting_date: string; docstatus: 0 | 1; record_version: string };
}

export function parseRow(o: unknown): InvoiceRowVm {
  const r = parseCore(o, ROW_KEYS, ROW_KEYS.filter((k) => k !== "selection_ref"));
  const ref = r.selection_ref ?? null;
  if (ref !== null && !str(ref, 2048)) return bad();
  return {
    invoiceId: r.invoice_id,
    postingDate: r.posting_date,
    docstatus: r.docstatus,
    recordVersion: r.record_version,
    selectionRef: ref as string | null,
  };
}
