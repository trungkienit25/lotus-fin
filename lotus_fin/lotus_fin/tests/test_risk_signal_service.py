"""S5 service pipeline + security matrix tests (hermetic, no Frappe import).

Covers the packet §18 security matrix cases implementable hermetically and the
gold first-failed-stage behaviors:
- A1 before A2 (unauth + malformed -> FORBIDDEN), generic denial envelope,
- A2 strict structure, A3 company-before-future (STAGE_C), A5 report allowlist,
- A6 currency gates (company + row), payload suppression on denied/error,
- A7 dedupe/conflict, A8 schedule preflight (multi-schedule, denial, non-PI,
  missing due date), zero denominator, STAGE_E history-before-policy,
- STAGE_F POLICY_PENDING with valid partials,
- AR/AP happy-path composition (boundaries already pinned in S3),
- explanation degradation only (banned term, ungrounded numbers, provider
  failure leave the deterministic result unchanged),
- evidence ref presence + cross-company denial.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.modules.f003_risk_signal import evidence as evidence_module  # noqa: E402
from lotus_fin.modules.f003_risk_signal import policy as policy_module  # noqa: E402
from lotus_fin.modules.f003_risk_signal.agent import explain_result, next_check_actions  # noqa: E402
from lotus_fin.modules.f003_risk_signal.contracts import (  # noqa: E402
    DataMode,
    Explanation,
    ExplanationStatus,
    ReasonCode,
    SignalId,
    Status,
    result_to_dict,
)
from lotus_fin.modules.f003_risk_signal.interfaces import (  # noqa: E402
    APReportSnapshot,
    APRow,
    ARSnapshot,
    ScheduleMetadata,
)
from lotus_fin.modules.f003_risk_signal.provenance import SourceFailure  # noqa: E402
from lotus_fin.modules.f003_risk_signal.service import ServiceDeps, evaluate_signal, get_evidence  # noqa: E402


class _HermeticEvidenceRedis:
    """Explicitly injected raw-boundary fake (make_key/setex/get/delete) so
    AP evidence records persist in this module without Frappe and without any
    process-local fallback (runtime has none since G4B remediation)."""

    def __init__(self):
        self.data = {}

    def make_key(self, key):
        return f"hermetic|{key}"

    def setex(self, name, time, value):
        self.data[name] = value

    def get(self, name):
        return self.data.get(name)

    def delete(self, name):
        self.data.pop(name, None)


def setUpModule():
    # Module-isolated hermetic store: never rely on suite-execution order or
    # on state leaked from the evidence test module.
    evidence_module._STORE = evidence_module.EvidenceStore(client=_HermeticEvidenceRedis())


APPLIED = {
    "company": "AI003 Gold 2026",
    "report_date": "2026-09-26",
    "based_on_payment_terms": 0,
    "in_party_currency": 0,
    "show_future_payments": 0,
    "ageing_based_on": "Due Date",
    "age_as_on": "Report Date",
}


def _ap_row(voucher, amount, due=None, account="Creditors - AI003 Gold 2026", voucher_type="Purchase Invoice"):
    return APRow(
        voucher_type=voucher_type,
        voucher_no=voucher,
        party_account=account,
        outstanding_amount=Decimal(amount),
        due_date_raw=due,
        due_date=due,
        currency="VND",
    )


class _FakeAP:
    def __init__(self, rows):
        self.rows = rows

    def fetch(self, company, as_of):
        return APReportSnapshot(
            status="success",
            report_key="accounts_payable",
            report_name="Accounts Payable",
            company=company,
            as_of=as_of,
            filters_applied=dict(APPLIED),
            rows=tuple(self.rows),
            source_hash="b" * 64,
        )


class _FakeAR:
    def __init__(self, current, baseline=None, baseline_failure=None):
        self.current = current
        self.baseline = baseline
        self.baseline_failure = baseline_failure

    def fetch(self, company, cutoff):
        if cutoff == self.current.as_of:
            return self.current
        if self.baseline_failure is not None:
            raise self.baseline_failure
        return self.baseline


def _ar_snap(total, ratio, cutoff):
    return ARSnapshot(
        status="OK",
        contract_version="1.0.0",
        formula_version="2026.1",
        company="AI003 Gold 2026",
        currency="VND",
        as_of=cutoff,
        total_ar=Decimal(total),
        overdue_ratio=Decimal(ratio),
        ar_metrics_available=True,
        snapshot_id="SNAP-1",
        source_hash="a" * 64,
    )


def _schedule_meta(voucher, count=1, header=None, children=None):
    return ScheduleMetadata(
        voucher_type="Purchase Invoice",
        voucher_no=voucher,
        company="AI003 Gold 2026",
        docstatus=1,
        schedule_count=count,
        header_due_date=header,
        child_due_dates=tuple(children or ([header] if header else [])),
    )


class _FakeSchedule:
    def __init__(self, mapping, fail=None):
        self.mapping = mapping
        self.fail = fail

    def get(self, voucher_no, expected_company):
        if self.fail is not None:
            raise self.fail
        return self.mapping[voucher_no]


def _deps(
    company_ok=True,
    currency="VND",
    today=date(2026, 10, 2),
    ar=None,
    ap=None,
    schedule=None,
    permission=True,
    data_mode=DataMode.CONTROLLED_FIXTURE,
):
    def verify(company):
        if not company_ok or company == "Other Company":
            raise RuntimeError("denied")
        return company

    return ServiceDeps(
        company_verifier=verify,
        currency_provider=lambda c: currency,
        today_provider=lambda: today,
        ar_provider=ar,
        ap_provider=ap,
        schedule_provider=schedule,
        data_mode=data_mode,
        report_permission=lambda report: permission,
    )


def _ar_payload(**overrides):
    payload = {
        "company": "AI003 Gold 2026",
        "signal_id": "AR_OVERDUE_SPIKE",
        "as_of_date": "2026-09-26",
    }
    payload.update(overrides)
    return payload


def _ap_payload(**overrides):
    payload = {
        "company": "AI003 Gold 2026",
        "signal_id": "AP_DUE_CLUSTER",
        "as_of_date": "2026-09-26",
    }
    payload.update(overrides)
    return payload


USER = "finance.user@example.com"


class StageA_Authentication(unittest.TestCase):
    def test_unauthenticated_forbidden_before_structure(self):
        result = evaluate_signal(_ar_payload(signal_id="NOT_A_SIGNAL"), checked_user=None, deps=_deps())
        self.assertEqual(result.status, Status.FORBIDDEN)
        self.assertEqual(result.reason_code, ReasonCode.UNAUTHORIZED_ACCESS)
        self.assertEqual(result.stage_trace, ("A1_AUTH",))

    def test_guest_denied(self):
        result = evaluate_signal(_ar_payload(), checked_user="Guest", deps=_deps())
        self.assertEqual(result.status, Status.FORBIDDEN)

    def test_denial_envelope_has_no_financial_payload(self):
        wire = result_to_dict(
            evaluate_signal(_ar_payload(), checked_user=None, deps=_deps())
        )
        for banned in ("company", "observed", "delta_pp", "baseline", "rule", "evidence", "coverage"):
            self.assertNotIn(banned, wire)
        self.assertEqual(wire["reason_code"], "UNAUTHORIZED_ACCESS")


class StageB_Structure(unittest.TestCase):
    def test_unknown_key_rejected(self):
        result = evaluate_signal(_ar_payload(threshold=99), checked_user=USER, deps=_deps())
        self.assertEqual(result.status, Status.VALIDATION_ERROR)
        self.assertEqual(result.reason_code, ReasonCode.INVALID_REQUEST)
        self.assertEqual(result.stage_trace, ("A1_AUTH", "A2_STRUCTURE"))

    def test_loose_date_rejected(self):
        result = evaluate_signal(_ar_payload(as_of_date="2026-9-26"), checked_user=USER, deps=_deps())
        self.assertEqual(result.status, Status.VALIDATION_ERROR)


class StageC_Company(unittest.TestCase):
    def test_company_denied_generic(self):
        result = evaluate_signal(_ar_payload(company="Other Company"), checked_user=USER, deps=_deps())
        self.assertEqual(result.status, Status.FORBIDDEN)
        self.assertEqual(result.reason_code, ReasonCode.ACCESS_DENIED)

    def test_company_before_future_date(self):
        # STAGE_C gold: denied company + future date -> FORBIDDEN (company first).
        result = evaluate_signal(
            _ar_payload(company="Other Company", as_of_date="2030-01-01"),
            checked_user=USER,
            deps=_deps(),
        )
        self.assertEqual(result.status, Status.FORBIDDEN)

    def test_future_date_after_company(self):
        result = evaluate_signal(_ar_payload(as_of_date="2030-01-01"), checked_user=USER, deps=_deps())
        self.assertEqual(result.status, Status.VALIDATION_ERROR)
        self.assertEqual(result.reason_code, ReasonCode.FUTURE_AS_OF)


class StageA5_ReportPermission(unittest.TestCase):
    def test_report_denied_forbidden(self):
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(permission=False))
        self.assertEqual(result.status, Status.FORBIDDEN)
        self.assertEqual(result.stage_trace[-1], "A5_SOURCE_AUTH")


class StageA6_CurrencyAndSource(unittest.TestCase):
    def test_company_currency_gate(self):
        ar = _FakeAR(_ar_snap("565000", "0.1150", date(2026, 9, 26)),
                     _ar_snap("650000", "0.0000", date(2026, 8, 26)))
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(currency="EUR", ar=ar))
        self.assertEqual(result.status, Status.VALIDATION_ERROR)
        self.assertEqual(result.reason_code, ReasonCode.UNSUPPORTED_COMPANY_CURRENCY)


    def test_source_error_before_policy(self):
        ar = _FakeAR(
            _ar_snap("565000", "0.1150", date(2026, 9, 26)),
            baseline_failure=SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, "down"),
        )
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(ar=ar))
        self.assertEqual(result.status, Status.SOURCE_ERROR)


class ARPipeline(unittest.TestCase):
    def _deps_ar(self, current_total, current_ratio, baseline_total="650000", baseline_ratio="0.0000",
                 baseline_failure=None):
        ar = _FakeAR(
            _ar_snap(current_total, current_ratio, date(2026, 9, 26)),
            None if baseline_failure else _ar_snap(baseline_total, baseline_ratio, date(2026, 8, 26)),
            baseline_failure=baseline_failure,
        )
        return _deps(ar=ar)

    # NOTE: include_explanation is a service kwarg, never a request-payload key.

    def test_watch(self):
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=self._deps_ar("565000", "0.1150"))
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.finding.value, "TRIGGERED")
        self.assertEqual(result.severity.value, "WATCH")
        self.assertTrue(result.triggered)
        self.assertEqual(result.delta_pp, Decimal("11.5000"))

    def test_benign_and_high(self):
        benign = evaluate_signal(_ar_payload(), checked_user=USER, deps=self._deps_ar("565000", "0.0499"))
        self.assertEqual(benign.finding.value, "BENIGN")
        self.assertIsNone(benign.severity)
        self.assertFalse(benign.triggered)
        high = evaluate_signal(_ar_payload(), checked_user=USER, deps=self._deps_ar("565000", "0.1501"))
        self.assertEqual(high.severity.value, "HIGH")

    def test_baseline_missing_history(self):
        result = evaluate_signal(
            _ar_payload(),
            checked_user=USER,
            deps=self._deps_ar("565000", "0.1150",
                               baseline_failure=SourceFailure(Status.INCONCLUSIVE, ReasonCode.SOURCE_UNAVAILABLE, "none")),
        )
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.HISTORY_INSUFFICIENT)

    def test_current_zero_denominator(self):
        ar = _FakeAR(_ar_snap("0", "0.0000", date(2026, 9, 26)),
                     _ar_snap("650000", "0.0000", date(2026, 8, 26)))
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(ar=ar))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.CURRENT_DENOMINATOR_INVALID)

    def test_ok_wire_shape(self):
        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=self._deps_ar("565000", "0.1150"))
        wire = result_to_dict(result)
        self.assertNotIn("company", wire)
        self.assertEqual(wire["delta_pp"], "11.50")
        self.assertEqual(wire["observed"]["value"], "0.1150")
        self.assertEqual(wire["observed"]["supporting_amount"], "565000.00")
        self.assertEqual(wire["baseline"]["cutoff"], "2026-08-26")
        self.assertEqual(wire["baseline"]["denominator"], "650000.00")
        self.assertEqual(wire["rule"]["threshold"], "5.00")  # pp at 2dp
        self.assertEqual(wire["rule"]["high_threshold"], "15.00")
        self.assertEqual(wire["rule"]["threshold_unit"], "percentage_points")
        self.assertEqual(wire["data_mode"], "CONTROLLED_FIXTURE")
        self.assertIn("A11_EXPLANATION", wire["stage_trace"])


class APPipeline(unittest.TestCase):
    def _gold_rows(self):
        """Gold AP_TRANSACTION_ORACLE shape: N=3/3? -> here a WATCH variant."""
        as_of = date(2026, 9, 26)
        return [
            _ap_row("PINV-D0", "300", as_of),
            _ap_row("PINV-D30", "300", date(2026, 10, 26)),
            _ap_row("PINV-D31", "300", date(2026, 10, 27)),
            _ap_row("PINV-LONG", "100", date(2026, 12, 31)),
        ]

    def _deps_ap(self, rows, schedule=None):
        schedule = schedule or _FakeSchedule({
            row.voucher_no: _schedule_meta(row.voucher_no, count=1, header=row.due_date)
            for row in rows
            if row.outstanding_amount > 0
        })
        return _deps(ap=_FakeAP(rows), schedule=schedule)

    def test_watch_with_counts_and_evidence(self):
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(self._gold_rows()))
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.finding.value, "TRIGGERED")
        self.assertEqual(result.severity.value, "WATCH")
        self.assertEqual(result.observed.value, Decimal("0.6"))
        self.assertEqual(result.observed.supporting_amount, Decimal("600"))
        self.assertEqual(result.count_positive_vouchers, 4)
        self.assertEqual(result.count_due_vouchers, 2)
        self.assertEqual(result.rule.window_start, date(2026, 9, 26))
        self.assertEqual(result.rule.window_end, date(2026, 10, 26))
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.evidence[0].kind, "REPORT_SNAPSHOT")

    def test_multi_schedule_inconclusive(self):
        rows = [_ap_row("PINV-MULTI", "300", date(2026, 10, 1))]
        schedule = _FakeSchedule({"PINV-MULTI": _schedule_meta("PINV-MULTI", count=2, header=date(2026, 10, 1),
                                                               children=[date(2026, 10, 1), date(2026, 11, 1)])})
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows, schedule))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.UNSUPPORTED_MULTI_SCHEDULE)
        self.assertIsNone(result.finding)
        self.assertIsNone(result.triggered)

    def test_metadata_denial_forbidden(self):
        rows = [_ap_row("PINV-D0", "300", date(2026, 9, 26))]
        schedule = _FakeSchedule({}, fail=SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "denied"))
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows, schedule))
        self.assertEqual(result.status, Status.FORBIDDEN)
        wire = result_to_dict(result)
        self.assertNotIn("observed", wire)

    def test_non_purchase_invoice_scope(self):
        rows = [_ap_row("JV-001", "300", date(2026, 10, 1), voucher_type="Journal Entry")]
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.UNSUPPORTED_ALLOCATION_SCOPE)

    def test_missing_due_date_inconclusive(self):
        rows = [_ap_row("PINV-NODUE", "300", None)]
        schedule = _FakeSchedule({"PINV-NODUE": _schedule_meta("PINV-NODUE", count=0, header=None)})
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows, schedule))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.INCOMPLETE_DUE_DATE_COVERAGE)

    def test_single_schedule_null_child_is_coverage_gap_not_multi(self):
        # Audit P2 regression: a 1-schedule invoice with no usable child due date
        # must yield INCOMPLETE_DUE_DATE_COVERAGE, never UNSUPPORTED_MULTI_SCHEDULE.
        rows = [_ap_row("PINV-ONE", "300", date(2026, 10, 1))]
        schedule = _FakeSchedule({
            "PINV-ONE": ScheduleMetadata(
                voucher_type="Purchase Invoice",
                voucher_no="PINV-ONE",
                company="AI003 Gold 2026",
                docstatus=1,
                schedule_count=1,
                header_due_date=None,
                child_due_dates=(None,),
            )
        })
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows, schedule))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.INCOMPLETE_DUE_DATE_COVERAGE)

    def test_duplicate_no_double_count(self):
        as_of = date(2026, 9, 26)
        rows = [
            _ap_row("PINV-A", "300", as_of),
            _ap_row("PINV-A", "300", as_of),  # exact duplicate
            _ap_row("PINV-B", "700", date(2026, 12, 31)),
        ]
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows))
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.observed.supporting_amount, Decimal("300"))  # numerator only PINV-A once
        self.assertEqual(result.count_positive_vouchers, 2)
        self.assertEqual(result.count_due_vouchers, 1)

    def test_conflict_source_error_payload_suppressed(self):
        as_of = date(2026, 9, 26)
        rows = [_ap_row("PINV-A", "300", as_of), _ap_row("PINV-A", "400", as_of)]
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows))
        self.assertEqual(result.status, Status.SOURCE_ERROR)
        self.assertEqual(result.reason_code, ReasonCode.CONFLICTING_OBSERVATION)
        wire = result_to_dict(result)
        self.assertIsNone(wire["observed"])
        self.assertEqual(wire["evidence"], [])

    def test_zero_denominator(self):
        as_of = date(2026, 9, 26)
        rows = [_ap_row("PINV-PAST", "300", date(2026, 9, 1)), _ap_row("PINV-CR", "-50", as_of)]
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(rows))
        self.assertEqual(result.status, Status.INCONCLUSIVE)
        self.assertEqual(result.reason_code, ReasonCode.ZERO_DENOMINATOR)

    def test_policy_pending_with_valid_partials(self):
        pending = policy_module.SignalPolicy(
            policy_version="AI003_TEST_PENDING",
            signal_id=SignalId.AP_DUE_CLUSTER,
            approval_status=policy_module.APPROVAL_PENDING,
            policy_scope="DEMO_ONLY",
            data_mode_scope="ALL",
            approver="Nobody",
            approved_date=date(2026, 10, 2),
            validation_evidence="none",
            floor=Decimal("0"),
            watch_threshold=Decimal("0.50"),
            high_threshold=Decimal("0.75"),
            threshold_unit=policy_module.ThresholdUnit.RATIO,
            precision="0.0001",
            baseline_spec=None,
            window_days=30,
        )
        original_registry = dict(policy_module._REGISTRY)
        original_active = dict(policy_module._ACTIVE_VERSIONS)
        try:
            policy_module._REGISTRY[(SignalId.AP_DUE_CLUSTER, "AI003_TEST_PENDING")] = pending
            policy_module._ACTIVE_VERSIONS[SignalId.AP_DUE_CLUSTER] = "AI003_TEST_PENDING"
            result = evaluate_signal(_ap_payload(), checked_user=USER, deps=self._deps_ap(self._gold_rows()))
            self.assertEqual(result.status, Status.POLICY_PENDING)
            self.assertEqual(result.reason_code, ReasonCode.POLICY_NOT_APPROVED)
            self.assertIsNone(result.finding)
            self.assertIsNotNone(result.observed.supporting_amount)
        finally:
            policy_module._REGISTRY.clear()
            policy_module._REGISTRY.update(original_registry)
            policy_module._ACTIVE_VERSIONS.clear()
            policy_module._ACTIVE_VERSIONS.update(original_active)


class ExplanationDegradation(unittest.TestCase):
    def _ar_result(self, explain=explain_result):
        ar = _FakeAR(_ar_snap("565000", "0.1150", date(2026, 9, 26)),
                     _ar_snap("650000", "0.0000", date(2026, 8, 26)))
        return evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(ar=ar),
                               include_explanation=True, explain=explain)

    def test_mock_explanation_available_and_grounded(self):
        result = self._ar_result()
        self.assertEqual(result.explanation.status, ExplanationStatus.AVAILABLE)
        self.assertIn("11.50", result.explanation.text)
        # deterministic fields intact
        self.assertEqual(result.delta_pp, Decimal("11.5000"))
        self.assertEqual(result.severity.value, "WATCH")

    def test_banned_term_degrades_only_explanation(self):
        def explain(result):
            return Explanation(status=ExplanationStatus.AVAILABLE, text="This indicates fraud risk.")

        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(
            ar=_FakeAR(_ar_snap("565000", "0.1150", date(2026, 9, 26)),
                       _ar_snap("650000", "0.0000", date(2026, 8, 26)))),
            include_explanation=True, explain=explain)
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.explanation.status, ExplanationStatus.UNAVAILABLE)

    def test_ungrounded_number_rejected(self):
        def explain(result):
            return Explanation(status=ExplanationStatus.AVAILABLE, text="Exposure is 999999 VND.")

        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(
            ar=_FakeAR(_ar_snap("565000", "0.1150", date(2026, 9, 26)),
                       _ar_snap("650000", "0.0000", date(2026, 8, 26)))),
            include_explanation=True, explain=explain)
        self.assertEqual(result.explanation.status, ExplanationStatus.UNAVAILABLE)
        self.assertEqual(result.explanation.reason_code, "GROUNDING_FAILED")

    def test_provider_failure_keeps_result(self):
        def explain(result):
            raise RuntimeError("llm down")

        result = evaluate_signal(_ar_payload(), checked_user=USER, deps=_deps(
            ar=_FakeAR(_ar_snap("565000", "0.1150", date(2026, 9, 26)),
                       _ar_snap("650000", "0.0000", date(2026, 8, 26)))),
            include_explanation=True, explain=explain)
        self.assertEqual(result.status, Status.OK)
        self.assertEqual(result.explanation.status, ExplanationStatus.UNAVAILABLE)
        self.assertEqual(result.explanation.reason_code, "PROVIDER_FAILURE")

    def test_next_check_actions_allowlisted(self):
        actions = next_check_actions("AR_OVERDUE_SPIKE", "OK")
        self.assertEqual(len(actions), 3)
        self.assertTrue(all("fraud" not in a.lower() for a in actions))
        self.assertEqual(next_check_actions("AP_DUE_CLUSTER", "FORBIDDEN"),
                         ["Contact an administrator to verify your company access"])


class EvidenceAuthorization(unittest.TestCase):
    def test_evidence_replay_match_and_cross_company(self):
        as_of = date(2026, 9, 26)
        rows = [_ap_row("PINV-D0", "300", as_of)]
        schedule = _FakeSchedule({"PINV-D0": _schedule_meta("PINV-D0", count=1, header=as_of)})
        deps = _deps(ap=_FakeAP(rows), schedule=schedule)
        result = evaluate_signal(_ap_payload(), checked_user=USER, deps=deps)
        self.assertEqual(len(result.evidence), 1)
        ref = result.evidence[0].ref

        def factory(record):
            def replay():
                snapshot = deps.ap_provider.fetch("AI003 Gold 2026", record.as_of_date)
                return {"report_key": snapshot.report_key, "source_hash": snapshot.source_hash}
            return replay

        matched = get_evidence(ref, checked_user=USER, verified_company="AI003 Gold 2026",
                               replay_factory=factory)
        self.assertEqual(matched.outcome, "MATCH")
        denied = get_evidence(ref, checked_user=USER, verified_company="Other Company",
                              replay_factory=factory)
        self.assertEqual(denied.outcome, "FORBIDDEN")
        unauth = get_evidence(ref, checked_user=None, verified_company="AI003 Gold 2026",
                              replay_factory=factory)
        self.assertEqual(unauth.outcome, "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
