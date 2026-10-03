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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://ai003-verify.localhost:8080"
USER = "Administrator"
PASSWORD = "admin"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
VIDEOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")

results = []


def record(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS" if ok else "FAIL"), name, detail)


def hold_first_get_risk_signal(page, held, abort_on_release=False):
    """Hold the FIRST get_risk_signal POST at the browser (it is not sent
    until released) — later requests pass through untouched, including after
    the release (single-shot armed flag; the harness must never re-arm and
    swallow a subsequent evaluation). On release the held request continues to
    the real server, so every financial result the UI sees is the server's
    real response; only the delivery ORDER is controlled.
    abort_on_release=True instead aborts the held request to produce a real
    transport error at release time."""
    held["armed"] = True
    held["abort_on_release"] = abort_on_release

    def handler(route):
        if held.get("armed"):
            held["armed"] = False
            held["route"] = route
        else:
            route.continue_()
    page.route("**/api/method/lotus_fin.api.ai_insights.get_risk_signal", handler)


def release_held(held):
    route = held.pop("route", None)
    if route is None:
        return
    if held.pop("abort_on_release", False):
        route.abort("connectionreset")
    else:
        route.continue_()


def set_date(page, value):
    page.fill("input[data-fieldname='as_of_date']", value)
    page.locator("input[data-fieldname='as_of_date']").evaluate(
        "el => el.dispatchEvent(new Event('change'))"
    )


def controller_state(page):
    try:
        return page.evaluate(
            "() => { const c = cur_page.page.controller; return {in_flight: c.in_flight,"
            " seq: c.request_seq, inflight_req: c.in_flight_request}; }"
        )
    except Exception:
        return None


def wait_result_or_fail_with_diag(page, label, timeout=60000):
    try:
        page.wait_for_selector(".rs-result .rs-panel", timeout=timeout)
    except Exception:
        print(f"DIAG[{label}]:", controller_state(page),
              "| state:", page.locator(".rs-state").inner_text()[:120].replace("\n", " | "),
              "| result:", page.locator(".rs-result").inner_text()[:120].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_failure_diag.png"), full_page=True)
        raise


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=60)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=VIDEOS,
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()

        # --- login: redirect-to lands directly on the workspace (no splash stall) ---
        page.goto(BASE_URL + "/login?redirect-to=/app/risk-signal", wait_until="domcontentloaded")
        page.wait_for_selector("#login_email", timeout=30000)
        page.fill("#login_email", USER)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_selector(".rs-banner", timeout=90000)
        body = page.locator(".layout-main-section")
        expect(body).to_contain_text("DEMO_ONLY")
        expect(body).to_contain_text("NOT production calibrated")
        record("page_loads_with_disclosures", True)
        empty_visible = page.locator(".rs-state").inner_text()
        record("empty_state", "No evaluation yet" in empty_visible, empty_visible[:60])

        # --- HIGH result (AR gold pair with explicit as_of_date) ---
        page.locator("select[data-fieldname='signal_id']").select_option("AR_OVERDUE_SPIKE")
        page.fill("input[data-fieldname='company']", "AI003 MG AR")
        page.keyboard.press("Escape")  # close link dropdown if open
        page.fill("input[data-fieldname='as_of_date']", "2026-09-26")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        content = page.locator(".rs-result").inner_text()
        ok_high = ("Evaluation completed" in content and "HIGH" in content
                   and "72.73" in content and "BENIGN" not in content)
        record("high_renders", ok_high, content[:120].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_01_high_ar.png"), full_page=True)

        # Frozen AR semantics: AR result does NOT attach evidence snapshot button
        ar_evidence_btns = page.locator(".rs-evidence-btn").count()
        record("ar_no_evidence_button", ar_evidence_btns == 0, f"count={ar_evidence_btns}")

        # --- stale-clear on signal switch ---
        page.locator("select[data-fieldname='signal_id']").select_option("AP_DUE_CLUSTER")
        page.wait_for_timeout(400)
        cleared = page.locator(".rs-result").inner_text()
        record("stale_clear_on_change", ("cleared" in cleared.lower()), cleared[:60].replace("\n", " | "))

        # --- BENIGN result (AP gold) ---
        page.fill("input[data-fieldname='company']", "AI003 MG AP")
        page.keyboard.press("Escape")
        page.fill("input[data-fieldname='as_of_date']", "2026-09-26")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        benign = page.locator(".rs-result").inner_text()
        ok_benign = ("BENIGN" in benign and "33.33%" in benign)
        record("benign_renders", ok_benign, benign[:100].replace("\n", " | "))
        record("explanation_present", ("AI explanation" in benign or "narrative" in benign or "Continued monitoring" in benign), benign[:80].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_03_benign_ap.png"), full_page=True)

        # --- WATCH result (AP gold at 2026-09-27) ---
        page.fill("input[data-fieldname='as_of_date']", "2026-09-27")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        watch_text = page.locator(".rs-result").inner_text()
        ok_watch = ("WATCH" in watch_text and "50.00%" in watch_text)
        record("watch_renders", ok_watch, watch_text[:100].replace("\n", " | "))

        # --- restore 2026-09-26 for evidence drilldown ---
        page.fill("input[data-fieldname='as_of_date']", "2026-09-26")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)

        # --- evidence drilldown on AP result (MATCH) ---
        page.locator(".rs-evidence-btn").first.click()
        page.wait_for_selector(".rs-evidence-live", timeout=30000)
        ev = page.locator(".rs-evidence-live").inner_text()
        record("evidence_match", "MATCH" in ev, ev[:80].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_02_evidence_match.png"), full_page=True)

        # --- date transition clears stale result ---
        page.fill("input[data-fieldname='as_of_date']", "2026-09-28")
        page.locator("input[data-fieldname='as_of_date']").evaluate("el => el.dispatchEvent(new Event('change'))")
        page.wait_for_timeout(300)
        cleared_date = page.locator(".rs-result").inner_text()
        record("date_transition_clears_stale", "cleared" in cleared_date.lower(), cleared_date[:60].replace("\n", " | "))

        # --- error recovery: empty company validation then recovers ---
        page.fill("input[data-fieldname='company']", "")
        page.evaluate("() => { if (cur_page && cur_page.page && cur_page.page.controller) { cur_page.page.controller.last_typed_company = ''; cur_page.page.controller.company_field.set_value(''); } }")
        page.locator(".page-head .primary-action").click()
        page.wait_for_timeout(300)
        err_msg = page.locator(".rs-result").inner_text()
        record("error_recovery_empty_company_validation", "Select a company" in err_msg, err_msg[:60].replace("\n", " | "))

        # --- INCONCLUSIVE renders distinctly (real two-schedule parent) ---
        page.fill("input[data-fieldname='company']", "AI003 MG Multi")
        page.keyboard.press("Escape")
        page.fill("input[data-fieldname='as_of_date']", "2026-09-26")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        inconc = page.locator(".rs-result").inner_text()
        ok_inc = ("Inconclusive" in inconc and "multiple installment" in inconc
                  and "BENIGN" not in inconc and "HIGH" not in inconc)
        record("inconclusive_distinct", ok_inc, inconc[:110].replace("\n", " | "))
        page.screenshot(path=os.path.join(SHOTS, "rs_04_inconclusive_multi.png"), full_page=True)

        # --- safe denial / FORBIDDEN ---
        page.fill("input[data-fieldname='company']", "Unauthorized Corp")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        denial = page.locator(".rs-result").inner_text()
        record("permission_denial_safe", "FORBIDDEN" in denial or "Access" in denial or "denied" in denial.lower(),
               denial[:80].replace("\n", " | "))

        # --- rapid change: real in-flight request + input change: last request wins ---
        # Request A (AP, 2026-09-26 -> BENIGN 33.33%) is held server-side;
        # the user changes the date (invalidates A), evaluates B (2026-09-27
        # -> WATCH 50.00%), and only then is A's real response delivered.
        # B's result must persist; A must never render.
        page.locator("select[data-fieldname='signal_id']").select_option("AP_DUE_CLUSTER")
        page.fill("input[data-fieldname='company']", "AI003 MG AP")
        page.keyboard.press("Escape")
        set_date(page, "2026-09-26")
        held_a = {}
        hold_first_get_risk_signal(page, held_a)
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-state:has-text('Evaluating')", timeout=15000)
        set_date(page, "2026-09-27")  # invalidates A while it is truly in flight
        page.wait_for_timeout(300)
        record("rapid_inflight_invalidated_not_stuck",
               "Evaluating" not in page.locator(".rs-state").inner_text()
               and "Evaluate Signal" in page.locator(".page-head .primary-action").inner_text())
        page.locator(".page-head .primary-action").click()  # request B allowed after invalidation
        page.wait_for_selector(".rs-result .rs-panel", timeout=60000)
        release_held(held_a)  # A's real success response arrives AFTER B rendered
        page.wait_for_timeout(700)
        final_rapid = page.locator(".rs-result").inner_text()
        record("rapid_change_last_wins",
               "WATCH" in final_rapid and "50.00%" in final_rapid
               and "33.33%" not in final_rapid and "BENIGN" not in final_rapid,
               final_rapid[:100].replace("\n", " | "))
        page.unroute("**/api/method/lotus_fin.api.ai_insights.get_risk_signal")

        # --- stale delayed SUCCESS discarded after date change ---
        page.locator("select[data-fieldname='signal_id']").select_option("AR_OVERDUE_SPIKE")
        page.fill("input[data-fieldname='company']", "AI003 MG AR")
        page.keyboard.press("Escape")
        set_date(page, "2026-09-26")
        held_b = {}
        hold_first_get_risk_signal(page, held_b)
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-state:has-text('Evaluating')", timeout=15000)
        set_date(page, "2026-09-27")
        page.wait_for_timeout(300)
        release_held(held_b)  # real HIGH/72.73 response for 09-26 arrives late
        page.wait_for_timeout(700)
        after_stale = page.locator(".rs-result").inner_text()
        record("stale_success_discarded_after_date_change",
               page.locator(".rs-result .rs-panel").count() == 0
               and "cleared" in after_stale.lower() and "72.73" not in after_stale,
               after_stale[:80].replace("\n", " | "))
        # User can still evaluate the new inputs after invalidation.
        page.locator(".page-head .primary-action").click()
        wait_result_or_fail_with_diag(page, "evaluate_new_inputs_after_invalidation")
        new_date_res = page.locator(".rs-result").inner_text()
        record("evaluate_new_inputs_after_invalidation",
               "2026-09-27" in new_date_res, new_date_res[:90].replace("\n", " | "))
        page.unroute("**/api/method/lotus_fin.api.ai_insights.get_risk_signal")

        # --- stale delayed SUCCESS discarded after signal change ---
        page.locator("select[data-fieldname='signal_id']").select_option("AP_DUE_CLUSTER")
        page.wait_for_timeout(300)
        held_c = {}
        hold_first_get_risk_signal(page, held_c)
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-state:has-text('Evaluating')", timeout=15000)
        page.locator("select[data-fieldname='signal_id']").select_option("AR_OVERDUE_SPIKE")
        page.wait_for_timeout(300)
        release_held(held_c)  # AP success arrives after signal switched to AR
        page.wait_for_timeout(700)
        after_sig = page.locator(".rs-result").inner_text()
        record("stale_success_discarded_after_signal_change",
               page.locator(".rs-result .rs-panel").count() == 0
               and "cleared" in after_sig.lower(),
               after_sig[:80].replace("\n", " | "))
        page.fill("input[data-fieldname='company']", "AI003 MG AR")
        page.keyboard.press("Escape")
        page.locator(".page-head .primary-action").click()
        wait_result_or_fail_with_diag(page, "evaluate_after_signal_invalidation")
        sig_res = page.locator(".rs-result").inner_text()
        record("evaluate_after_signal_invalidation",
               "AR Overdue Spike" in sig_res, sig_res[:90].replace("\n", " | "))
        page.unroute("**/api/method/lotus_fin.api.ai_insights.get_risk_signal")

        # --- stale delayed TRANSPORT ERROR discarded after input change ---
        page.fill("input[data-fieldname='company']", "AI003 MG AP")
        page.keyboard.press("Escape")
        set_date(page, "2026-09-26")
        page.locator("select[data-fieldname='signal_id']").select_option("AP_DUE_CLUSTER")
        held_d = {}
        hold_first_get_risk_signal(page, held_d, abort_on_release=True)
        page.locator(".page-head .primary-action").click()
        page.wait_for_selector(".rs-state:has-text('Evaluating')", timeout=15000)
        set_date(page, "2026-09-27")
        page.wait_for_timeout(300)
        release_held(held_d)  # real transport error for the dead request
        page.wait_for_timeout(900)
        after_err = page.locator(".rs-result").inner_text()
        record("stale_transport_error_discarded_after_change",
               page.locator(".rs-result .rs-panel").count() == 0
               and "cleared" in after_err.lower() and "Request failed" not in after_err,
               after_err[:80].replace("\n", " | "))
        page.locator(".page-head .primary-action").click()
        wait_result_or_fail_with_diag(page, "evaluate_after_transport_error_invalidation")
        page.unroute("**/api/method/lotus_fin.api.ai_insights.get_risk_signal")

        # --- keyboard flow: Enter on primary action performs a REAL evaluation ---
        set_date(page, "2026-09-26")
        page.locator(".page-head .primary-action").focus()
        page.keyboard.press("Enter")
        wait_result_or_fail_with_diag(page, "keyboard_primary_action")
        kb = page.locator(".rs-result").inner_text()
        record("keyboard_primary_action",
               "Evaluation completed" in kb and "33.33%" in kb, kb[:90].replace("\n", " | "))

        video_path = page.video.path()
        context.close()  # flush desktop video
        if os.path.exists(video_path):
            final = os.path.join(VIDEOS, "ai003_risk_signal_e2e.webm")
            if os.path.exists(final):
                os.remove(final)
            os.replace(video_path, final)
            print("VIDEO:", final)

        # --- mobile viewport ---
        mobile = browser.new_page(viewport={"width": 375, "height": 812})
        mobile.goto(BASE_URL + "/login?redirect-to=/app/risk-signal", wait_until="domcontentloaded")
        mobile.wait_for_selector("#login_email", timeout=30000)
        mobile.fill("#login_email", USER)
        mobile.fill("#login_password", PASSWORD)
        mobile.click(".btn-login")
        mobile.wait_for_selector(".rs-banner", timeout=90000)
        mobile.fill("input[data-fieldname='company']", "AI003 MG AR")
        mobile.keyboard.press("Escape")
        mobile.fill("input[data-fieldname='as_of_date']", "2026-09-26")
        mobile.keyboard.press("Escape")
        mobile.locator(".page-head .primary-action").click()
        mobile.wait_for_selector(".rs-result .rs-panel", timeout=60000)
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
