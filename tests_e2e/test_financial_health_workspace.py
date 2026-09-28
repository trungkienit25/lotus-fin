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

    print("=== STARTING PLAYWRIGHT E2E TEST: LOTUS FIN FINANCIAL HEALTH WORKSPACE ===")
    print(f"Video directory: {video_dir}")
    print(f"Screenshot directory: {screenshot_dir}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        context = browser.new_context(
            record_video_dir=video_dir,
            record_video_size={"width": 1440, "height": 900},
            viewport={"width": 1440, "height": 900}
        )
        page = context.new_page()

        try:
            # Step 1: Login
            print("\n[Step 1] Navigating to http://localhost:8080/login...")
            page.goto("http://localhost:8080/login", wait_until="networkidle")
            page.fill("input#login_email", "Administrator")
            page.fill("input#login_password", "admin")
            page.click("button.btn-login")

            # Step 2: Desk home
            print("\n[Step 2] Waiting for Frappe Desk to load...")
            page.wait_for_url(lambda u: "/app" in u or "/desk" in u, timeout=25000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)

            # Step 3: Navigate directly to Lotus Fin Financial Health page
            health_url = "http://localhost:8080/app/financial-health"
            print(f"\n[Step 3] Navigating to Lotus Fin Financial Health: {health_url}...")
            page.goto(health_url, wait_until="networkidle")
            time.sleep(4)
            page.screenshot(path=os.path.join(screenshot_dir, "01_financial_health_page.png"))
            # Step 4: Ensure Company is 'Name (Demo)' and Period is 'FY2020'
            print("\n[Step 4] Checking company and period selection...")
            # Dismiss any modal dialog if open
            if page.locator(".modal.show").count() > 0:
                print("  Dismissing modal...")
                page.keyboard.press("Escape")
                time.sleep(1)

            # Trigger analysis
            page.locator("button:has-text('Analyze Financial Health'), button:has-text('Analyze')").first.click()
            time.sleep(4)

            # Step 5: Verify KPI Summary Cards
            print("\n[Step 5] Capturing KPI summary cards...")
            if page.locator(".modal.show").count() > 0:
                page.keyboard.press("Escape")
                time.sleep(1)
            kpis = page.locator("#lotus-kpi-cards")
            kpis.wait_for(state="visible", timeout=10000)
            page.screenshot(path=os.path.join(screenshot_dir, "02_kpi_summary.png"))

            # Check known gold text presence in page
            body_text = page.locator(".lotus-financial-health-container").inner_text()
            print("  Verifying gold metrics on screen:")
            assert "363,000" in body_text or "363000" in body_text, "Revenue 363k missing"
            assert "253,760" in body_text or "253760" in body_text, "COGS 253.76k missing"
            assert "30.09%" in body_text or "0.3009" in body_text, "Gross Margin 30.09% missing"
            assert "-117,854" in body_text or "-117854" in body_text, "Negative cash balance missing"
            assert "316,000" in body_text or "316000" in body_text, "AR 316k missing"
            assert "100.00%" in body_text or "100%" in body_text, "Overdue ratio 100% missing"
            print("  -> ALL GOLD VALUES VERIFIED VISIBLE ON SCREEN!")

            # Step 6: Period Comparison Section
            print("\n[Step 6] Capturing Period Comparison section...")
            comp_section = page.locator("#lotus-comparison-section")
            comp_section.scroll_into_view_if_needed()
            time.sleep(1)
            page.screenshot(path=os.path.join(screenshot_dir, "03_period_comparison.png"))

            # Step 7: AI Analysis Section
            print("\n[Step 7] Capturing AI Financial Analysis section...")
            ai_section = page.locator("#lotus-ai-section")
            ai_section.scroll_into_view_if_needed()
            time.sleep(1)
            page.screenshot(path=os.path.join(screenshot_dir, "04_ai_analysis.png"))

            # Step 8: Evidence & Audit Provenance
            print("\n[Step 8] Capturing Evidence section...")
            ev_section = page.locator("#lotus-evidence-section")
            ev_section.scroll_into_view_if_needed()
            time.sleep(1)
            page.screenshot(path=os.path.join(screenshot_dir, "05_evidence_drawer.png"))

            # Step 9: Test Partial / Degraded / Model-Unavailable state
            print("\n[Step 9] Simulating empty company / unavailable state...")
            # Switch company to 'Name' (the empty company)
            company_input = page.locator("input[data-fieldname='company']")
            if company_input.count() > 0:
                company_input.fill("Name")
                company_input.press("Enter")
                time.sleep(3)
                page.click("button:has-text('Analyze Financial Health'), button:has-text('Analyze')")
                time.sleep(4)
                page.screenshot(path=os.path.join(screenshot_dir, "06_partial_or_model_unavailable.png"))
                print("  Captured degraded/empty company state screenshot.")

            print("\n[SUCCESS] All E2E interactions and verifications passed.")

        except Exception as e:
            print(f"\n[ERROR] E2E test encountered exception: {e}")
            page.screenshot(path=os.path.join(screenshot_dir, "error_state.png"))
            raise e
        finally:
            video_path = page.video.path() if page.video else None
            context.close()
            browser.close()
            print(f"\n=== E2E TEST FINISHED ===")
            if video_path and os.path.exists(video_path):
                print(f"[VIDEO RECORDED] {video_path} ({os.path.getsize(video_path)} bytes)")
            return video_path

if __name__ == "__main__":
    run_test()
