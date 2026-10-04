"""
Regression tests for AI003 foundation remediation (AI001/AI002 platform blockers
documented in docs/features/AI003/AI003_MASTER_SSOT.md §23).

Buckets covered:
- Bucket A: AI001 fail-closed source validation — malformed AR/AP rows, unknown
  report status, missing `data` and mixed valid/invalid rows become typed
  unavailable/error states; only status=success + valid data list + legitimate
  empty result yields a verified zero.
- Bucket B: AI001 request/cutoff validation — full ISO `as_of` validation,
  rejection of as_of < period_start, mid-period cutoff semantics, consistent
  effective period length for previous-period comparison, zero prior
  denominator handling.
- Bucket C: currency safety — server-side accounting-currency authority, no
  client currency relabeling, FX unsupported rejection, cross-currency
  comparison block, Finance Book explicitly NOT_SUPPORTED in AI002.
- Bucket D: AI002 cache authorization — cache hits re-authorize report access;
  revoked permissions yield FORBIDDEN with no cached financial data and eviction;
  regranting restores authorized behavior; cache isolation between users is
  preserved.
"""

import sys
import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Add repo to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_snapshot import (
    build_financial_snapshot,
    parse_ar_data,
    parse_ap_data,
    validate_source_payload,
    FinancialSourceDataError,
)
from lotus_fin.ai.financial_health import build_comparison_block, compute_metric_change
from lotus_fin.cashflow.models import (
    ForecastRequest,
    ForecastStatus,
    OpeningCash,
    AccountBalance,
)
from lotus_fin.cashflow.adapters import ObligationSourceError, check_party_type_preflight
from lotus_fin.cashflow.cache import _CACHE_STORE, compute_cache_key
from lotus_fin.cashflow.source_interface import FailClosedSource
from lotus_fin.cashflow.service import get_cash_forecast


GOLD_PNL = [
    {"account_name": "Sales Revenue", "balance": 700000.00},
    {"account_name": "Service Income", "balance": 300000.00},
    {"account_name": "Cost of Goods Sold - Materials", "balance": 450000.00},
    {"account_name": "COGS - Direct Labor", "balance": 150000.00},
]
GOLD_TB = [
    {"account_name": "Cash on Hand", "account_type": "Cash", "closing_balance": 50000.00},
]


def _ok(data):
    return {"status": "success", "data": data}


class TestBucketAFailClosedSourceValidation(unittest.TestCase):
    """Bucket A: malformed source data must never collapse to a verified zero."""

    # --- parser-level fail-closed ---
    def test_malformed_ar_row_missing_amount_raises(self):
        """SSOT §23 controlled replay: a row without any amount field must be
        a typed error, not an apparent zero."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([{"party": "X"}], as_of_date=date(2026, 9, 26))

    def test_malformed_ap_row_missing_amount_raises(self):
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([{"party": "X"}])

    def test_malformed_ar_amount_unparseable_raises(self):
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(
                [{"party": "A", "outstanding_amount": "not-a-number"}],
                as_of_date=date(2026, 9, 26),
            )

    def test_malformed_ap_amount_unparseable_raises(self):
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([{"party": "S", "outstanding_amount": None}])

    def test_non_dict_ar_row_raises(self):
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(
                [{"party": "A", "outstanding_amount": 10.0}, "garbage"],
                as_of_date=date(2026, 9, 26),
            )

    def test_mixed_valid_and_invalid_rows_fail_closed(self):
        """One malformed row invalidates the whole source — no partial sums."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(
                [
                    {"party": "A", "outstanding_amount": 100.0},
                    {"party": "B"},
                ],
                as_of_date=date(2026, 9, 26),
            )

    def test_legitimate_success_empty_is_verified_zero(self):
        total, overdue, ratio, lims = parse_ar_data([], as_of_date=date(2026, 9, 26))
        self.assertEqual(total, Decimal("0.00"))
        self.assertEqual(overdue, Decimal("0.00"))
        self.assertEqual(ratio, Decimal("0.00"))
        ap_total, ap_lims = parse_ap_data([])
        self.assertEqual(ap_total, Decimal("0.00"))

    # --- envelope-level fail-closed (validate_source_payload) ---
    def test_validate_source_payload_unknown_status_rejected(self):
        ok, data, err = validate_source_payload("accounts_receivable", {"status": "mystery", "data": []})
        self.assertFalse(ok)
        self.assertIn("unknown report status", err)

    def test_validate_source_payload_missing_data_rejected(self):
        ok, data, err = validate_source_payload("accounts_receivable", {"status": "success"})
        self.assertFalse(ok)
        self.assertIn("missing the 'data' payload", err)

    def test_validate_source_payload_non_list_data_rejected(self):
        ok, data, err = validate_source_payload("accounts_receivable", {"status": "success", "data": {"a": 1}})
        self.assertFalse(ok)

    def test_validate_source_payload_success_empty_accepted(self):
        ok, data, err = validate_source_payload("accounts_receivable", {"status": "success", "data": []})
        self.assertTrue(ok)
        self.assertEqual(data, [])

    # --- snapshot-level behavior ---
    def _base_sources(self, **overrides):
        sources = {
            "profit_and_loss": GOLD_PNL,
            "trial_balance": GOLD_TB,
            "accounts_receivable": [],
            "accounts_payable": [],
        }
        sources.update(overrides)
        return sources

    def test_unknown_report_status_becomes_unavailable_not_zero(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=self._base_sources(
                accounts_receivable={"status": "mystery", "data": []},
            ),
        )
        self.assertNotEqual(snapshot["status"], "OK")
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ar_outstanding"]["value"])
        self.assertEqual(metrics["overdue_ar_ratio"]["status"], "UNAVAILABLE")
        self.assertIn("accounts_receivable", snapshot["missing_inputs"])

    def test_missing_data_key_becomes_unavailable_not_zero(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=self._base_sources(
                accounts_payable={"status": "success"},
            ),
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ap_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ap_outstanding"]["value"])
        self.assertIn("accounts_payable", snapshot["missing_inputs"])

    def test_success_empty_data_is_verified_zero(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=self._base_sources(
                accounts_receivable={"status": "success", "data": []},
                accounts_payable={"status": "success", "data": []},
            ),
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics["ar_outstanding"]["value"], 0.0)
        self.assertEqual(metrics["ap_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics["ap_outstanding"]["value"], 0.0)

    def test_malformed_row_in_success_payload_is_unavailable_not_zero(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=self._base_sources(
                accounts_receivable={"status": "success", "data": [{"party": "X"}]},
            ),
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ar_outstanding"]["value"])
        self.assertTrue(
            any("AR source data invalid" in lim for lim in snapshot["limitations"])
        )

    def test_mixed_rows_through_snapshot_fail_closed(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=self._base_sources(
                accounts_payable={
                    "status": "success",
                    "data": [
                        {"party": "S1", "outstanding_amount": 500.0},
                        {"party": "S2"},
                    ],
                },
            ),
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        # The valid 500.0 row must NOT be summed into an apparent total.
        self.assertEqual(metrics["ap_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ap_outstanding"]["value"])


class TestBucketBAsOfValidation(unittest.TestCase):
    """Bucket B: strict as_of validation and consistent previous-period alignment."""

    def test_invalid_as_of_rejected(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            as_of="2026-13-01",
        )
        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")
        self.assertTrue(
            any("Invalid as_of" in m for m in snapshot["missing_inputs"])
        )

    def test_garbage_as_of_rejected(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            as_of="not-a-date",
        )
        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")

    def test_as_of_before_period_start_rejected(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            as_of="2025-12-31",
        )
        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")
        self.assertTrue(
            any("before period_start" in m for m in snapshot["missing_inputs"])
        )

    def _recording_fetcher(self):
        calls = []

        def fetcher(key, filters, company):
            calls.append((key, dict(filters)))
            if key == "profit_and_loss":
                return _ok([{"account_name": "Sales Revenue", "balance": 100.0}])
            if key == "trial_balance":
                return _ok([{"account_type": "Cash", "balance": 5.0}])
            return _ok([])

        return calls, fetcher

    def test_mid_period_cutoff_uses_validated_as_of(self):
        """Mid-period cutoff flows into report filters; an explicit historical
        semantics limitation is preserved (no as_known_at support claim)."""
        calls, fetcher = self._recording_fetcher()
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            as_of="2026-06-30",
            source_fetcher=fetcher,
        )
        pnl_filters = [f for k, f in calls if k == "profit_and_loss"][0]
        self.assertEqual(pnl_filters["period_end_date"], "2026-06-30")
        ar_filters = [f for k, f in calls if k == "accounts_receivable"][0]
        self.assertEqual(ar_filters["report_date"], "2026-06-30")
        self.assertTrue(
            any("as_known_at" in lim for lim in snapshot["limitations"])
        )

    def test_previous_period_aligned_with_effective_length(self):
        """Previous window must use the same effective length as the current
        window: current cutoff 2026-06-30 (180 days) => prior P&L window
        2025-01-01..2025-06-30, not the full 2025 year."""
        calls, fetcher = self._recording_fetcher()
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            as_of="2026-06-30",
            comparison="PREVIOUS_PERIOD",
            source_fetcher=fetcher,
        )
        pnl_calls = [f for k, f in calls if k == "profit_and_loss"]
        self.assertEqual(len(pnl_calls), 2)
        self.assertEqual(pnl_calls[1]["period_start_date"], "2025-01-01")
        self.assertEqual(pnl_calls[1]["period_end_date"], "2025-06-30")
        ar_calls = [f for k, f in calls if k == "accounts_receivable"]
        self.assertEqual(len(ar_calls), 2)
        self.assertEqual(ar_calls[1]["report_date"], "2025-06-30")

    def test_previous_period_full_year_when_no_cutoff(self):
        """Without an as_of cutoff the previous period remains the full year."""
        calls, fetcher = self._recording_fetcher()
        build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            comparison="PREVIOUS_PERIOD",
            source_fetcher=fetcher,
        )
        pnl_calls = [f for k, f in calls if k == "profit_and_loss"]
        self.assertEqual(len(pnl_calls), 2)
        self.assertEqual(pnl_calls[1]["period_end_date"], "2025-12-31")

    def test_zero_prior_denominator_relative_change_unavailable(self):
        result = compute_metric_change(20.0, 0.0)
        self.assertEqual(result["status"], "AVAILABLE")
        self.assertIsNone(result["relative_change"])
        self.assertTrue(
            any("zero" in lim.lower() for lim in result["limitations"])
        )


class TestBucketCCurrencySafety(unittest.TestCase):
    """Bucket C: no client currency relabeling; Finance Book NOT_SUPPORTED."""

    def _build_with_frappe(self, company_currency, request_currency, raw_sources=None):
        fake_frappe = MagicMock()
        fake_frappe.local.db = object()
        sources = raw_sources or {
            "profit_and_loss": GOLD_PNL,
            "trial_balance": GOLD_TB,
            "accounts_receivable": [],
            "accounts_payable": [],
        }
        with patch.dict(sys.modules, {"frappe": fake_frappe}), patch(
            "lotus_fin.security.access.get_verified_company",
            return_value="Name (Demo)",
        ), patch(
            "lotus_fin.security.access.get_company_accounting_currency",
            return_value=company_currency,
        ):
            return build_financial_snapshot(
                company="Name (Demo)",
                period_start="2026-01-01",
                period_end="2026-12-31",
                currency=request_currency,
                raw_sources=sources,
            )

    def test_currency_tampering_rejected(self):
        """VND company + USD request must be a typed VALIDATION_ERROR, never a
        USD-labeled metric (SSOT §20 observed mismatch)."""
        snapshot = self._build_with_frappe("VND", "USD")
        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")
        self.assertTrue(
            any("FX conversion is not implemented" in m for m in snapshot["missing_inputs"])
        )
        for m in snapshot["metrics"]:
            self.assertNotEqual(m.get("currency_or_unit"), "USD")

    def test_matching_currency_normalized_to_server_value(self):
        snapshot = self._build_with_frappe("VND", "vnd")
        self.assertEqual(snapshot["status"], "OK")
        self.assertEqual(snapshot["currency"], "VND")

    def test_undetermined_company_currency_fails_closed(self):
        snapshot = self._build_with_frappe(None, "VND")
        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")
        self.assertTrue(
            any("could not be determined" in m for m in snapshot["missing_inputs"])
        )

    def test_get_company_accounting_currency_reads_server_value(self):
        from lotus_fin.security.access import get_company_accounting_currency

        fake_frappe = MagicMock()
        fake_frappe.db.get_value.return_value = "VND"
        with patch("lotus_fin.security.access.frappe", fake_frappe):
            self.assertEqual(get_company_accounting_currency("Name (Demo)"), "VND")
            fake_frappe.db.get_value.return_value = None
            self.assertIsNone(get_company_accounting_currency("Name (Demo)"))

    def test_comparison_blocks_cross_currency(self):
        current = {
            "company": "Name (Demo)",
            "currency": "VND",
            "metrics": [],
        }
        previous = {
            "company": "Name (Demo)",
            "currency": "USD",
            "metrics": [],
        }
        block = build_comparison_block(current, previous, correlation_id="t-currency")
        self.assertEqual(block["status"], "UNAVAILABLE")
        self.assertTrue(
            any("different currencies" in lim for lim in block["limitations"])
        )

    def test_ai002_finance_book_explicitly_not_supported(self):
        """The request contract carries finance_book; supplying it must fail
        closed with an explicit not-supported message — never silently ignored."""
        from lotus_fin.cashflow.models import ForecastRequest, CoverageScope
        from lotus_fin.cashflow.validation import validate_forecast_request
        from lotus_fin.cashflow.models import ReasonCode

        request = ForecastRequest(
            company="AI002 Fixture 2026",
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
            reporting_currency="VND",
            cash_account_scope=["Cash - A2F"],
            coverage_scope=CoverageScope.TRADE_ONLY,
            finance_book="Q1-2026",
        )
        valid, reason, message = validate_forecast_request(request)
        self.assertFalse(valid)
        self.assertIn("not supported", message)


class TestBucketDCacheAuthorization(unittest.TestCase):
    """Bucket D: cache hits must re-authorize report access; permission
    revocation inside the TTL yields FORBIDDEN with no cached financial data."""

    def setUp(self):
        from lotus_fin.cashflow import cache as cache_mod

        cache_mod._CACHE_STORE.clear()
        cache_mod._SINGLE_FLIGHT_LOCKS.clear()
        self.as_of = date(2026, 9, 26)
        self.start = date(2026, 9, 27)
        self.end = date(2026, 10, 26)
        self.opening = OpeningCash(
            aggregate_amount=Decimal("11550000"),
            reconciliation="ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
            has_constituent_deficit=False,
            accounts=[
                AccountBalance(
                    account="Cash - A2F",
                    amount=Decimal("11550000"),
                    currency="VND",
                    deficit=False,
                )
            ],
        )
        self.request = ForecastRequest(
            company="AI002 Fixture 2026",
            financial_as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.end,
            reporting_currency="VND",
            cash_account_scope=["Cash - A2F"],
        )

    def _service_context(self, opening_mock=None):
        return (
            patch(
                "lotus_fin.cashflow.service.validate_forecast_request",
                return_value=(True, None, None),
            ),
            patch(
                "lotus_fin.cashflow.service.get_opening_cash_ledger",
                opening_mock or MagicMock(return_value=self.opening),
            ),
            patch(
                "lotus_fin.cashflow.service.get_trade_obligations",
                MagicMock(return_value=[]),
            ),
            patch("lotus_fin.cashflow.service.frappe", MagicMock()),
        )

    def _run(self):
        return get_cash_forecast(
            request=self.request,
            user="perm-user@example.com",
            future_event_source=FailClosedSource(),
        )

    def test_revoked_permission_on_cache_hit_yields_forbidden_no_financial_data(self):
        ctx = self._service_context()
        with ctx[0], ctx[1], ctx[2], ctx[3], patch(
            "lotus_fin.security.access.check_ai002_report_permission"
        ) as perm:
            # 1. authorized call -> cache populated
            first = self._run()
            self.assertEqual(first.status, ForecastStatus.FORECAST_UNAVAILABLE)
            self.assertIsNotNone(first.opening_cash)

            # 2. role/report permission revoked; same user repeats request
            perm.side_effect = Exception("FORBIDDEN")
            second = self._run()
            self.assertEqual(second.status, ForecastStatus.FORBIDDEN)
            self.assertIsNone(second.opening_cash)
            self.assertEqual(len(second.obligations), 0)
            self.assertEqual(len(second.forecast_points), 0)
            self.assertEqual(len(second.cash_events), 0)

        # 3. the stale authorized entry was evicted
        key = compute_cache_key(
            user_id="perm-user@example.com",
            company=self.request.company,
            as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.end,
            account_scope=["Cash - A2F"],
            coverage_scope="TRADE_ONLY",
        )
        self.assertNotIn(key, _CACHE_STORE)

    def test_regranted_permission_restores_authorized_behavior(self):
        ctx = self._service_context()
        with ctx[0], ctx[1], ctx[2], ctx[3], patch(
            "lotus_fin.security.access.check_ai002_report_permission"
        ) as perm:
            first = self._run()
            self.assertEqual(first.status, ForecastStatus.FORECAST_UNAVAILABLE)

            perm.side_effect = Exception("FORBIDDEN")
            second = self._run()
            self.assertEqual(second.status, ForecastStatus.FORBIDDEN)

            # permission re-granted -> authorized behavior restored
            perm.side_effect = None
            third = self._run()
            self.assertNotEqual(third.status, ForecastStatus.FORBIDDEN)
            self.assertEqual(third.status, ForecastStatus.FORECAST_UNAVAILABLE)
            self.assertIsNotNone(third.opening_cash)

    def test_cache_isolation_between_users_preserved(self):
        """Bucket D must not weaken cache isolation: different users never
        share cache entries (a second user's call recomputes)."""
        opening_mock = MagicMock(return_value=self.opening)
        ctx = self._service_context(opening_mock=opening_mock)
        with ctx[0], ctx[1], ctx[2], ctx[3], patch(
            "lotus_fin.security.access.check_ai002_report_permission"
        ):
            r1 = get_cash_forecast(
                request=self.request,
                user="userA@example.com",
                future_event_source=FailClosedSource(),
            )
            r2 = get_cash_forecast(
                request=self.request,
                user="userB@example.com",
                future_event_source=FailClosedSource(),
            )
        self.assertEqual(r1.status, ForecastStatus.FORECAST_UNAVAILABLE)
        self.assertEqual(r2.status, ForecastStatus.FORECAST_UNAVAILABLE)
        # Each user's first call computed independently: two source reads.
        self.assertEqual(opening_mock.call_count, 2)


class TestWV01ReportFooterNormalization(unittest.TestCase):
    """WV-01: Frappe query_report total footer normalization & edge case rejection."""

    def setUp(self):
        from lotus_fin.api.key_reports import is_valid_frappe_report_footer, normalize_frappe_report_footer
        from lotus_fin.cashflow.adapters import _parse_report_rows
        self.is_valid_footer = is_valid_frappe_report_footer
        self.normalize_footer = normalize_frappe_report_footer
        self.parse_report_rows = _parse_report_rows
        self.columns = [
            {"fieldname": "posting_date", "label": "Date"},
            {"fieldname": "party", "label": "Customer"},
            {"fieldname": "voucher_type", "label": "Voucher Type"},
            {"fieldname": "voucher_no", "label": "Voucher No"},
            {"fieldname": "invoiced_amount", "label": "Invoiced"},
            {"fieldname": "outstanding_amount", "label": "Outstanding"},
        ]
        self.valid_data_rows = [
            {"posting_date": "2026-09-01", "party": "Cust A", "voucher_type": "Sales Invoice", "voucher_no": "SINV-001", "invoiced_amount": 100, "outstanding_amount": 100},
            {"posting_date": "2026-09-02", "party": "Cust B", "voucher_type": "Sales Invoice", "voucher_no": "SINV-002", "invoiced_amount": 200, "outstanding_amount": 200},
        ]
        self.valid_footer_row = [None, "Total", None, None, 300, 300]

    def test_valid_list_footer_normalized_successfully(self):
        rows = list(self.valid_data_rows) + [self.valid_footer_row]
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        self.assertTrue(has_total)
        self.assertEqual(len(clean_rows), 2)
        self.assertEqual(total_row, self.valid_footer_row)

        # Adapters boundary parsing
        payload = {
            "status": "success",
            "columns": self.columns,
            "add_total_row": 1,
            "data": rows,
        }
        res = self.parse_report_rows(payload, "Accounts Receivable")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["voucher_no"], "SINV-001")

        # Snapshot source validation
        ok, res_data, err = validate_source_payload("accounts_receivable", payload)
        self.assertTrue(ok)
        self.assertEqual(len(res_data), 2)

    def test_list_row_in_middle_rejected(self):
        # A list row at index 0 or 1 is NOT a valid footer
        rows = [self.valid_footer_row] + list(self.valid_data_rows)
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        self.assertFalse(has_total)
        # Should remain un-stripped so subsequent dict check catches it and fails closed
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(clean_rows, as_of_date=date(2026, 9, 26))

        payload = {
            "status": "success",
            "columns": self.columns,
            "add_total_row": 1,
            "data": rows,
        }
        with self.assertRaises(ObligationSourceError):
            self.parse_report_rows(payload, "Accounts Receivable")

    def test_multiple_list_rows_rejected(self):
        # Two list rows at the end
        rows = list(self.valid_data_rows) + [self.valid_footer_row, self.valid_footer_row]
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        # One was stripped as footer, but the earlier list row remains and fails closed
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(clean_rows, as_of_date=date(2026, 9, 26))

    def test_footer_with_wrong_column_count_rejected(self):
        short_footer = [None, "Total", 300]  # len 3 != len 6
        self.assertFalse(self.is_valid_footer("Accounts Receivable", self.columns, short_footer, True, False))
        rows = list(self.valid_data_rows) + [short_footer]
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        self.assertFalse(has_total)

    def test_footer_with_voucher_no_populated_rejected(self):
        bad_footer = [None, "Total", "Sales Invoice", "SINV-999", 300, 300]
        self.assertFalse(self.is_valid_footer("Accounts Receivable", self.columns, bad_footer, True, False))
        rows = list(self.valid_data_rows) + [bad_footer]
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        self.assertFalse(has_total)

    def test_summary_row_dict_fails_closed(self):
        """WR-01 recheck: a dict total/summary row is not a verified Frappe v16
        output shape (the verified footer is a list row separated by
        normalize_frappe_report_footer). Trailing or mid-report, it must fail
        closed instead of being silently skipped into an apparent zero."""
        summary_dict = {"party": "Total", "outstanding_amount": 300, "invoiced_amount": 300}

        # Trailing dict summary — adapter boundary raises, no silent filter
        rows = list(self.valid_data_rows) + [summary_dict]
        payload = {
            "status": "success",
            "columns": self.columns,
            "data": rows,
        }
        with self.assertRaises(ObligationSourceError):
            self.parse_report_rows(payload, "Accounts Receivable")
        # Snapshot parser raises as well
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(rows, as_of_date=date(2026, 9, 26))

        # Mid-report dict summary — previously dropped silently by the adapter
        mid_rows = [self.valid_data_rows[0], summary_dict, self.valid_data_rows[1]]
        mid_payload = {
            "status": "success",
            "columns": self.columns,
            "data": mid_rows,
        }
        with self.assertRaises(ObligationSourceError):
            self.parse_report_rows(mid_payload, "Accounts Receivable")
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(mid_rows, as_of_date=date(2026, 9, 26))

    def test_footer_with_unexpected_descriptive_field_rejected(self):
        # A list row with a descriptive field populated (like posting_date) must NOT be treated as a footer
        bad_footer = ["2026-09-26", "Total", None, None, 300, 300]
        self.assertFalse(self.is_valid_footer("Accounts Receivable", self.columns, bad_footer, True, False))
        rows = list(self.valid_data_rows) + [bad_footer]
        clean_rows, total_row, has_total = self.normalize_footer(
            "Accounts Receivable", self.columns, rows, add_total_row=True, skip_total_row=False
        )
        self.assertFalse(has_total)

    def test_all_empty_candidate_footer_rejected(self):
        # A candidate footer containing only empty strings has no aggregates and is rejected
        empty_footer = ["", "", "", "", "", ""]
        self.assertFalse(self.is_valid_footer("Accounts Receivable", self.columns, empty_footer, True, False))

    def test_string_column_definitions_footer_normalized(self):
        str_columns = [
            "Posting Date:Date:90",
            "Customer:Link/Customer:120",
            "Voucher Type:Data:120",
            "Voucher No:Link/Sales Invoice:120",
            "Invoiced:Currency:100",
            "Outstanding:Currency:100",
        ]
        valid_footer = ["", "", "", "", 300.0, 300.0]
        self.assertTrue(self.is_valid_footer("Accounts Receivable", str_columns, valid_footer, True, False))

        bad_footer = ["", "", "", "SINV-001", 300.0, 300.0]
        self.assertFalse(self.is_valid_footer("Accounts Receivable", str_columns, bad_footer, True, False))

    def test_skip_total_row_string_zero_handled(self):
        # HTTP form dicts or JSON envelopes may provide "0" as string
        self.assertTrue(self.is_valid_footer("Accounts Receivable", self.columns, self.valid_footer_row, "1", "0"))
        self.assertFalse(self.is_valid_footer("Accounts Receivable", self.columns, self.valid_footer_row, "1", "1"))


class TestWV02MasterDataAndVoucherSafety(unittest.TestCase):
    """WV-02: Party Type preflight check and cross-leg voucher/party rejection."""

    def test_ar_cross_leg_party_rejected(self):
        row = {"party": "Supp A", "party_type": "Supplier", "voucher_no": "SINV-001", "outstanding_amount": 100}
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([row], as_of_date=date(2026, 9, 26))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [row]},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )

    def test_ar_cross_leg_voucher_rejected(self):
        row = {"party": "Cust A", "voucher_type": "Purchase Invoice", "voucher_no": "PINV-001", "outstanding_amount": 100}
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([row], as_of_date=date(2026, 9, 26))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [row]},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )

    def test_ap_cross_leg_party_rejected(self):
        row = {"party": "Cust A", "party_type": "Customer", "voucher_no": "PINV-001", "outstanding_amount": 100}
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([row])

        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [row]},
                "AP",
                ("party",),
                "Purchase Invoice",
                "VND",
                "Accounts Payable",
            )

    def test_ap_cross_leg_voucher_rejected(self):
        row = {"party": "Supp A", "voucher_type": "Sales Invoice", "voucher_no": "SINV-001", "outstanding_amount": 100}
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([row])

        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [row]},
                "AP",
                ("party",),
                "Purchase Invoice",
                "VND",
                "Accounts Payable",
            )

    def test_preflight_receivable_missing_customer_fails_closed(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_all.side_effect = lambda dt, filters=None, pluck=None: (
            ["Student"] if filters and filters.get("account_type") == "Receivable" else ["Supplier"]
        )
        fake_frappe.db.get_value.return_value = {"company": "Test Co", "docstatus": 1}
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                check_party_type_preflight()
            self.assertIn("Customer", str(ctx.exception))

    def test_preflight_payable_missing_supplier_fails_closed(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_all.side_effect = lambda dt, filters=None, pluck=None: (
            ["Customer"] if filters and filters.get("account_type") == "Receivable" else ["Employee"]
        )
        fake_frappe.db.get_value.return_value = {"company": "Test Co", "docstatus": 1}
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                check_party_type_preflight()
            self.assertIn("Supplier", str(ctx.exception))

    def test_db_company_mismatch_rejected(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_value.return_value = {"company": "Wrong Co", "docstatus": 1}

        from lotus_fin.cashflow.adapters import _collect_obligations
        row = {"party": "Cust A", "voucher_no": "SINV-001", "outstanding": 100}
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                _collect_obligations(
                    {"status": "success", "data": [row]},
                    "AR",
                    ("party",),
                    "Sales Invoice",
                    "VND",
                    "Accounts Receivable",
                    company="Target Co",
                )
            self.assertIn("company mismatch", str(ctx.exception))

    def test_db_non_submitted_voucher_rejected(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_value.return_value = {"company": "Target Co", "docstatus": 0}

        from lotus_fin.cashflow.adapters import _collect_obligations
        row = {"party": "Cust A", "voucher_no": "SINV-001", "outstanding": 100}
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                _collect_obligations(
                    {"status": "success", "data": [row]},
                    "AR",
                    ("party",),
                    "Sales Invoice",
                    "VND",
                    "Accounts Receivable",
                    company="Target Co",
                )
            self.assertIn("is not submitted", str(ctx.exception))

    def test_payment_entry_cross_leg_rejected(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_value.return_value = {
            "company": "Target Co",
            "docstatus": 1,
            "payment_type": "Pay",
            "party_type": "Supplier",
            "party": "Supp X",
        }

        row = {"party": "Cust A", "voucher_type": "Payment Entry", "voucher_no": "ACC-PAY-001", "outstanding": 100}
        with patch("lotus_fin.core.domain.calculators.ar_extractor.frappe", fake_frappe):
            with self.assertRaises(FinancialSourceDataError) as ctx:
                parse_ar_data([row], company="Target Co")
            self.assertIn("Supplier/Pay Payment Entry", str(ctx.exception))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                _collect_obligations(
                    {"status": "success", "data": [row]},
                    "AR",
                    ("party",),
                    "Sales Invoice",
                    "VND",
                    "Accounts Receivable",
                    company="Target Co",
                )
            self.assertIn("Supplier/Pay Payment Entry", str(ctx.exception))

    def test_payment_entry_non_existent_rejected(self):
        fake_frappe = MagicMock()
        fake_frappe.db.get_value.return_value = None

        row = {"party": "Cust A", "voucher_type": "Payment Entry", "voucher_no": "ACC-PAY-999", "outstanding": 100}
        with patch("lotus_fin.core.domain.calculators.ar_extractor.frappe", fake_frappe):
            with self.assertRaises(FinancialSourceDataError) as ctx:
                parse_ar_data([row], company="Target Co")
            self.assertIn("non-existent Payment Entry", str(ctx.exception))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                _collect_obligations(
                    {"status": "success", "data": [row]},
                    "AR",
                    ("party",),
                    "Sales Invoice",
                    "VND",
                    "Accounts Receivable",
                    company="Target Co",
                )
            self.assertIn("non-existent Payment Entry", str(ctx.exception))

    def test_party_account_validation_checks(self):
        # Non-existent account
        fake_frappe = MagicMock()
        def mock_get_value(doctype, name, fields=None, as_dict=False):
            if doctype == "Sales Invoice":
                return {"company": "Target Co", "docstatus": 1, "customer": "Cust A"}
            if doctype == "Account":
                return None
            return None
        fake_frappe.db.get_value.side_effect = mock_get_value

        row = {"party": "Cust A", "voucher_no": "SINV-001", "party_account": "Missing Acc", "outstanding": 100}
        with patch("lotus_fin.core.domain.calculators.ar_extractor.frappe", fake_frappe):
            with self.assertRaises(FinancialSourceDataError) as ctx:
                parse_ar_data([row], company="Target Co")
            self.assertIn("does not exist", str(ctx.exception))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with patch("lotus_fin.cashflow.adapters.frappe", fake_frappe):
            with self.assertRaises(ObligationSourceError) as ctx:
                _collect_obligations(
                    {"status": "success", "data": [row]},
                    "AR",
                    ("party",),
                    "Sales Invoice",
                    "VND",
                    "Accounts Receivable",
                    company="Target Co",
                )
            self.assertIn("does not exist", str(ctx.exception))

        # Account company mismatch
        def mock_get_value_co_mismatch(doctype, name, fields=None, as_dict=False):
            if doctype == "Sales Invoice":
                return {"company": "Target Co", "docstatus": 1, "customer": "Cust A"}
            if doctype == "Account":
                return {"company": "Wrong Co", "account_type": "Receivable"}
            return None
        fake_frappe.db.get_value.side_effect = mock_get_value_co_mismatch
        with patch("lotus_fin.core.domain.calculators.ar_extractor.frappe", fake_frappe):
            with self.assertRaises(FinancialSourceDataError) as ctx:
                parse_ar_data([row], company="Target Co")
            self.assertIn("company mismatch", str(ctx.exception))

        # Account type mismatch
        def mock_get_value_type_mismatch(doctype, name, fields=None, as_dict=False):
            if doctype == "Sales Invoice":
                return {"company": "Target Co", "docstatus": 1, "customer": "Cust A"}
            if doctype == "Account":
                return {"company": "Target Co", "account_type": "Payable"}
            return None
        fake_frappe.db.get_value.side_effect = mock_get_value_type_mismatch
        with patch("lotus_fin.core.domain.calculators.ar_extractor.frappe", fake_frappe):
            with self.assertRaises(FinancialSourceDataError) as ctx:
                parse_ar_data([row], company="Target Co")
            self.assertIn("expected 'Receivable'", str(ctx.exception))

    def test_foreign_currency_in_row_rejected(self):
        row = {"party": "Cust A", "voucher_no": "SINV-001", "currency": "USD", "outstanding": 100}
        with self.assertRaises(FinancialSourceDataError) as ctx:
            parse_ar_data([row], currency="VND")
        self.assertIn("unsupported currency", str(ctx.exception))

        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError) as ctx:
            _collect_obligations(
                {"status": "success", "data": [row]},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )
        self.assertIn("unsupported currency", str(ctx.exception))

    def test_report_envelope_mismatch_rejected(self):
        # Report name mismatch
        bad_name_payload = {
            "status": "success",
            "report_name": "Accounts Payable",
            "company": "Target Co",
            "data": [],
        }
        ok, _, err = validate_source_payload("accounts_receivable", bad_name_payload, expected_company="Target Co")
        self.assertFalse(ok)
        self.assertIn("report_name mismatch", err)

        # Company mismatch
        bad_comp_payload = {
            "status": "success",
            "report_name": "Accounts Receivable",
            "company": "Wrong Co",
            "data": [],
        }
        ok, _, err = validate_source_payload("accounts_receivable", bad_comp_payload, expected_company="Target Co")
        self.assertFalse(ok)
        self.assertIn("company mismatch", err)


class TestWR01WR02UntrustedSummaryAndVoucherlessRows(unittest.TestCase):
    """WR-01/WR-02 recheck regressions: untrusted dict summary rows are never
    skipped into an apparent zero, and AI001 never sums voucher-less rows.
    Both AI001 and AI002 stay fail-closed and consistent."""

    # --- WR-01: untrusted dict summary rows ---

    def test_wr01_repro_is_total_row_dict_alone_is_not_verified_zero(self):
        """Minimal recheck repro: parse_ar_data([{"is_total_row": True, "outstanding": 123}])
        must raise, not return AR=0."""
        from lotus_fin.cashflow.adapters import _parse_report_rows
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([{"is_total_row": True, "outstanding": 123}])
        with self.assertRaises(ObligationSourceError):
            _parse_report_rows(
                {"status": "success", "data": [{"is_total_row": True, "outstanding": 123}]},
                "Accounts Receivable",
            )

    def test_wr01_fake_truthy_marker_raises(self):
        for marker in (1, "1", "true", "yes"):
            with self.assertRaises(FinancialSourceDataError):
                parse_ar_data([{"is_total_row": marker, "outstanding": 123}])
            with self.assertRaises(FinancialSourceDataError):
                parse_ap_data([{"is_total_row": marker, "outstanding": 123}])

    def test_wr01_all_summary_report_raises(self):
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(
                [
                    {"is_total_row": True, "outstanding": 10},
                    {"party": "Total", "outstanding": 20},
                ]
            )
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data(
                [
                    {"is_total_row": True, "outstanding": 10},
                    {"party": "Total", "outstanding": 20},
                ]
            )

    def test_wr01_trailing_party_total_dict_raises(self):
        """The old contract skipped a trailing voucher-less party="Total" dict;
        verified raw Frappe behavior has no such shape, so it fails closed."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(
                [
                    {"party": "A", "voucher_no": "SINV-1", "outstanding": 100},
                    {"party": "Total", "outstanding": 100},
                ]
            )

    def test_wr01_mixed_valid_and_fake_summary_raises(self):
        rows = [
            {"party": "A", "voucher_no": "SINV-1", "outstanding": 100},
            {"is_total_row": True, "outstanding": 999},
            {"party": "B", "voucher_no": "SINV-2", "outstanding": 200},
        ]
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data(rows, as_of_date=date(2026, 9, 26))
        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": rows},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )

    def test_wr01_total_label_with_voucher_is_transaction_row(self):
        """A party string alone is never summary authority: a row labelled
        'Total' carrying voucher identity is processed as a transaction row."""
        total, overdue, ratio, lims = parse_ar_data(
            [{"party": "Total", "voucher_no": "SINV-0077", "outstanding": 42}]
        )
        self.assertEqual(total, Decimal("42.00"))

    def test_wr01_summary_dict_top_level_metric_unavailable_not_zero(self):
        """Top-level AI001 must not report a zero metric when the source is a
        fake summary — the whole source becomes typed UNAVAILABLE."""
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources={
                "profit_and_loss": GOLD_PNL,
                "trial_balance": GOLD_TB,
                "accounts_receivable": {
                    "status": "success",
                    "data": [{"is_total_row": True, "outstanding": 123}],
                },
                "accounts_payable": {
                    "status": "success",
                    "data": [{"party": "Total", "outstanding": 123}],
                },
            },
        )
        self.assertNotEqual(snapshot["status"], "OK")
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ar_outstanding"]["value"])
        self.assertEqual(metrics["ap_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ap_outstanding"]["value"])
        self.assertIn("accounts_receivable", snapshot["missing_inputs"])
        self.assertIn("accounts_payable", snapshot["missing_inputs"])

    # --- WR-02: voucher-less rows ---

    def test_wr02_repro_voucherless_positive_row_raises(self):
        """Minimal recheck repro: a positive row without voucher_no/name must
        never be summed into the AI001 metric."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([{"outstanding": 123}])
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([{"outstanding": 123}])

    def test_wr02_voucherless_negative_row_raises(self):
        """Voucher-less rows are invalid regardless of amount sign: a negative
        unattributable row must not silently shift the total."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([{"outstanding": -50}])
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([{"outstanding": -50}])

    def test_wr02_voucherless_zero_row_raises(self):
        """A voucher-less zero row is a fake summary claiming zero — it must
        not become an AVAILABLE verified zero."""
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([{"outstanding": 0}])

    def test_wr02_name_alias_counts_as_voucher_identity(self):
        """`name` is the accepted identity alias; without an active DB the
        voucher is present-but-unverified (trusted raw_sources path)."""
        total, overdue, ratio, lims = parse_ar_data([{"name": "SINV-0042", "outstanding": 123}])
        self.assertEqual(total, Decimal("123.00"))

    def test_wr02_voucherless_row_top_level_metric_unavailable_not_zero(self):
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources={
                "profit_and_loss": GOLD_PNL,
                "trial_balance": GOLD_TB,
                "accounts_receivable": {"status": "success", "data": [{"outstanding": 123}]},
                "accounts_payable": {"status": "success", "data": [{"outstanding": 123}]},
            },
        )
        self.assertNotEqual(snapshot["status"], "OK")
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ar_outstanding"]["value"])
        self.assertEqual(metrics["ap_outstanding"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["ap_outstanding"]["value"])
        self.assertTrue(any("AR source data invalid" in lim for lim in snapshot["limitations"]))
        self.assertTrue(any("AP source data invalid" in lim for lim in snapshot["limitations"]))

    def test_wr02_ai002_mixed_valid_and_voucherless_rows_fail_closed(self):
        """AI002 already rejects positive obligations without a voucher; one
        voucher-less row must invalidate the whole obligation read so no
        partial/fake-empty obligation set is returned."""
        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {
                    "status": "success",
                    "data": [
                        {"party": "Cust A", "voucher_no": "SINV-001", "outstanding": 100},
                        {"party": "Cust B", "outstanding": 200},
                    ],
                },
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )

    def test_wr01_ai002_all_summary_payload_raises_not_empty_obligations(self):
        """AI002 top-level adapter path: an all-summary payload must raise, so
        the service fails closed instead of reporting zero obligations."""
        from lotus_fin.cashflow.adapters import _collect_obligations
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [{"is_total_row": True, "outstanding": 123}]},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )

    def test_wr02_ai001_ai002_voucherless_row_contract_consistent(self):
        """Both engines reject the same row shape with their typed errors."""
        from lotus_fin.cashflow.adapters import _collect_obligations
        row = {"party": "Cust A", "outstanding": 123}
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([row], as_of_date=date(2026, 9, 26))
        with self.assertRaises(ObligationSourceError):
            _collect_obligations(
                {"status": "success", "data": [dict(row)]},
                "AR",
                ("party",),
                "Sales Invoice",
                "VND",
                "Accounts Receivable",
            )


if __name__ == "__main__":
    unittest.main()


