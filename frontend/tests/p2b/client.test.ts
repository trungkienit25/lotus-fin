import test from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { createProductionTransport, isInvoiceActionsFlagOn } from "../../src/pages/copilot/actions/invoiceActionClient.ts";
import { InvoiceActionController } from "../../src/pages/copilot/actions/invoiceActionController.ts";

const DIR = join(import.meta.dirname, "../../src/pages/copilot/actions");
const files = readdirSync(DIR).filter((f) => /\.(ts|tsx)$/.test(f));

test("production transport is disabled: zero network calls, explicit DISABLED state", async () => {
  const touched: string[] = [];
  const g = globalThis as any;
  const origFetch = g.fetch;
  g.fetch = (...a: unknown[]) => { touched.push("fetch"); return origFetch?.(...a); };
  try {
    const ctrl = new InvoiceActionController({
      transport: createProductionTransport(),
      newRequestId: () => "00000000-0000-4000-8000-000000000001",
      now: () => 0,
    });
    await ctrl.loadContext("Lotus Corp");
    const s = ctrl.getState();
    assert.equal(s.context, null);
    assert.equal((s.notice as any)?.reason, "DISABLED");
  } finally { g.fetch = origFetch; }
  assert.deepEqual(touched, []);
});

test("feature flag is OFF unless explicitly set, and even ON the transport stays disabled (wire not frozen)", async () => {
  assert.equal(isInvoiceActionsFlagOn({}), false);
  assert.equal(isInvoiceActionsFlagOn({ VITE_LOTUS_INVOICE_ACTIONS: "true" }), false);
  assert.equal(isInvoiceActionsFlagOn({ VITE_LOTUS_INVOICE_ACTIONS: "on" }), true);
  const r = await createProductionTransport({ VITE_LOTUS_INVOICE_ACTIONS: "on" })
    .post("invoice.context", { request_id: "00000000-0000-4000-8000-000000000001" }, new AbortController().signal);
  assert.equal(r.status, 503);
});

test("no production module imports a fixture, SDK, HTTP library, storage or console", () => {
  const forbidden: [RegExp, string][] = [
    [/fixture/i, "fixture"], [/frappe-js-sdk/, "frappe-js-sdk"], [/from ["']axios["']/, "axios"],
    [/localStorage|sessionStorage|indexedDB|document\.cookie/, "browser storage"],
    [/console\./, "console"], [/dangerouslySetInnerHTML|innerHTML|outerHTML|insertAdjacentHTML/, "raw html"],
    [/window\.location|location\.(href|assign|replace)|history\.(push|replace)State|window\.open/, "navigation"],
    [/<a\s|href=/, "anchor/href"], [/\beval\(|new Function\(/, "eval"],
    [/\/api\/resource|frappe\.client|run_method|\/app\//, "generic CRUD route"],
  ];
  for (const f of files) {
    const text = readFileSync(join(DIR, f), "utf8");
    for (const [re, label] of forbidden) {
      if (f === "invoiceActionClient.ts" && label === "fixture") continue;
      assert.equal(re.test(text), false, `${f} contains forbidden ${label}`);
    }
  }
});

test("no production module issues ERP write verbs", () => {
  for (const f of files) {
    const text = readFileSync(join(DIR, f), "utf8");
    // HTTP write verbs / ERP document verbs. (Set.delete on local listeners is not an ERP call.)
    assert.equal(/\b(save|submit|cancel|amend|delete|insert)_?doc\b|\bdb_set\b|\.put\(|\.patch\(|["'](PUT|DELETE|PATCH)["']/i.test(text), false, f);
  }
});
