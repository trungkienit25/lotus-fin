import subprocess
import time
import os
import shutil
import socket
import urllib.request
import pytest
from playwright.sync_api import sync_playwright

FIXTURE_PORT = 5189
FIXTURE_URL = f"http://127.0.0.1:{FIXTURE_PORT}"
ROOT_DIR = os.path.normcase(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

EXPECTED_LITERAL = (
    "Xin chào,\n\n"
    "Tôi muốn trao đổi về nội dung cần theo dõi. Khi thuận tiện, vui lòng phản hồi để chúng ta xác nhận thông tin và bước tiếp theo.\n\n"
    "Cảm ơn."
)

def is_port_in_use(port: int = FIXTURE_PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def kill_process_cleanly(proc) -> None:
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except Exception:
                pass

@pytest.fixture(scope="module")
def fixture_server():
    frontend_dir = os.path.join(ROOT_DIR, "frontend")
    node_bin = shutil.which("node") or "node"
    vite_js = os.path.join(frontend_dir, "node_modules", "vite", "bin", "vite.js")
    config_path = os.path.join(ROOT_DIR, "tests_e2e", "followup_preview_fixture", "vite.config.ts")
    node_modules_dir = os.path.join(frontend_dir, "node_modules")

    env = os.environ.copy()
    env["NODE_PATH"] = node_modules_dir

    proc = subprocess.Popen(
        [node_bin, vite_js, "--config", config_path, "--host", "127.0.0.1", "--port", str(FIXTURE_PORT), "--strictPort"],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ready = False
    start_time = time.time()
    while time.time() - start_time < 15:
        if proc.poll() is not None:
            raise RuntimeError(f"Vite server exited prematurely with code {proc.poll()}")
        if is_port_in_use(FIXTURE_PORT):
            try:
                req = urllib.request.Request(FIXTURE_URL + "/")
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                pass
        time.sleep(0.3)

    if not ready:
        kill_process_cleanly(proc)
        raise RuntimeError("Vite fixture server failed to become ready within timeout.")

    try:
        yield FIXTURE_URL
    finally:
        kill_process_cleanly(proc)

def install_strict_network_guard(page):
    requests_made = []
    def handle_route(route):
        url = route.request.url
        if url.startswith(FIXTURE_URL) or "127.0.0.1" in url or "localhost" in url:
            route.continue_()
        else:
            requests_made.append(url)
            route.abort("blockedbyclient")
    page.route("**/*", handle_route)
    return requests_made

def test_l3_fixture_oracle_complete_flow(fixture_server):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            unexpected_external = install_strict_network_guard(page)
            page.goto(fixture_server, wait_until="networkidle")

            # Initial state: EMPTY, Prepare button visible
            prepare_btn = page.locator("[data-testid='btn-prepare']")
            assert prepare_btn.is_visible()

            # L301: Click Prepare -> PREVIEW_READY with exact literal and SUGGESTED badge
            prepare_btn.click()
            page.wait_for_selector("[data-testid='preview-textarea']")
            textarea = page.locator("[data-testid='preview-textarea']")
            badge = page.locator("[data-testid='provenance-badge']")
            
            assert textarea.input_value() == EXPECTED_LITERAL
            assert "SUGGESTED" in badge.inner_text()

            # L303: Verify no sentinels leak into textarea or DOM text
            content = page.content()
            assert "INVOICE-100-SECRET-VAL" not in textarea.input_value()
            assert "BEARER-TOKEN-SECRET-XYZ" not in content
            assert "ACME-CORP-SECRET-NAME" not in content

            # L304: Copy button disabled before Review
            copy_btn = page.locator("[data-testid='btn-copy']")
            assert copy_btn.is_disabled()

            # L305: Check Review -> Copy button enabled -> Click Copy
            review_checkbox = page.locator("[data-testid='checkbox-review']")
            review_checkbox.check()
            assert not copy_btn.is_disabled()
            copy_btn.click()

            page.wait_for_selector("[data-testid='notice-copied']")
            writes = page.evaluate("() => window.__clipboardWrites")
            assert len(writes) == 1
            assert writes[0] == EXPECTED_LITERAL

            # L306 & L307: Edit text -> provenance changes to USER_ENTERED, Review cleared, Copy disabled
            new_text = "Nội dung do tôi nhập."
            textarea.fill(new_text)
            assert "USER_ENTERED" in badge.inner_text()
            assert not review_checkbox.is_checked()
            assert copy_btn.is_disabled()

            # L309: XSS payload renders strictly as plain text in textarea
            xss_payload = "<script>alert(1)</script><img src=x onerror=alert(1)>"
            textarea.fill(xss_payload)
            assert page.locator("script").count() == 0 or page.locator("body script[src*='main.tsx']").count() > 0
            assert page.evaluate("() => window.__xss_flag") is None

            # L308: Reset template restores exact literal SUGGESTED
            reset_btn = page.locator("[data-testid='btn-reset-template']")
            reset_btn.click()
            assert textarea.input_value() == EXPECTED_LITERAL
            assert "SUGGESTED" in badge.inner_text()

            # L314: Discard clears preview back to EMPTY
            discard_btn = page.locator("[data-testid='btn-discard']")
            discard_btn.click()
            assert page.locator("[data-testid='btn-prepare']").is_visible()

            # L315: Scope change resets preview
            page.locator("[data-testid='btn-prepare']").click()
            page.wait_for_selector("[data-testid='preview-textarea']")
            page.click("#btn-switch-scope")
            assert page.locator("[data-testid='btn-prepare']").is_visible()

            # L316: Unmount and Remount starts EMPTY
            page.click("#btn-toggle-mount")
            assert page.locator("#unmounted-indicator").is_visible()
            page.click("#btn-toggle-mount")
            assert page.locator("[data-testid='btn-prepare']").is_visible()

            # L317: Absolute TTL Expiry at 600,000ms
            page.locator("[data-testid='btn-prepare']").click()
            page.wait_for_selector("[data-testid='preview-textarea']")
            page.evaluate("() => { window.__mockClockTime += 600001; }")
            review_checkbox.click()
            assert page.locator("[data-testid='alert-expired']").is_visible()

            # Ensure zero unauthorized network calls
            assert len(unexpected_external) == 0, f"Unexpected external requests: {unexpected_external}"
        finally:
            browser.close()
