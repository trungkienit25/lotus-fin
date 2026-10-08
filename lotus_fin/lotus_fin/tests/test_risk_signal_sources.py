"""S2 source/coverage/provenance tests for AI003 (hermetic, no Frappe import).

Pins the S2 acceptance surface against the METHOD GOLD semantics:
- AR baseline resolver (prev-month same-day, month-end clamp, leap/January),
- AR pair role failures (HISTORY_INSUFFICIENT vs BASELINE/CURRENT_DENOMINATOR_
  INVALID vs genuine SOURCE_ERROR), version pins, currency gate,
- AP pinned filter recipe (exact §16.5 dict), row normalization (missing vs
  malformed due date), envelope/filter drift fail-closed,
- V2.2 identity: exact-duplicate dedupe, CONFLICTING_OBSERVATION,
  UNSUPPORTED_ALLOCATION_SCOPE, currency gate before identity,
- window classification D0/D30/D31/long/past/credit.
"""

import os
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.modules.f003_risk_signal import sources  # noqa: E402
from lotus_fin.modules.f003_risk_signal.contracts import ReasonCode, Status  # noqa: E402
from lotus_fin.modules.f003_risk_signal.coverage import (  # noqa: E402
    DueDateCoverage,
    ap_window,
    classify_due,
    previous_month_same_day,
    select_ap_observations,
    sum_amounts,
)
from lotus_fin.modules.f003_risk_signal.interfaces import APRow  # noqa: E402
from lotus_fin.modules.f003_risk_signal.provenance import (  # noqa: E402
    SourceFailure,
    distinct_voucher_count,
    gate_company_currency,
    parse_amount,
    reconcile_observations,
)


def _ai001_envelope(
    company="AI003 Gold 2026",
    cutoff="2026-09-26",
    status="OK",
    total=650000.0,
    ratio=0.1150,
    total_status="AVAILABLE",
    ratio_status="AVAILABLE",
    contract_version="1.0.0",
    formula_version="2026.1",
    currency="VND",
):
    return {
        "status": status,
        "contract_version": contract_version,
        "company": company,
        "currency": currency,
        "as_of": cutoff,
        "metrics": [
            {
                "metric_id": "ar_outstanding",
                "status": total_status,
                "value": total,
                "formula_version": formula_version,
            },
            {
                "metric_id": "overdue_ar_ratio",
                "status": ratio_status,
                "value": ratio,
                "formula_version": formula_version,
            },
        ],
    }


class _FakeARProvider:
    def __init__(self, envelopes):
        self.envelopes = envelopes  # callable(company, cutoff) -> mapping

    def fetch(self, company, cutoff):
        return sources._parse_ai001_envelope(self.envelopes(company, cutoff), cutoff)


class ARBaselineResolver(unittest.TestCase):
    def test_same_day(self):
        self.assertEqual(previous_month_same_day(date(2026, 9, 26)), date(2026, 8, 26))

    def test_month_end_clamp_non_leap(self):
        self.assertEqual(previous_month_same_day(date(2026, 3, 31)), date(2026, 2, 28))

    def test_month_end_clamp_leap(self):
        self.assertEqual(previous_month_same_day(date(2024, 3, 31)), date(2024, 2, 29))

    def test_january_to_previous_december(self):
        self.assertEqual(previous_month_same_day(date(2026, 1, 15)), date(2025, 12, 15))
        self.assertEqual(previous_month_same_day(date(2026, 1, 31)), date(2025, 12, 31))

    def test_thirty_first_to_thirty(self):
        self.assertEqual(previous_month_same_day(date(2026, 7, 30)), date(2026, 6, 30))


class ARPairSemantics(unittest.TestCase):
    def test_happy_pair(self):
        provider = _FakeARProvider(
            lambda company, cutoff: _ai001_envelope(company=company, cutoff=cutoff.isoformat(), total=565000.0, ratio=0.1150)
        )
        current, baseline = sources.fetch_ar_pair(
            provider, "AI003 Gold 2026", date(2026, 9, 26), date(2026, 8, 26)
        )
        self.assertEqual(current.total_ar, Decimal("565000.0"))
        self.assertEqual(baseline.overdue_ratio, Decimal("0.1150"))

    def test_version_pins(self):
        provider = _FakeARProvider(
            lambda company, cutoff: _ai001_envelope(company=company, contract_version="9.9.9")
        )
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(ctx.exception.reason_code, ReasonCode.UNSUPPORTED_SOURCE_VERSION)

    def test_formula_pin(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company, formula_version="1999.9"))
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(ctx.exception.reason_code, ReasonCode.UNSUPPORTED_SOURCE_VERSION)

    def test_currency_gate(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company, currency="USD"))
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(ctx.exception.status, Status.VALIDATION_ERROR)
        self.assertEqual(ctx.exception.reason_code, ReasonCode.UNSUPPORTED_COMPANY_CURRENCY)

    def test_forbidden_propagates(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company, status="FORBIDDEN"))
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(ctx.exception.status, Status.FORBIDDEN)

    def test_current_zero_denominator(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company, total=0))
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26), date(2026, 8, 26))
        self.assertEqual(ctx.exception.reason_code, ReasonCode.CURRENT_DENOMINATOR_INVALID)

    def test_baseline_zero_denominator(self):
        provider = _FakeARProvider(
            lambda company, cutoff: _ai001_envelope(
                company=company, cutoff=cutoff.isoformat(), total=0 if cutoff == date(2026, 8, 26) else 650000.0
            )
        )
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26), date(2026, 8, 26))
        self.assertEqual(ctx.exception.reason_code, ReasonCode.BASELINE_DENOMINATOR_INVALID)

    def test_baseline_unavailable_is_history_insufficient(self):
        provider = _FakeARProvider(
            lambda company, cutoff: _ai001_envelope(
                company=company,
                cutoff=cutoff.isoformat(),
                status="INSUFFICIENT_DATA" if cutoff == date(2026, 8, 26) else "OK",
            )
        )
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26), date(2026, 8, 26))
        self.assertEqual(ctx.exception.status, Status.INCONCLUSIVE)
        self.assertEqual(ctx.exception.reason_code, ReasonCode.HISTORY_INSUFFICIENT)

    def test_baseline_source_error_stays_source_error(self):
        def envelopes(company, cutoff):
            if cutoff == date(2026, 8, 26):
                return _ai001_envelope(cutoff=cutoff.isoformat(), status="SOURCE_ERROR")
            return _ai001_envelope(cutoff=cutoff.isoformat())

        provider = _FakeARProvider(envelopes)
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26), date(2026, 8, 26))
        self.assertEqual(ctx.exception.status, Status.SOURCE_ERROR)

    def test_partial_envelope_with_ar_available_accepted(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company, status="PARTIAL"))
        current, _ = sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertTrue(current.ar_metrics_available)

    def test_partial_envelope_without_ar_metrics_rejected(self):
        provider = _FakeARProvider(
            lambda company, cutoff: _ai001_envelope(
                company=company, total_status="UNAVAILABLE", ratio_status="UNAVAILABLE"
            )
        )
        with self.assertRaises(SourceFailure) as ctx:
            sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(ctx.exception.reason_code, ReasonCode.SOURCE_UNAVAILABLE)

    def test_source_hash_present(self):
        provider = _FakeARProvider(lambda company, cutoff: _ai001_envelope(company=company))
        current, _ = sources.fetch_ar_pair(provider, "C", date(2026, 9, 26))
        self.assertEqual(len(current.source_hash), 64)



FULL_APPLIED = {
    "company": "C",
    "report_date": "2026-09-26",
    "based_on_payment_terms": 0,
    "in_party_currency": 0,
    "show_future_payments": 0,
    "ageing_based_on": "Due Date",
    "age_as_on": "Report Date",
}

class APPinnedRecipe(unittest.TestCase):
    def test_exact_filter_dict_sent_to_boundary(self):
        captured = {}

        def fake_boundary(report_key, filters, company):
            captured.update({"report_key": report_key, "filters": dict(filters), "company": company})
            return {
                "status": "success",
                "report_key": "accounts_payable",
                "report_name": "Accounts Payable",
                "company": company,
                "filters_applied": {**filters, "company": company},
                "data": [],
            }

        original = sources._ap_report_callable
        sources._ap_report_callable = lambda: fake_boundary
        try:
            sources.APReportAdapter().fetch("AI003 Gold 2026", date(2026, 9, 26))
        finally:
            sources._ap_report_callable = original
        self.assertEqual(captured["report_key"], "accounts_payable")
        self.assertEqual(captured["company"], "AI003 Gold 2026")
        self.assertEqual(
            captured["filters"],
            {
                "report_date": "2026-09-26",
                "based_on_payment_terms": 0,
                "in_party_currency": 0,
                "show_future_payments": 0,
                "ageing_based_on": "Due Date",
                "age_as_on": "Report Date",
            },
        )

    def _adapter_with(self, envelope):
        original = sources._ap_report_callable
        sources._ap_report_callable = lambda: lambda report_key, filters, company: envelope
        try:
            return sources.APReportAdapter().fetch("C", date(2026, 9, 26))
        finally:
            sources._ap_report_callable = original

    def test_row_normalization(self):
        snapshot = self._adapter_with(
            {
                "status": "success",
                "report_name": "Accounts Payable",
                "company": "C",
                "filters_applied": {
                    "company": "C",
                    "report_date": "2026-09-26",
                    "based_on_payment_terms": 0,
                    "in_party_currency": 0,
                    "show_future_payments": 0,
                    "ageing_based_on": "Due Date",
                    "age_as_on": "Report Date",
                },
                "data": [
                    {
                        "voucher_type": "Purchase Invoice",
                        "voucher_no": "ACC-PINV-0001",
                        "party_account": "Creditors - C",
                        "outstanding": "500000.00",
                        "due_date": "2026-10-01",
                        "party": "Vendor A",
                    },
                    {
                        "voucher_type": "Purchase Invoice",
                        "voucher_no": "ACC-PINV-0002",
                        "party_account": "Creditors - C",
                        "outstanding": 250.5,
                        "due_date": None,
                    },
                ],
            }
        )
        self.assertEqual(len(snapshot.rows), 2)
        self.assertEqual(snapshot.rows[0].outstanding_amount, Decimal("500000.00"))
        self.assertEqual(snapshot.rows[0].due_date, date(2026, 10, 1))
        self.assertIsNone(snapshot.rows[1].due_date)  # missing -> coverage decision

    def test_malformed_due_date_is_source_error(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._adapter_with(
                {
                    "status": "success",
                    "report_name": "Accounts Payable",
                    "company": "C",
                    "filters_applied": dict(FULL_APPLIED),
                    "data": [
                        {
                            "voucher_type": "Purchase Invoice",
                            "voucher_no": "P1",
                            "party_account": "A",
                            "outstanding": "10",
                            "due_date": "soon",
                        }
                    ],
                }
            )
        self.assertEqual(ctx.exception.reason_code, ReasonCode.SOURCE_INVALID)

    def test_missing_voucher_identity_is_source_error(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._adapter_with(
                {
                    "status": "success",
                    "report_name": "Accounts Payable",
                    "company": "C",
                    "filters_applied": dict(FULL_APPLIED),
                    "data": [{"voucher_type": "Purchase Invoice", "outstanding": "10"}],
                }
            )
        self.assertEqual(ctx.exception.reason_code, ReasonCode.SOURCE_INVALID)

    def test_filter_drift_fail_closed(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._adapter_with(
                {
                    "status": "success",
                    "report_name": "Accounts Payable",
                    "company": "C",
                    "filters_applied": {
                        "company": "C",
                        "report_date": "2026-09-26",
                        "ageing_based_on": "Posting Date",
                    },
                    "data": [],
                }
            )
        self.assertEqual(ctx.exception.reason_code, ReasonCode.INCONSISTENT_DATA)

    def test_unexpected_report_identity_rejected(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._adapter_with(
                {
                    "status": "success",
                    "report_name": "Accounts Receivable",
                    "company": "C",
                    "filters_applied": {"company": "C"},
                    "data": [],
                }
            )
        self.assertEqual(ctx.exception.reason_code, ReasonCode.UNSUPPORTED_SOURCE_VERSION)

    def test_non_success_status(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._adapter_with({"status": "error", "report_name": "Accounts Payable"})
        self.assertEqual(ctx.exception.status, Status.SOURCE_ERROR)


class V2_2Identity(unittest.TestCase):
    def _row(self, voucher, account="Creditors - C", amount="100", due=None, currency="VND"):
        return APRow(
            voucher_type="Purchase Invoice",
            voucher_no=voucher,
            party_account=account,
            outstanding_amount=Decimal(amount),
            due_date_raw=due,
            due_date=due,
            currency=currency,
        )

    def test_exact_duplicate_deduped(self):
        rows = [self._row("P1"), self._row("P1")]
        reconciled = reconcile_observations(rows, "C")
        self.assertEqual(len(reconciled), 1)
        self.assertEqual(reconciled[0].duplicate_count, 2)

    def test_amount_conflict(self):
        rows = [self._row("P1", amount="100"), self._row("P1", amount="200")]
        with self.assertRaises(SourceFailure) as ctx:
            reconcile_observations(rows, "C")
        self.assertEqual(ctx.exception.reason_code, ReasonCode.CONFLICTING_OBSERVATION)

    def test_due_conflict(self):
        rows = [
            self._row("P1", due=date(2026, 10, 1)),
            self._row("P1", due=date(2026, 10, 2)),
        ]
        with self.assertRaises(SourceFailure) as ctx:
            reconcile_observations(rows, "C")
        self.assertEqual(ctx.exception.reason_code, ReasonCode.CONFLICTING_OBSERVATION)

    def test_unproved_multi_account_scope(self):
        rows = [self._row("P1", account="Creditors - A"), self._row("P1", account="Creditors - B")]
        with self.assertRaises(SourceFailure) as ctx:
            reconcile_observations(rows, "C")
        self.assertEqual(ctx.exception.status, Status.INCONCLUSIVE)
        self.assertEqual(ctx.exception.reason_code, ReasonCode.UNSUPPORTED_ALLOCATION_SCOPE)

    def test_proved_multi_account_scope_passes(self):
        rows = [self._row("P1", account="Creditors - A"), self._row("P1", account="Creditors - B")]
        reconciled = reconcile_observations(rows, "C", allocation_provenance={("C", "Purchase Invoice", "P1"): True})
        self.assertEqual(len(reconciled), 2)
        self.assertEqual(distinct_voucher_count(reconciled), 1)  # count basis stays voucher

    def test_currency_gate_before_identity(self):
        # Gold: AP_CURRENCY_MISMATCH_BEFORE_IDENTITY — reconciliation never invoked.
        with self.assertRaises(SourceFailure) as ctx:
            gate_company_currency("USD")
        self.assertEqual(ctx.exception.status, Status.VALIDATION_ERROR)
        gate_company_currency("VND")  # passes

    def test_identity_never_from_amount_or_date(self):
        rows = [
            self._row("P1", amount="100", due=date(2026, 10, 1)),
            self._row("P2", amount="100", due=date(2026, 10, 1)),
        ]
        reconciled = reconcile_observations(rows, "C")
        self.assertEqual(len(reconciled), 2)  # distinct vouchers stay distinct


class WindowAndSelection(unittest.TestCase):
    def test_window_bounds(self):
        self.assertEqual(ap_window(date(2026, 9, 26)), (date(2026, 9, 26), date(2026, 10, 26)))

    def test_classification(self):
        as_of = date(2026, 9, 26)
        self.assertEqual(classify_due(date(2026, 9, 26), as_of), DueDateCoverage.IN_WINDOW)
        self.assertEqual(classify_due(date(2026, 10, 26), as_of), DueDateCoverage.IN_WINDOW)
        self.assertEqual(classify_due(date(2026, 10, 27), as_of), DueDateCoverage.FUTURE_BEYOND)
        self.assertEqual(classify_due(date(2026, 12, 31), as_of), DueDateCoverage.FUTURE_BEYOND)
        self.assertEqual(classify_due(date(2026, 9, 25), as_of), DueDateCoverage.PAST_DUE)

    def _reconciled(self, voucher, amount, due):
        row = APRow(
            voucher_type="Purchase Invoice",
            voucher_no=voucher,
            party_account="Creditors - C",
            outstanding_amount=Decimal(amount),
            due_date_raw=due,
            due_date=due,
            currency="VND",
        )
        return reconcile_observations([row], "C")[0]

    def test_selection_matches_gold_oracle_shape(self):
        as_of = date(2026, 9, 26)
        observations = [
            self._reconciled("D0", "100", date(2026, 9, 26)),
            self._reconciled("D30", "100", date(2026, 10, 26)),
            self._reconciled("D31", "100", date(2026, 10, 27)),
            self._reconciled("LONG", "700", date(2026, 12, 31)),
            self._reconciled("PAST", "50", date(2026, 9, 1)),
            self._reconciled("CREDIT", "-30", date(2026, 10, 1)),
        ]
        selection = select_ap_observations(observations, as_of)
        self.assertEqual(len(selection.numerator), 2)  # D0, D30
        self.assertEqual(len(selection.denominator), 4)  # + D31, LONG
        self.assertEqual(selection.numerator_voucher_count, 2)
        self.assertEqual(selection.denominator_voucher_count, 4)
        self.assertEqual(selection.excluded_past_due_count, 1)
        self.assertEqual(selection.excluded_credit_count, 1)
        self.assertEqual(sum_amounts(selection.numerator), Decimal("200"))
        self.assertEqual(sum_amounts(selection.denominator), Decimal("1000"))


class AmountParsing(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(parse_amount("500000.00", "r"), Decimal("500000.00"))
        self.assertEqual(parse_amount(250.5, "r"), Decimal("250.5"))

    def test_non_numeric_amount(self):
        with self.assertRaises(SourceFailure) as ctx:
            parse_amount("abc", "r")
        self.assertEqual(ctx.exception.reason_code, ReasonCode.SOURCE_INVALID)

    def test_datetime_due_date_normalized(self):
        row = sources._normalize_ap_row(
            {
                "voucher_type": "Purchase Invoice",
                "voucher_no": "P1",
                "party_account": "A",
                "outstanding": "10",
                "due_date": datetime(2026, 10, 1, 13, 30),
            },
            0,
        )
        self.assertEqual(row.due_date, date(2026, 10, 1))


if __name__ == "__main__":
    unittest.main()
