import subprocess
import time
import os
import shutil
import urllib.request
import pytest
from playwright.sync_api import sync_playwright

from tests_e2e.copilot_test_harness import (
    FIXTURE_URL,
    PORT,
    COPILOT_PATH,
    is_port_in_use,
    get_port_listeners,
    kill_process_cleanly,
    LifecycleGuard,
    install_network_guard,
)

@pytest.fixture(scope="module")
def vite_fixture_server():
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    frontend_dir = os.path.join(cwd, "frontend")
    node_bin = shutil.which("node") or "node"
    vite_js = os.path.join(frontend_dir, "node_modules", "vite", "bin", "vite.js")
    config_path = os.path.join(cwd, "tests_e2e", "copilot_fixture", "vite.config.ts")
    node_modules_dir = os.path.join(frontend_dir, "node_modules")

    # Invariant B: Preflight: refuse unexpected pre-existing listener (Q5)
    if is_port_in_use(PORT):
        raise RuntimeError(f"Port {PORT} already in use; refusing unexpected foreign listener.")

    env = os.environ.copy()
    env["NODE_PATH"] = node_modules_dir

    # Invariant B1: Direct Node spawn with tracked PID
    proc = subprocess.Popen(
        [node_bin, vite_js, "--config", config_path, "--host", "127.0.0.1", "--port", str(PORT), "--strictPort"],
        cwd=cwd,
        env=env,
    )

    try:
        # Invariant B2: Readiness verification (Process alive, Port listening, Exact PID, HTTP body)
        start_time = time.time()
        ready = False
        while time.time() - start_time < 15:
            if proc.poll() is not None:
                raise RuntimeError(f"Vite server PID {proc.pid} exited prematurely with code {proc.poll()}")

            listeners = get_port_listeners(PORT)
            if listeners:
                if listeners != [proc.pid]:
                    raise RuntimeError(
                        f"Port {PORT} listener PID {listeners} does not match owned Vite process {proc.pid}"
                    )
                try:
                    req = urllib.request.Request(FIXTURE_URL + "/")
                    with urllib.request.urlopen(req, timeout=1) as resp:
                        content = resp.read().decode("utf-8", errors="ignore")
                        if resp.status == 200 and "Lotus Fin Copilot Test Fixture" in content:
                            ready = True
                            break
                except Exception:
                    pass
            time.sleep(0.2)

        if not ready:
            raise RuntimeError(f"Vite server PID {proc.pid} failed full readiness verification within 15s")

        yield proc
    finally:
        # Invariant B3: Cleanup owned process and verify port release (Q4, Q6)
        kill_process_cleanly(proc)
        time.sleep(0.5)
        if is_port_in_use(PORT):
            raise RuntimeError(f"Port {PORT} remained occupied after terminating owned Vite process {proc.pid}")

def test_unqualified_context_makes_zero_post_calls(vite_fixture_server):
    """Asserts that both callers make ZERO Copilot POST calls under current unqualified context."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(service_workers="block")
            copilot_posts = []

            def mock_api(route, path):
                copilot_posts.append(route.request.url)
                route.abort()
                return True

            unexpected = install_network_guard(page, mock_api)
            page.goto(FIXTURE_URL, wait_until="networkidle")

            page.click("#btn-mode-panel")
            page.wait_for_selector("#fixture-panel-container")
            textarea = page.locator("textarea")
            textarea.fill("Financial health snapshot")
            page.locator("button[title='Send message']").click()
            page.wait_for_selector("text=Chưa đủ ngữ cảnh hoặc nguồn đã xác minh để thực hiện yêu cầu này.")

            page.click("#btn-mode-drawer")
            page.wait_for_selector("#fixture-drawer-container")
            page.locator("button[title='Open Lotus Fin AI Copilot']").click()
            page.wait_for_selector("textarea")
            textarea = page.locator("textarea")
            textarea.fill("30-day cash forecast")
            page.locator("button[title='Send message']").click()
            page.wait_for_selector("text=Chưa đủ ngữ cảnh hoặc nguồn đã xác minh để thực hiện yêu cầu này.")

            assert len(copilot_posts) == 0, f"Expected 0 Copilot POST calls, but got {len(copilot_posts)}"
        finally:
            browser.close()
            # Invariant C: ledger check after settled browser teardown
            assert len(unexpected) == 0, f"Unexpected network traffic detected: {unexpected}"

def test_copilot_failclosed_normalization_scenarios(vite_fixture_server):
    """Table-driven test for fail-closed normalization (F01, F02, F05)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(service_workers="block")
            mock_response = {"data": None, "status": 200, "headers": {}}

            def mock_api(route, path):
                body = mock_response["data"]
                body_str = body if isinstance(body, str) else (__import__("json").dumps(body) if body is not None else "")
                route.fulfill(
                    status=mock_response["status"],
                    headers=mock_response.get("headers", {}),
                    content_type="application/json",
                    body=body_str,
                )
                return True

            unexpected = install_network_guard(page, mock_api)
            page.goto(FIXTURE_URL, wait_until="networkidle")

            # Setup request listener to count exact synthetic copilot requests
            req_counter = {"count": 0}
            def on_request(req):
                if COPILOT_PATH in req.url:
                    req_counter["count"] += 1
            page.on("request", on_request)

            page.click("#btn-mode-hook")
            page.wait_for_selector("#fixture-hook-container")
            page.click("#btn-qualify-context")

            cases = [
                ("EMPTY", 200, {}, "", "NOT_AVAILABLE", "FALSE"),
                ("FORBIDDEN_403", 403, {}, {"message": "Forbidden"}, "FORBIDDEN", "FALSE"),
                ("SOURCE_ERROR_500", 500, {}, {"error": "Internal Error"}, "SOURCE_ERROR", "FALSE"),
                ("NESTED_TOOL_ERROR", 200, {}, {"message": {"status": "success", "reply": "SENSITIVE_MARKER", "tool_output": {"status": "SOURCE_ERROR", "error": "SENSITIVE_MARKER"}}}, "SOURCE_ERROR", "FALSE"),
                ("NESTED_TOOL_FORBIDDEN", 200, {}, {"message": {"status": "success", "reply": "SENSITIVE_MARKER", "tool_output": {"status": "FORBIDDEN"}}}, "FORBIDDEN", "FALSE"),
                ("CONTRADICTORY", 200, {}, {"status": "SOURCE_ERROR", "message": {"status": "TIMEOUT", "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("ROOT_DENIAL", 200, {}, {"status": "FORBIDDEN", "message": {"status": "OK", "reply": "SENSITIVE_MARKER"}}, "FORBIDDEN", "FALSE"),
                ("UNKNOWN_STATUS", 200, {}, {"message": {"status": "UNRECOGNIZED", "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("NOT_AVAILABLE_STATUS", 200, {}, {"message": {"status": "NOT_AVAILABLE", "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("PARTIAL_FINANCIAL", 200, {}, {"message": {"status": "PARTIAL", "reply": "SENSITIVE_MARKER", "tool_output": {"amount": 100}}}, "PARTIAL", "FALSE"),
                ("RESULT_FINANCIAL", 200, {}, {"message": {"reply": "SENSITIVE_MARKER", "result": {"amount": 100}}}, "NOT_AVAILABLE", "FALSE"),
                ("ACTION_FINANCIAL", 200, {}, {"message": {"reply": "SENSITIVE_MARKER", "suggestedActions": [{"type": "send", "args": {"secret": "SENSITIVE_MARKER"}}]}}, "NOT_AVAILABLE", "FALSE"),
                ("DEMO_FINANCIAL", 200, {}, {"message": {"reply": "SENSITIVE_MARKER", "source": "DEMO_ONLY", "result": {"amount": 100}}}, "NOT_AVAILABLE", "FALSE"),
                ("BENIGN", 200, {}, {"message": {"reply": "SAFE_REPLY"}}, "OK", "FALSE"),
                ("R1_DENIAL_UNKNOWN", 200, {}, {"status": "FORBIDDEN", "message": {"status": "UNRECOGNIZED", "reply": "SENSITIVE_MARKER"}}, "FORBIDDEN", "FALSE"),
                ("R1_OBJECT_STATUS", 200, {}, {"message": {"status": {"code": "FORBIDDEN"}, "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("R1_BOOLEAN_STATUS", 200, {}, {"message": {"status": True, "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("R1_ARRAY_STATUS", 200, {}, {"message": {"status": ["FORBIDDEN"], "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("R1_SOURCE_UNAVAILABLE_CONFLICT", 200, {}, {"status": "SOURCE_ERROR", "message": {"status": "NOT_AVAILABLE", "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("R1_TIMEOUT_UNAVAILABLE_CONFLICT", 200, {}, {"status": "TIMEOUT", "message": {"status": "NOT_AVAILABLE", "reply": "SENSITIVE_MARKER"}}, "NOT_AVAILABLE", "FALSE"),
                ("R1_HTTP_500_DENIAL", 500, {}, {"message": {"status": "FORBIDDEN", "reply": "SENSITIVE_MARKER"}}, "FORBIDDEN", "FALSE"),
                ("R1_HTTP_504_DENIAL", 504, {}, {"message": {"status": "FORBIDDEN", "reply": "SENSITIVE_MARKER"}}, "FORBIDDEN", "FALSE"),
                ("R2_BODY_DENIAL_TIMEOUT", 500, {}, {"message": {"status": "FORBIDDEN", "reply": "SENSITIVE_MARKER"}}, "FORBIDDEN", "FALSE"),
                ("SAFE_REPLY_CID", 200, {"x-correlation-id": "safe-cid-12345"}, {"message": {"reply": "Xin chào"}}, "OK", "FALSE"),
                ("MALFORMED_CID", 200, {"x-correlation-id": "invalid cid spaces"}, {"message": {"reply": "Xin chào"}}, "OK", "FALSE"),
                ("CONFLICTING_CID", 200, {"x-correlation-id": "cid-1, cid-2"}, {"message": {"reply": "Xin chào"}}, "OK", "FALSE"),
            ]

            for cid, status, headers, data, exp_status, exp_widgets in cases:
                mock_response["status"] = status
                mock_response["headers"] = headers
                mock_response["data"] = data

                before_count = req_counter["count"]

                # Invariant D: synchronously wait for this exact case's response and settled IDLE state
                with page.expect_response(lambda res: COPILOT_PATH in res.url):
                    page.click("#btn-send-hook")

                page.wait_for_selector("#hook-loading:has-text('IDLE')")

                after_count = req_counter["count"]
                assert after_count == before_count + 1, (
                    f"Case {cid}: expected request increment from {before_count}, but observed {after_count}"
                )

                res_status = page.locator("#hook-result-status").inner_text()
                res_text = page.locator("#hook-result-text").inner_text()
                res_widgets = page.locator("#hook-result-widgets").inner_text()

                assert res_status == exp_status, f"Case {cid}: expected status {exp_status}, got {res_status}"
                assert res_widgets == exp_widgets, f"Case {cid}: expected widgets {exp_widgets}, got {res_widgets}"
                if cid not in ("BENIGN", "SAFE_REPLY_CID", "MALFORMED_CID", "CONFLICTING_CID"):
                    assert "SENSITIVE_MARKER" not in res_text, f"Case {cid} leaked sensitive marker: {res_text}"
                if cid == "BENIGN":
                    assert res_text == "SAFE_REPLY"
                if cid == "SAFE_REPLY_CID":
                    assert page.locator("#hook-result-cid").inner_text() == "safe-cid-12345"
                elif cid in ("MALFORMED_CID", "CONFLICTING_CID"):
                    assert page.locator("#hook-result-cid").inner_text() == "NONE"
        finally:
            browser.close()
            assert len(unexpected) == 0, f"Unexpected network traffic detected: {unexpected}"

def test_scope_presentation_clear_and_unqualified_claims(vite_fixture_server):
    """Test message clearing, disabled reports & disabled quick action shortcuts (F03, F06)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(service_workers="block")
            unexpected = install_network_guard(page)
            page.goto(FIXTURE_URL, wait_until="networkidle")
            page.click("#btn-mode-panel")
            page.wait_for_selector("#fixture-panel-container")

            # Verify no General Ledger claim
            container_text = page.locator("#fixture-panel-container").inner_text()
            assert "connected to General Ledger" not in container_text
            assert "Analyzing General Ledger records" not in container_text

            # Verify Reports button is disabled
            reports_btn = page.locator("button[title='Reports unavailable under unqualified observation context']")
            assert reports_btn.count() > 0
            assert reports_btn.is_disabled()

            # Verify quick actions shortcuts are disabled or unavailable (R1_QUICK_ACTIONS_GATE)
            for name in ["Financial Health", "Cash Forecast 30D", "Risk Signals", "What-If Studio"]:
                btn = page.get_by_role("button", name=name, exact=True)
                assert btn.count() > 0
                assert btn.is_disabled() or "unavailable" in (btn.inner_text() + " " + str(btn.get_attribute("title"))).lower()

            # Send a message to panel
            textarea = page.locator("textarea")
            textarea.fill("SCOPE_TEST_MARKER")
            page.locator("button[title='Send message']").click()
            page.wait_for_selector("text=SCOPE_TEST_MARKER")

            # Change company: assert old messages cleared
            page.click("#btn-panel-company-b")
            page.wait_for_timeout(100)
            assert page.locator("text=SCOPE_TEST_MARKER").count() == 0

            # Send another message, change contextKey: assert cleared
            textarea = page.locator("textarea")
            textarea.fill("CONTEXT_TEST_MARKER")
            page.locator("button[title='Send message']").click()
            page.wait_for_selector("text=CONTEXT_TEST_MARKER")

            page.click("#btn-panel-ctx-b")
            page.wait_for_timeout(100)
            assert page.locator("text=CONTEXT_TEST_MARKER").count() == 0
        finally:
            browser.close()
            assert len(unexpected) == 0, f"Unexpected network traffic detected: {unexpected}"

def test_xss_injection_rendered_safely_as_text(vite_fixture_server):
    """Verify that XSS payloads are rendered strictly as text nodes without executing."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(service_workers="block")
            unexpected = install_network_guard(page)
            page.goto(FIXTURE_URL, wait_until="networkidle")
            page.click("#btn-mode-body")
            page.wait_for_selector("#fixture-body-container")

            payload = "<script>window.__xss_executed = true;</script><img src='invalid' onerror='window.__xss_executed=true' /><a href='javascript:alert(1)'>click me</a>"
            page.locator("#body-input").fill(payload)

            rendered = page.locator("#body-rendered")
            assert rendered.locator("script").count() == 0
            assert rendered.locator("img").count() == 0
            assert page.evaluate("() => window.__xss_executed") is None
        finally:
            browser.close()
            assert len(unexpected) == 0, f"Unexpected network traffic detected: {unexpected}"
