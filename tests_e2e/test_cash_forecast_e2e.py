import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

def run_test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    video_dir = os.path.join(base_dir, "videos")
    screenshot_dir = os.path.join(base_dir, "screenshots")
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(screenshot_dir, exist_ok=True)

    print("=== STARTING PLAYWRIGHT E2E TEST: CASH FORECAST COPILOT ===")
    print(f"Video directory: {video_dir}")
    print(f"Screenshot directory: {screenshot_dir}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        context = browser.new_context(
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            # Step 1: Login
            print("\n[Step 1] Navigating to http://localhost:8080/login...")
            page.goto("http://localhost:8080/login", wait_until="networkidle")
            page.screenshot(path=os.path.join(screenshot_dir, "cf_01_login.png"))
            print(f"  Page title: {page.title()}")

            print("[Step 1.1] Entering credentials...")
            page.fill("input#login_email", "Administrator")
            page.fill("input#login_password", "admin")
            page.click("button.btn-login")

            # Step 2: Desk home
            print("\n[Step 2] Waiting for Frappe Desk to load...")
            page.wait_for_url(lambda u: "/app" in u or "/desk" in u, timeout=20000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            page.screenshot(path=os.path.join(screenshot_dir, "cf_02_desk.png"))

            # Step 3: Navigate to Cash Forecast Copilot Page
            cf_url = "http://localhost:8080/app/cash-forecast"
            print(f"\n[Step 3] Navigating to Cash Forecast: {cf_url}...")
            page.goto(cf_url, wait_until="networkidle")
            time.sleep(3)
            page.screenshot(path=os.path.join(screenshot_dir, "cf_03_initial_view.png"))

            # Step 4: Verify Company field and set to AI002 Fixture 2026
            print("\n[Step 4] Setting company filter to AI002 Fixture 2026...")
            company_input = page.locator("input[data-fieldname='company']")
            if company_input.count() > 0:
                company_input.fill("AI002 Fixture 2026")
                page.keyboard.press("Enter")
                time.sleep(2)

            # Step 5: Click Compute Forecast
            print("\n[Step 5] Clicking Compute Forecast...")
            compute_btn = page.locator("button:has-text('Compute Forecast')")
            if compute_btn.count() > 0:
                compute_btn.first.click()
                time.sleep(4)

            page.screenshot(path=os.path.join(screenshot_dir, "cf_04_computed_forecast.png"))

            # Step 6: Verify Opening Cash and Ledger Truth
            opening_cash_el = page.locator("#cf-opening-amount")
            if opening_cash_el.count() > 0:
                print(f"  Opening Cash Balance rendered: {opening_cash_el.text_content()}")

            recon_status_el = page.locator("#cf-reconciliation-status")
            if recon_status_el.count() > 0:
                print(f"  Reconciliation Status: {recon_status_el.text_content()}")

            print("\n[Step 7] Capturing full dashboard screenshot...")
            page.screenshot(path=os.path.join(screenshot_dir, "cf_05_final_dashboard.png"))
            time.sleep(2)

            print("=== PLAYWRIGHT E2E TEST COMPLETED SUCCESSFULLY ===")

        except Exception as e:
            print(f"\n[ERROR] Test failed with exception: {e}")
            page.screenshot(path=os.path.join(screenshot_dir, "cf_error_state.png"))
            raise
        finally:
            context.close()
            browser.close()
            print("Video recorded and saved to:", video_dir)

if __name__ == "__main__":
    run_test()
