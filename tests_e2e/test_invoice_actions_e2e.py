import json
import time
import pytest
from playwright.sync_api import sync_playwright

from tests_e2e.copilot_test_harness import (
    FIXTURE_URL,
    INVOICE_PATHS,
    LifecycleGuard,
    install_network_guard,
)

# Re-use the existing vite_fixture_server fixture from test_copilot_failclosed
from tests_e2e.test_copilot_failclosed import vite_fixture_server

# Valid UUID4 constants
DEMO_CID = "22222222-2222-4222-8222-222222222222"
DEFAULT_RID = "11111111-1111-4111-8111-111111111111"

def build_envelope(capability: str, status: str = "OK", reason: str = "RESULTS_FOUND", data=None, request_id: str = DEFAULT_RID, context_version: str = "ctx_demo_v1"):
    is_failure = status in ("NOT_AVAILABLE", "FORBIDDEN", "SOURCE_ERROR", "TIMEOUT")
    source = None if is_failure else {
        "mode": "DEMO_ISOLATED",
        "verification": "AUTHORIZED_READ",
        "product_ref": "lotus",
        "site_ref": "site1",
        "connection_ref": "conn1",
        "connection_version": "1.0.0",
        "projection_version": "invoice.min.v1",
        "observed_at": "2026-10-12T00:00:00+00:00",
        "timezone": "Asia/Ho_Chi_Minh",
        "coverage": "PAGE_COMPLETE" if status == "OK" else "INCOMPLETE",
        "consistency": "LIVE_KEYSET",
    }
    return {
        "contract_version": "p1.invoice.v1",
        "status": status,
        "reason_code": reason,
        "correlation_id": DEMO_CID,
        "request_id": request_id,
        "capability": capability,
        "source": source,
        "context_version": None if is_failure else context_version,
        "data": None if is_failure else data,
        "user_message": "server text that must never be rendered",
    }

def test_p2b_invoice_search_select_open_flow(vite_fixture_server):
    """
    UI Flow:
    1. Mount invoice actions panel.
    2. Context qualified with company label from server.
    3. User queries SINV-2026.
    4. Two results displayed with identity fields (no financial figures).
    5. User selects second invoice.
    6. Read-only viewer opens with 5 approved fields.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            with LifecycleGuard(browser) as guard:
                page = guard.page

                def mock_api(route, path):
                    req_rid = (route.request.post_data_json or {}).get("request_id") or DEFAULT_RID

                    if "invoice_context" in path:
                        ctx_body = {
                            "message": build_envelope(
                                "invoice.context",
                                status="OK",
                                reason="CONTEXT_READY",
                                request_id=req_rid,
                                data={
                                    "context_ref": "ref.v1.ctx.demo",
                                    "context_version": "ctx_demo_v1",
                                    "company_label": "Lotus Technologies JSC",
                                    "allowed_filters": ["invoice_name_prefix", "posting_date", "docstatus"],
                                    "expires_at": "2099-01-01T00:00:00+00:00",
                                    "default_posting_from": "2026-07-15",
                                    "default_posting_to": "2026-10-12",
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(ctx_body))
                        return True

                    if "invoice_search" in path:
                        req_data = route.request.post_data_json
                        filters = req_data.get("filters", {})
                        assert filters.get("invoice_name_prefix") == "SINV-2026"

                        search_body = {
                            "message": build_envelope(
                                "invoice.search",
                                status="OK",
                                reason="RESULTS_FOUND",
                                request_id=req_rid,
                                data={
                                    "items": [
                                        {
                                            "invoice_type": "SALES",
                                            "invoice_id": "SINV-2026-0001",
                                            "posting_date": "2026-10-01",
                                            "docstatus": 1,
                                            "record_version": "rec_001",
                                            "selection_ref": "ref.v2.sel.001",
                                        },
                                        {
                                            "invoice_type": "SALES",
                                            "invoice_id": "SINV-2026-0002",
                                            "posting_date": "2026-10-02",
                                            "docstatus": 1,
                                            "record_version": "rec_002",
                                            "selection_ref": "ref.v2.sel.002",
                                        },
                                    ],
                                    "returned_count": 2,
                                    "total_count": None,
                                    "page_complete": True,
                                    "has_more": False,
                                    "next_cursor": None,
                                    "selection_required": True,
                                    "limitations": None,
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(search_body))
                        return True

                    if "invoice_open" in path:
                        req_data = route.request.post_data_json
                        assert req_data.get("selection_ref") == "ref.v2.sel.002"

                        open_body = {
                            "message": build_envelope(
                                "invoice.open",
                                status="OK",
                                reason="DOCUMENT_READY",
                                request_id=req_rid,
                                data={
                                    "document": {
                                        "invoice_type": "SALES",
                                        "invoice_id": "SINV-2026-0002",
                                        "posting_date": "2026-10-02",
                                        "docstatus": 1,
                                        "record_version": "rec_002",
                                    },
                                    "company_label": "Lotus Technologies JSC",
                                    "navigation": {
                                        "kind": "LOTUS_READ_VIEW",
                                        "view": "sales-invoice-minimal-v1"
                                    }
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(open_body))
                        return True

                    return False

                guard.mock_handler = mock_api

                page.goto(FIXTURE_URL, wait_until="networkidle")
                page.click("#btn-mode-invoice")
                page.wait_for_selector("#fixture-invoice-container")

                # Verify context received and company label rendered
                company_label = page.wait_for_selector('[data-testid="company-label"]')
                assert company_label.inner_text() == "Lotus Technologies JSC"

                # Perform search
                page.fill('[data-testid="f-prefix"]', "SINV-2026")
                page.click('[data-testid="search-btn"]')

                # Verify search results
                page.wait_for_selector('[data-testid="results"]')
                rows = page.locator('[data-testid="result-row"]')
                assert rows.count() == 2

                # Security check: No financial amount columns rendered
                page_text = page.locator('[data-testid="results"]').inner_text()
                assert "VND" not in page_text
                assert "USD" not in page_text
                assert "Total" not in page_text
                assert "grand_total" not in page_text

                # Explicit selection: select second invoice
                page.locator('[data-invoice-id="SINV-2026-0002"] [data-testid="open-btn"]').click()

                # Verify read-only viewer opens
                page.wait_for_selector('[data-testid="read-view"]')
                assert page.locator('[data-testid="readonly-badge"]').inner_text() == "Read-only"

                # Verify approved fields only
                assert page.locator('[data-testid="f-invoice-id"]').inner_text() == "SINV-2026-0002"
                assert page.locator('[data-testid="f-type"]').inner_text() == "Sales"
                assert page.locator('[data-testid="f-date"]').inner_text() == "2026-10-02"
                assert page.locator('[data-testid="f-status"]').inner_text() == "Submitted"
                assert page.locator('[data-testid="f-version"]').inner_text() == "rec_002"

                # Verify trace footer
                assert page.locator('[data-testid="trace-cid"]').inner_text() == DEMO_CID

                # Verify no edit/save/submit buttons exist
                assert page.locator("button:has-text('Save')").count() == 0
                assert page.locator("button:has-text('Submit')").count() == 0
                assert page.locator("button:has-text('Edit')").count() == 0
        finally:
            browser.close()

def test_p2b_invoice_empty_and_partial_results(vite_fixture_server):
    """Verifies that empty results show message and PARTIAL results disable selection."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            with LifecycleGuard(browser) as guard:
                page = guard.page
                current_mode = {"mode": "empty"}

                def mock_api(route, path):
                    req_rid = (route.request.post_data_json or {}).get("request_id") or DEFAULT_RID

                    if "invoice_context" in path:
                        ctx_body = {
                            "message": build_envelope(
                                "invoice.context",
                                status="OK",
                                reason="CONTEXT_READY",
                                request_id=req_rid,
                                data={
                                    "context_ref": "ref.v1.ctx.demo",
                                    "context_version": "ctx_demo_v1",
                                    "company_label": "Lotus Technologies JSC",
                                    "allowed_filters": ["invoice_name_prefix", "posting_date", "docstatus"],
                                    "expires_at": "2099-01-01T00:00:00+00:00",
                                    "default_posting_from": "2026-07-15",
                                    "default_posting_to": "2026-10-12",
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(ctx_body))
                        return True

                    if "invoice_search" in path:
                        if current_mode["mode"] == "empty":
                            resp_body = {
                                "message": build_envelope(
                                    "invoice.search",
                                    status="OK",
                                    reason="EMPTY_RESULT",
                                    request_id=req_rid,
                                    data={
                                        "items": [],
                                        "returned_count": 0,
                                        "total_count": None,
                                        "page_complete": True,
                                        "has_more": False,
                                        "next_cursor": None,
                                        "selection_required": False,
                                        "limitations": None,
                                    }
                                )
                            }
                        else:  # partial
                            resp_body = {
                                "message": build_envelope(
                                    "invoice.search",
                                    status="PARTIAL",
                                    reason="COVERAGE_INCOMPLETE",
                                    request_id=req_rid,
                                    data={
                                        "items": [
                                            {
                                                "invoice_type": "SALES",
                                                "invoice_id": "SINV-PART-001",
                                                "posting_date": "2026-10-01",
                                                "docstatus": 0,
                                                "record_version": "rec_part",
                                                "selection_ref": None,
                                            }
                                        ],
                                        "returned_count": 1,
                                        "total_count": None,
                                        "page_complete": False,
                                        "has_more": None,
                                        "next_cursor": None,
                                        "selection_required": True,
                                        "limitations": ["COVERAGE_INCOMPLETE"],
                                    }
                                )
                            }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(resp_body))
                        return True

                    return False

                guard.mock_handler = mock_api

                page.goto(FIXTURE_URL, wait_until="networkidle")
                page.click("#btn-mode-invoice")
                page.wait_for_selector('[data-testid="company-label"]')

                # 1. Empty result test
                page.fill('[data-testid="f-prefix"]', "NONEXISTENT")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-testid="results-empty"]')
                assert "No invoices matched these criteria in the checked range." in page.locator('[data-testid="results-empty"]').inner_text()

                # 2. Partial result test
                current_mode["mode"] = "partial"
                page.fill('[data-testid="f-prefix"]', "PARTIAL-SCAN")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-testid="results-partial"]')

                # Assert that selection buttons do NOT exist or are disabled in PARTIAL results
                assert page.locator("button:has-text('Open')").count() == 0
                assert "Results are incomplete, so selection is disabled." in page.locator('[data-testid="results-partial"]').inner_text()
        finally:
            browser.close()

def test_p2b_invoice_scope_switch_clears_state(vite_fixture_server):
    """Switching company or scope key immediately clears results and open document."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            with LifecycleGuard(browser) as guard:
                page = guard.page

                def mock_api(route, path):
                    req_rid = (route.request.post_data_json or {}).get("request_id") or DEFAULT_RID

                    if "invoice_context" in path:
                        req_data = route.request.post_data_json
                        comp = req_data.get("company_candidate", "DefaultCorp")
                        ctx_ver = f"ctx_{comp}_v1"
                        ctx_body = {
                            "message": build_envelope(
                                "invoice.context",
                                status="OK",
                                reason="CONTEXT_READY",
                                request_id=req_rid,
                                context_version=ctx_ver,
                                data={
                                    "context_ref": f"ref.v1.ctx.{comp}",
                                    "context_version": ctx_ver,
                                    "company_label": f"Verified {comp}",
                                    "allowed_filters": ["invoice_name_prefix", "posting_date", "docstatus"],
                                    "expires_at": "2099-01-01T00:00:00+00:00",
                                    "default_posting_from": "2026-07-15",
                                    "default_posting_to": "2026-10-12",
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(ctx_body))
                        return True

                    if "invoice_search" in path:
                        req_data = route.request.post_data_json or {}
                        expected_ver = req_data.get("expected_context_version", "ctx_demo_v1")
                        search_body = {
                            "message": build_envelope(
                                "invoice.search",
                                status="OK",
                                reason="RESULTS_FOUND",
                                request_id=req_rid,
                                context_version=expected_ver,
                                data={
                                    "items": [
                                        {
                                            "invoice_type": "SALES",
                                            "invoice_id": "SINV-SWITCH-001",
                                            "posting_date": "2026-10-01",
                                            "docstatus": 1,
                                            "record_version": "rec_001",
                                            "selection_ref": "ref.sel.001",
                                        }
                                    ],
                                    "returned_count": 1,
                                    "total_count": None,
                                    "page_complete": True,
                                    "has_more": False,
                                    "next_cursor": None,
                                    "selection_required": True,
                                    "limitations": None,
                                }
                            )
                        }
                        route.fulfill(status=200, content_type="application/json", body=json.dumps(search_body))
                        return True

                    return False

                guard.mock_handler = mock_api

                page.goto(FIXTURE_URL, wait_until="networkidle")
                page.click("#btn-mode-invoice")
                page.wait_for_selector('[data-testid="company-label"]')

                # Run search
                page.fill('[data-testid="f-prefix"]', "SINV-SWITCH")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-invoice-id="SINV-SWITCH-001"]')

                # Switch company to Company B
                page.click("#btn-inv-company-b")

                # Results must be purged immediately
                page.wait_for_timeout(300)
                assert page.locator('[data-invoice-id="SINV-SWITCH-001"]').count() == 0
                assert page.locator('[data-testid="company-label"]').inner_text() == "Verified Company B"
        finally:
            browser.close()

def test_p1_01_real_mounted_reproduction(vite_fixture_server):
    """
    P1-01 Real Mounted Reproduction & Verification:
    1. Mount VercelChatPanel in Panel mode.
    2. Switch to Invoice Actions tab.
    3. Switch to DEMO profile.
    4. Switch to Chat tab, then back to Invoice Actions.
    5. Search DEMO-SINV -> 2 DEMO rows returned.
    6. Open second record (DEMO-SINV-2026-0002) -> Read-only view displays approved fields.
    7. Switch to CORE profile -> DEMO records and read view purged immediately.
    8. Perform search under CORE -> RPC returns 503 CAPABILITY_DISABLED, 0 DEMO records leak.
    9. Switch back to DEMO -> recovers cleanly.
    10. Switch between DEMO scenarios (PARTIAL, EMPTY, FORBIDDEN, NORMAL) without remount.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            with LifecycleGuard(browser) as guard:
                page = guard.page

                def mock_api(route, path):
                    req_rid = (route.request.post_data_json or {}).get("request_id") or DEFAULT_RID

                    if "invoice_actions_api.get_context" in path or "invoice_context" in path:
                        disabled_body = {
                            "message": build_envelope(
                                "invoice.context",
                                status="NOT_AVAILABLE",
                                reason="CAPABILITY_DISABLED",
                                request_id=req_rid,
                                data=None,
                            )
                        }
                        route.fulfill(status=503, content_type="application/json", body=json.dumps(disabled_body))
                        return True

                    if "invoice_actions_api.search_invoices" in path or "invoice_search" in path:
                        disabled_body = {
                            "message": build_envelope(
                                "invoice.search",
                                status="NOT_AVAILABLE",
                                reason="CAPABILITY_DISABLED",
                                request_id=req_rid,
                                data=None,
                            )
                        }
                        route.fulfill(status=503, content_type="application/json", body=json.dumps(disabled_body))
                        return True

                    return False

                guard.mock_handler = mock_api

                page.goto(FIXTURE_URL, wait_until="networkidle")
                page.click("#btn-mode-panel")

                # Step 1: Switch to Invoice Actions tab in VercelChatPanel
                page.get_by_role("tab", name="Invoice Actions mode").click()
                page.wait_for_selector('[aria-label="Select DEMO profile"]')

                # Step 2: Switch to DEMO profile
                page.get_by_role("button", name="Select DEMO profile").click()
                page.wait_for_selector("text=DEMO DATA (ISOLATED SYNTHETIC PROFILE)")

                # Step 3: Switch to Chat tab, then back to Invoice Actions
                page.get_by_role("tab", name="Chat mode").click()
                page.wait_for_selector("textarea")
                page.get_by_role("tab", name="Invoice Actions mode").click()

                # Step 4: Search DEMO-SINV
                page.fill('[data-testid="f-prefix"]', "DEMO-SINV")
                page.click('[data-testid="search-btn"]')

                # Step 5: Verify 3 DEMO rows appear
                page.wait_for_selector('[data-testid="results"]')
                rows = page.locator('[data-testid="result-row"]')
                assert rows.count() == 3
                assert page.locator('[data-invoice-id="DEMO-SINV-2026-002"]').count() == 1

                # Step 6: Open second record
                page.locator('[data-invoice-id="DEMO-SINV-2026-002"] [data-testid="open-btn"]').click()
                page.wait_for_selector('[data-testid="read-view"]')
                assert page.locator('[data-testid="f-invoice-id"]').inner_text() == "DEMO-SINV-2026-002"

                # Step 7: Switch to CORE profile
                page.get_by_role("button", name="Select CORE profile").click()

                # Step 8: VERIFY P1-01 FIX: Protected DEMO state is completely purged
                page.wait_for_timeout(200)
                assert page.locator('[data-testid="read-view"]').count() == 0
                assert page.locator('[data-invoice-id="DEMO-SINV-2026-002"]').count() == 0
                assert page.locator('[data-testid="results"]').count() == 0
                assert page.locator('[data-testid="f-prefix"]').input_value() == ""

                # Step 9: Verify truthful 503 disabled notice under CORE, search button disabled, 0 DEMO rows
                notice = page.wait_for_selector('[data-testid="notice"][data-reason="DISABLED"]')
                assert "Invoice lookup is not enabled" in notice.inner_text()
                assert page.locator('[data-testid="search-btn"]').is_disabled()
                assert page.locator('[data-invoice-id="DEMO-SINV-2026-001"]').count() == 0
                assert page.locator('[data-invoice-id="DEMO-SINV-2026-002"]').count() == 0
                assert page.locator('[data-invoice-id="DEMO-SINV-2026-003"]').count() == 0

                # Step 10: Switch CORE -> DEMO cleanly
                page.get_by_role("button", name="Select DEMO profile").click()
                page.wait_for_selector("text=DEMO DATA (ISOLATED SYNTHETIC PROFILE)")
                assert page.locator('[data-testid="notice"][data-reason="DISABLED"]').count() == 0
                assert not page.locator('[data-testid="search-btn"]').is_disabled()

                # Step 11: Switch scenarios without remount
                # NORMAL -> PARTIAL
                page.select_option("#demo-scenario-select", "PARTIAL")
                page.fill('[data-testid="f-prefix"]', "DEMO-SINV")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-testid="results-partial"]')
                assert page.locator("button:has-text('Open')").count() == 0

                # PARTIAL -> EMPTY
                page.select_option("#demo-scenario-select", "EMPTY")
                page.fill('[data-testid="f-prefix"]', "DEMO-SINV")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-testid="results-empty"]')

                # FORBIDDEN
                page.select_option("#demo-scenario-select", "FORBIDDEN")
                notice = page.wait_for_selector('[data-testid="notice"][data-kind="denied"]')
                assert "You do not have permission" in notice.inner_text()
                assert page.locator('[data-testid="search-btn"]').is_disabled()

                # FORBIDDEN -> NORMAL
                page.select_option("#demo-scenario-select", "NORMAL")
                page.wait_for_selector('[data-testid="company-label"]')
                assert not page.locator('[data-testid="search-btn"]').is_disabled()
                page.fill('[data-testid="f-prefix"]', "DEMO-SINV")
                page.click('[data-testid="search-btn"]')
                page.wait_for_selector('[data-testid="results"]')
                assert page.locator('[data-testid="result-row"]').count() == 3
        finally:
            browser.close()

def test_p2_07_mobile_and_accessibility(vite_fixture_server):
    """
    P2-07 Mobile Viewport (390x844) & Accessibility:
    1. Verify 390x844 viewport: no clipping, mode switcher fits, tabs usable.
    2. Accessible names and ARIA attributes for scenario selector and tabs.
    3. Drawer bubble button and open window at 390x844: no horizontal overflow.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            with LifecycleGuard(browser) as guard:
                page = guard.page

                def mock_api(route, path):
                    req_rid = (route.request.post_data_json or {}).get("request_id") or DEFAULT_RID
                    if "invoice_actions_api.get_context" in path or "invoice_context" in path:
                        disabled_body = {
                            "message": build_envelope(
                                "invoice.context",
                                status="DISABLED",
                                reason="CAPABILITY_DISABLED",
                                request_id=req_rid,
                                data=None,
                            )
                        }
                        route.fulfill(status=503, content_type="application/json", body=json.dumps(disabled_body))
                        return True
                    return False

                guard.mock_handler = mock_api
                page.set_viewport_size({"width": 390, "height": 844})
                page.goto(FIXTURE_URL, wait_until="networkidle")
                page.click("#btn-mode-panel")

                # Verify mode tabs fit within 390px
                tabs_container = page.wait_for_selector('[role="tablist"][aria-label="Copilot modes"]')
                box = tabs_container.bounding_box()
                assert box is not None
                assert box["x"] + box["width"] <= 390

                # Switch to Invoice Actions mode
                page.get_by_role("tab", name="Invoice Actions mode").click()

                # Verify scenario selector has accessible name
                page.get_by_role("button", name="Select DEMO profile").click()
                scenario_select = page.wait_for_selector("#demo-scenario-select")
                assert scenario_select.get_attribute("aria-label") == "Test Scenario"
                label = page.locator('label[for="demo-scenario-select"]')
                assert label.inner_text() == "Test Scenario:"

                # Switch to Drawer mode
                page.click("#btn-mode-drawer")
                fab = page.wait_for_selector('button[aria-label="Open Lotus Fin AI Copilot"]')
                assert fab.is_visible()
                fab.click()

                # Verify drawer window at 390px does not overflow screen
                drawer_win = page.wait_for_selector('.fixed.bottom-5.right-4')
                d_box = drawer_win.bounding_box()
                assert d_box is not None
                assert d_box["width"] <= 390
                assert d_box["x"] + d_box["width"] <= 390

                # Close drawer
                page.get_by_role("button", name="Close panel").click()
                page.wait_for_timeout(200)
                assert page.locator('button[aria-label="Open Lotus Fin AI Copilot"]').is_visible()
        finally:
            browser.close()

