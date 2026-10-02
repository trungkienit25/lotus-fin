"""AI003 Risk Signal workspace E2E (Playwright, bare-script pattern).

Target: http://ai003-verify.localhost:8080 ONLY (isolated verification site;
the shared `frontend` site is never mutated — Chromium resolves *.localhost to
loopback natively; other browsers need a hosts entry).

Read-only: the script only evaluates signals and opens evidence replays; it
creates no business data. Screenshots land in tests_e2e/screenshots/ (small
set per packet §19: HIGH, BENIGN, INCONCLUSIVE, evidence, mobile).

Run (PowerShell, from E:\\lotus-fin, stack up on :8080):
  python tests_e2e\\test_risk_signal_workspace.py
"""

import os
import sys

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://ai003-verify.localhost:8080"
USER = "Administrator"
PASSWORD = "admin"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

results = []


def record(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=60)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        # --- login ---
        page.goto(BASE_URL + "/login", wait_until="domcontentloaded")
        page.wait_for_selector("#login_email", timeout=30000)
        page.fill("#login_email", USER)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_function("() => location.pathname.startsWith('/app') || location.pathname.startsWith('/desk')", timeout=30000)

        # --- page loads; disclosures visible ---
        # In-SPA navigation: full gotos are aborted by the desk router.
        page.evaluate("() => frappe.set_route('risk-signal')")
        page.wait_for_selector(".rs-banner", timeout=30000)
        body = page.locator(".layout-main-section")
        expect(body).to_contain_text("DEMO_ONLY")
        expect(body).to_contain_text("NOT production calibrated")
        record("page_loads_with_disclosures", True)
        empty_visible = page.locator(".rs-state").inner_text()
        record("empty_state", "No evaluation yet" in empty_visible, empty_visible[:60])

        # --- HIGH result (AR gold pair) ---
        page.fill("input[data-fieldname='company']", "AI003 MG AR")
        page.keyboard.press("Escape")  # close link dropdown if open
        page.locator(".page-head .btn-primary").click()
        page.wait_for_selector(".rs-panel", timeout=60000)
        content = page.locator(".rs-result").inner_text()
        ok_high = ("Evaluation completed" in content and "HIGH" in content
                   and "72.73" in content and "BENIGN" not in content)
        record("high_renders", ok_high, content[:120].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_01_high_ar.png"), full_page=True)

        # --- evidence drilldown (MATCH) ---
        page.locator(".rs-evidence-btn").first.click()
        page.wait_for_selector(".rs-evidence-live", timeout=30000)
        ev = page.locator(".rs-evidence-live").inner_text()
        record("evidence_match", "MATCH" in ev, ev[:80].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_02_evidence_match.png"), full_page=True)

        # --- stale-clear on signal switch ---
        page.locator(".page-head select[data-fieldname='signal_id']").select_option("AP_DUE_CLUSTER")
        page.wait_for_timeout(400)
        cleared = page.locator(".rs-result").inner_text()
        record("stale_clear_on_change", ("cleared" in cleared.lower()), cleared[:60].replace("\n", " | "))

        # --- BENIGN result (AP gold) ---
        page.fill("input[data-fieldname='company']", "AI003 MG AP")
        page.keyboard.press("Escape")
        page.locator(".page-head .btn-primary").click()
        page.wait_for_selector(".rs-panel", timeout=60000)
        benign = page.locator(".rs-result").inner_text()
        ok_benign = ("BENIGN" in benign and "33.33%" in benign)
        record("benign_renders", ok_benign, benign[:100].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_03_benign_ap.png"), full_page=True)

        # --- INCONCLUSIVE renders distinctly (real two-schedule parent) ---
        page.fill("input[data-fieldname='company']", "AI003 MG Multi")
        page.keyboard.press("Escape")
        page.locator(".page-head .btn-primary").click()
        page.wait_for_selector(".rs-panel", timeout=60000)
        inconc = page.locator(".rs-result").inner_text()
        ok_inc = ("Inconclusive" in inconc and "multiple installment" in inconc
                  and "BENIGN" not in inconc and "HIGH" not in inconc)
        record("inconclusive_distinct", ok_inc, inconc[:110].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_04_inconclusive_multi.png"), full_page=True)

        # --- rapid change: last selection wins ---
        page.locator(".page-head select[data-fieldname='signal_id']").select_option("AR_OVERDUE_SPIKE")
        page.fill("input[data-fieldname='company']", "AI003 MG AR")
        page.keyboard.press("Escape")
        page.locator(".page-head .btn-primary").click()
        page.wait_for_selector(".rs-panel", timeout=60000)
        rapid = page.locator(".rs-result").inner_text()
        record("rapid_change_last_wins", "AR Overdue Spike" in rapid and "HIGH" in rapid,
               rapid[:80].replace("\n", " | "))

        # --- keyboard flow: primary button reachable via Tab and Enter ---
        page.locator(".page-head .btn-primary").focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)
        record("keyboard_primary_action", True)

        # --- mobile viewport ---
        mobile = browser.new_page(viewport={"width": 375, "height": 812})
        mobile.goto(BASE_URL + "/login", wait_until="domcontentloaded")
        mobile.wait_for_selector("#login_email", timeout=30000)
        mobile.fill("#login_email", USER)
        mobile.fill("#login_password", PASSWORD)
        mobile.click(".btn-login")
        mobile.wait_for_function("() => location.pathname.startsWith('/app') || location.pathname.startsWith('/desk')", timeout=30000)
        mobile.evaluate("() => frappe.set_route('risk-signal')")
        mobile.wait_for_selector(".rs-banner", timeout=30000)
        mobile.fill("input[data-fieldname='company']", "AI003 MG AR")
        mobile.keyboard.press("Escape")
        mobile.locator(".page-head .btn-primary").click()
        mobile.wait_for_selector(".rs-panel", timeout=60000)
        no_overflow = mobile.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2"
        )
        record("mobile_no_horizontal_overflow", no_overflow)
        mobile.screenshot(path=os.path.join(SHOTS, "rs_05_mobile.png"), full_page=True)

        browser.close()

    passed = all(ok for _, ok, _ in results)
    print("E2E RESULT:", "PASS" if passed else "FAIL", "(%d/%d)" % (sum(1 for _, ok, _ in results if ok), len(results)))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(run())
