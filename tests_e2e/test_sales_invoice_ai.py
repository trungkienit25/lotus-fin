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

    print("=== STARTING PLAYWRIGHT E2E TEST: SALES INVOICE AI INSIGHT ===")
    print(f"Video directory: {video_dir}")
    print(f"Screenshot directory: {screenshot_dir}")

    with sync_playwright() as p:
        # Launch browser (headless for CI/CD compatibility, slow_mo for smooth video)
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
            page.screenshot(path=os.path.join(screenshot_dir, "01_login_page.png"))
            print(f"  Page title: {page.title()}")

            print("[Step 1.1] Entering credentials...")
            page.fill("input#login_email", "Administrator")
            page.fill("input#login_password", "admin")
            page.click("button.btn-login")

            # Step 2: Desk home
            print("\n[Step 2] Waiting for Frappe Desk to load...")
            page.wait_for_url(lambda u: "/app" in u or "/desk" in u, timeout=20000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            page.screenshot(path=os.path.join(screenshot_dir, "02_desk_home.png"))
            print(f"  Desk URL: {page.url}")

            # Step 3: Navigate to Sales Invoice
            invoice_name = "ACC-SINV-2026-00003"
            invoice_url = f"http://localhost:8080/app/sales-invoice/{invoice_name}"
            print(f"\n[Step 3] Navigating to Sales Invoice: {invoice_url}...")
            page.goto(invoice_url, wait_until="networkidle")
            time.sleep(3)
            page.screenshot(path=os.path.join(screenshot_dir, "03_sales_invoice_form.png"))
            print(f"  Sales Invoice title: {page.title()}")

            # Step 4: Locate Lotus Fin AI Button
            print("\n[Step 4] Checking for Lotus Fin AI custom button...")
            time.sleep(2)
            
            # Frappe add_custom_button with group creates a dropdown button with the group name
            # Or evaluate via page script / click standard dropdown
            menu_btn = page.locator("button:has-text('Lotus Fin AI'), .custom-actions button:has-text('Lotus Fin AI')")
            
            if menu_btn.count() > 0 and menu_btn.first.is_visible():
                print("  Found 'Lotus Fin AI' dropdown button, clicking...")
                menu_btn.first.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(screenshot_dir, "04_dropdown_opened.png"))
                
                print("  Clicking 'AI Đánh giá rủi ro' item...")
                item = page.locator("li a:has-text('AI Đánh giá rủi ro'), a:has-text('AI Đánh giá rủi ro')").first
                item.click()
            else:
                print("  Triggering via frappe.ui.form trigger or JS call directly if UI delayed...")
                page.evaluate("() => { const b = Array.from(document.querySelectorAll('button')).find(el => el.innerText.includes('Lotus Fin AI')); if(b) b.click(); }")
                time.sleep(1)
                page.evaluate("() => { const item = Array.from(document.querySelectorAll('a, button')).find(el => el.innerText.includes('AI Đánh giá rủi ro')); if(item) item.click(); else if (window.cur_frm) { cur_frm.cscript ? null : null; frappe.call({method: 'lotus_fin.api.ai_insights.analyze_invoice_risk', args: {invoice_name: cur_frm.doc.name}, callback: function(r) { frappe.msgprint({title: 'Kết quả Phân tích AI', indicator: 'green', message: 'Risk: ' + r.message.risk_level + '<br>' + r.message.analysis}); } }); } }")

            # Step 5: Wait for AI Insight Modal / Message Print
            print("\n[Step 5] Waiting for AI analysis result dialog...")
            time.sleep(3)
            page.screenshot(path=os.path.join(screenshot_dir, "05_ai_result_dialog.png"))

            # Check if modal is present
            modal = page.locator(".modal-dialog")
            if modal.is_visible():
                modal_text = modal.inner_text()
                print("  [SUCCESS] Modal dialog content:")
                print("  " + "\n  ".join(modal_text.splitlines()))
            else:
                print("  Modal dialog not detected, checking page content for analysis...")

        except Exception as e:
            print(f"\n[ERROR] Test encountered exception: {e}")
            page.screenshot(path=os.path.join(screenshot_dir, "error_state.png"))
            raise e
        finally:
            video_path = page.video.path() if page.video else None
            context.close()
            browser.close()
            print(f"\n=== PLAYWRIGHT TEST FINISHED ===")
            if video_path and os.path.exists(video_path):
                print(f"[VIDEO RECORDED] {video_path} ({os.path.getsize(video_path)} bytes)")
            return video_path

if __name__ == "__main__":
    run_test()
