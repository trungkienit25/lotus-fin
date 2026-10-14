import test from "node:test";
import assert from "node:assert/strict";
import { bootstrapSession, clearSessionBootstrap, SessionBootstrapError } from "../src/providers/sessionBootstrap.ts";
import { createHttpTransport } from "../src/pages/copilot/actions/invoiceActionClient.ts";
import { parseInvoiceOutcome } from "../src/pages/copilot/actions/invoiceActionDecoders.ts";

const RID = "11111111-1111-4111-8111-111111111111";
const CID = "22222222-2222-4222-8222-222222222222";
const session = { user: "ordinary@example.test", csrf_token: "session-token" };
const outcome = { message: { contract_version: "p1.invoice.v1", status: "NOT_AVAILABLE",
  reason_code: "CAPABILITY_DISABLED", request_id: RID, correlation_id: CID,
  capability: "invoice.context", source: null, data: null, context_version: null, user_message: "disabled" } };
const reply = (data: unknown, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { "Content-Type": "application/json", "x-correlation-id": CID },
});
const opts = { requestId: RID, capability: "invoice.context" as const };

test("bootstrap is same origin, no-store, cookie bound, strict and refreshed each time", async () => {
  const original = globalThis.fetch;
  const calls: RequestInit[] = [];
  globalThis.fetch = async (url, init) => {
    assert.equal(url, "/copilot/session"); calls.push(init!); return reply(session);
  };
  try {
    await bootstrapSession(); await bootstrapSession();
    assert.equal(calls.length, 2);
    assert.ok(calls.every(c => c.cache === "no-store" && c.credentials === "same-origin" && c.redirect === "error"));
  } finally { globalThis.fetch = original; }
});

test("actual bootstrap status fails closed for guests and malformed bodies", async () => {
  const original = globalThis.fetch;
  try {
    for (const [body, status] of [[{}, 401], [null, 200], [{ ...session, user: "Guest" }, 200],
      [{ ...session, extra: "invalid" }, 200], [{ ...session, csrf_token: "" }, 200]] as const) {
      globalThis.fetch = async () => reply(body, status);
      await assert.rejects(bootstrapSession(), SessionBootstrapError);
    }
  } finally { globalThis.fetch = original; }
});

test("cold CORE transport bootstraps token, posts once and preserves exact 503 envelope and CID", async () => {
  const original = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    calls.push(String(url));
    if (url === "/copilot/session") return reply(session);
    assert.equal(init?.method, "POST");
    assert.equal((init?.headers as Record<string, string>)["X-Frappe-CSRF-Token"], session.csrf_token);
    assert.equal(init?.credentials, "same-origin");
    return reply(outcome, 503);
  };
  try {
    const result = await createHttpTransport().post("invoice.context", { request_id: RID }, new AbortController().signal);
    assert.equal(result.status, 503); assert.deepEqual(result.data, outcome);
    assert.equal(result.headers?.["x-correlation-id"], CID);
    assert.deepEqual(calls, ["/copilot/session", "/api/method/lotus_fin.api.invoice_actions_api.get_context", "/copilot/session"]);
    assert.equal(parseInvoiceOutcome(result.data, { ...opts, httpStatus: result.status }).kind, "unavailable");
  } finally { globalThis.fetch = original; }
});

test("guest bootstrap denies without issuing native POST", async () => {
  const original = globalThis.fetch;
  let count = 0;
  globalThis.fetch = async () => { count++; return reply({ exc_type: "AuthenticationError" }, 401); };
  try {
    const result = await createHttpTransport().post("invoice.context", {}, new AbortController().signal);
    assert.equal(count, 1); assert.equal(result.status, 401);
    assert.equal(parseInvoiceOutcome(result.data, { ...opts, httpStatus: result.status }).kind, "denied");
  } finally { globalThis.fetch = original; }
});

test("logout/login generation fences late bootstrap and native replies", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => { clearSessionBootstrap(); return reply(session); };
  try { await assert.rejects(bootstrapSession(), { name: "AbortError" }); }
  finally { globalThis.fetch = original; }
});

test("external session change while a POST is in flight fences its reply", async () => {
  const original = globalThis.fetch;
  let reads = 0;
  globalThis.fetch = async url => url === "/copilot/session"
    ? reply({ ...session, csrf_token: ++reads === 1 ? "old" : "new" }) : reply(outcome, 503);
  try {
    await assert.rejects(createHttpTransport().post("invoice.context", {}, new AbortController().signal), { name: "AbortError" });
  } finally { globalThis.fetch = original; }
});

test("framework CSRF 400 is denied; arbitrary 400 and corrupt invoice envelopes remain invalid", () => {
  const csrf = parseInvoiceOutcome({ exc_type: "CSRFTokenError", _server_messages: "private text" }, { ...opts, httpStatus: 400 });
  assert.equal(csrf.kind, "denied"); assert.equal(csrf.reason, "CSRF_OR_ORIGIN_DENIED");
  assert.ok(!csrf.message.includes("private text"));
  for (const body of [{ exc_type: "ValidationError" }, { ...outcome, exc_type: "CSRFTokenError" },
    { message: { ...outcome.message, request_id: CID } }]) {
    assert.equal(parseInvoiceOutcome(body, { ...opts, httpStatus: 400 }).reason, "INVALID_RESPONSE");
  }
});

test("CSRF rejection is not retried and retains real HTTP400", async () => {
  const original = globalThis.fetch;
  let posts = 0;
  globalThis.fetch = async url => {
    if (url === "/copilot/session") return reply(session);
    posts++; return reply({ exc_type: "CSRFTokenError" }, 400);
  };
  try {
    const result = await createHttpTransport().post("invoice.context", {}, new AbortController().signal);
    assert.equal(result.status, 400); assert.equal(posts, 1);
    assert.equal(parseInvoiceOutcome(result.data, { ...opts, httpStatus: result.status }).kind, "denied");
  } finally { globalThis.fetch = original; }
});
