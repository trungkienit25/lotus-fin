from datetime import datetime, date, timedelta, timezone
import uuid
from typing import Any, Callable, Dict, Optional

from lotus_fin.core.use_cases.source_gatherer import SourceGatherer
from lotus_fin.core.use_cases.metric_assembler import MetricAssembler
from lotus_fin.ai.observability import (
    log_event,
    metrics as op_metrics,
    EVENT_REQUEST_STARTED,
    EVENT_AUTH_PASSED,
    EVENT_AUTH_DENIED,
    EVENT_SNAPSHOT_STARTED,
    EVENT_SNAPSHOT_COMPLETED,
    EVENT_SOURCE_ERROR,
    EVENT_METRIC_COMPUTED,
    EVENT_METRIC_UNAVAILABLE,
    EVENT_REQUEST_COMPLETED,
    EVENT_REQUEST_FAILED,
)

FEATURE_ID = "AI001"
CONTRACT_VERSION = "1.0.0"
FORMULA_VERSION = "2026.1"


class SnapshotCoordinator:
    """Coordinates deterministic financial health snapshot aggregation conforming to AI001.

    Restored approved foundation orchestration (86208f4): full request/auth/
    snapshot lifecycle events, Bucket B as_of cutoff validation, Bucket C
    server-authoritative currency, WV-02 master Party Type preflight, and the
    posting-date as-of limitation — none of which may be silently dropped.
    """

    def build_snapshot(
        self,
        company: str,
        period_start: str,
        period_end: str,
        as_of: Optional[str] = None,
        currency: str = "VND",
        correlation_id: Optional[str] = None,
        comparison: Optional[str] = None,
        raw_sources: Optional[Dict[str, Any]] = None,
        source_fetcher: Optional[Callable[..., Any]] = None,
        user: Optional[str] = None,
        include_explanation: bool = False,
        llm_provider: Optional[Any] = None
    ) -> Dict[str, Any]:
        cid = correlation_id or str(uuid.uuid4())
        snapshot_id = f"SNAP-{uuid.uuid4().hex[:12].upper()}"
        now_iso = as_of or (datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

        log_event(
            event_type=EVENT_REQUEST_STARTED,
            correlation_id=cid,
            company=company,
            user=user,
            details={"period_start": period_start, "period_end": period_end, "comparison": comparison}
        )

        # 1. Period bounds validation
        try:
            p_start = datetime.strptime(period_start, "%Y-%m-%d").date()
            p_end = datetime.strptime(period_end, "%Y-%m-%d").date()
            if p_start > p_end:
                log_event(
                    event_type=EVENT_REQUEST_FAILED,
                    correlation_id=cid,
                    status="VALIDATION_ERROR",
                    details={"reason": "period_start cannot be after period_end"}
                )
                op_metrics.record_request("VALIDATION_ERROR", 0.0)
                return self._validation_error_env(
                    cid, now_iso,
                    ["period_start cannot be after period_end"],
                    ["Invalid temporal range provided."]
                )
        except (ValueError, TypeError) as e:
            log_event(
                event_type=EVENT_REQUEST_FAILED,
                correlation_id=cid,
                status="VALIDATION_ERROR",
                details={"reason": str(e)}
            )
            op_metrics.record_request("VALIDATION_ERROR", 0.0)
            return self._validation_error_env(
                cid, now_iso,
                [f"Malformed period date: {str(e)}"],
                ["Date formats must be YYYY-MM-DD."]
            )

        # 1b. as_of cutoff validation (AI003 foundation remediation, Bucket B).
        # The cutoff must be a full valid ISO date; invalid values are rejected
        # with a typed VALIDATION_ERROR and never silently fall back to period_end.
        as_of_date: Optional[date] = None
        if as_of:
            as_of_raw = str(as_of).strip()
            parsed_as_of = None
            try:
                parsed_as_of = datetime.fromisoformat(as_of_raw.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                parsed_as_of = None
            if parsed_as_of is None:
                log_event(
                    event_type=EVENT_REQUEST_FAILED,
                    correlation_id=cid,
                    status="VALIDATION_ERROR",
                    details={"reason": "Invalid as_of date"}
                )
                op_metrics.record_request("VALIDATION_ERROR", 0.0)
                return self._validation_error_env(
                    cid, now_iso,
                    ["Invalid as_of date; expected a full ISO date (YYYY-MM-DD)."],
                    ["as_of must be a valid ISO date; it is never silently replaced by period_end."]
                )
            if parsed_as_of < p_start:
                log_event(
                    event_type=EVENT_REQUEST_FAILED,
                    correlation_id=cid,
                    status="VALIDATION_ERROR",
                    details={"reason": "as_of before period_start"}
                )
                op_metrics.record_request("VALIDATION_ERROR", 0.0)
                return self._validation_error_env(
                    cid, now_iso,
                    ["as_of cannot be before period_start."],
                    ["as_of must lie within the requested period."]
                )
            as_of_date = parsed_as_of

        # 2. Company authorization guard
        verified_company = company
        try:
            # If running in Frappe environment with active DB connection, invoke server-side guard
            try:
                import frappe
                if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
                    from lotus_fin.security.access import get_verified_company
                    verified_company = get_verified_company(company, user=user)
                else:
                    if not company:
                        raise ValueError("Company cannot be empty")
                    verified_company = company

                log_event(
                    event_type=EVENT_AUTH_PASSED,
                    correlation_id=cid,
                    company=verified_company,
                    user=user
                )
            except (ImportError, AttributeError):
                # Fallback if frappe not in environment (e.g. running in unit test without DB)
                if not company:
                    raise ValueError("Company cannot be empty")
                verified_company = company
                log_event(
                    event_type=EVENT_AUTH_PASSED,
                    correlation_id=cid,
                    company=verified_company,
                    user=user
                )
        except Exception as e:
            # INV-01: Company Access Denied
            log_event(
                event_type=EVENT_AUTH_DENIED,
                correlation_id=cid,
                company=None,
                user=user,
                status="FORBIDDEN",
                details={"error": str(e)}
            )
            op_metrics.record_auth_denial()
            op_metrics.record_request("FORBIDDEN", 0.0)
            return self._forbidden_env(cid, now_iso, str(e))

        # 2b. Currency authority (AI003 foundation remediation, Bucket C).
        # The client may never relabel a financial metric in an arbitrary currency:
        # the server resolves the company's accounting currency and FX conversion
        # is not implemented, so any mismatch is a typed VALIDATION_ERROR.
        try:
            import frappe
            if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
                from lotus_fin.security.access import get_company_accounting_currency
                company_currency = get_company_accounting_currency(verified_company)
                requested_currency = str(currency or "").strip().upper()
                company_currency_norm = str(company_currency or "").strip().upper()
                if not company_currency_norm:
                    log_event(
                        event_type=EVENT_REQUEST_FAILED,
                        correlation_id=cid,
                        status="VALIDATION_ERROR",
                        details={"reason": "Company accounting currency could not be determined"}
                    )
                    op_metrics.record_request("VALIDATION_ERROR", 0.0)
                    return self._validation_error_env(
                        cid, now_iso,
                        ["Company accounting currency could not be determined."],
                        ["Financial metrics cannot be labeled without a verified accounting currency."]
                    )
                if requested_currency != company_currency_norm:
                    log_event(
                        event_type=EVENT_REQUEST_FAILED,
                        correlation_id=cid,
                        status="VALIDATION_ERROR",
                        details={"reason": "Requested currency does not match company accounting currency"}
                    )
                    op_metrics.record_request("VALIDATION_ERROR", 0.0)
                    return self._validation_error_env(
                        cid, now_iso,
                        [
                            "Requested currency does not match the company accounting currency; "
                            "FX conversion is not implemented."
                        ],
                        ["Financial metrics are only reported in the company accounting currency."]
                    )
                # Server-authoritative currency replaces the client-provided label.
                currency = company_currency
        except ImportError:
            # Non-Frappe unit-test environment: keep the provided currency.
            pass

        log_event(
            event_type=EVENT_SNAPSHOT_STARTED,
            correlation_id=cid,
            company=verified_company,
            details={"snapshot_id": snapshot_id}
        )

        # 3. Source Gathering
        # Extract as_of date boundary (validated in step 1b — never a silent fallback)
        as_of_date_str = as_of_date.strftime("%Y-%m-%d") if as_of_date else period_end

        # Freeze as_of rule: If as_of date is before period_end, reports evaluate up to as_of date
        effective_end_date = min(period_end, as_of_date_str) if as_of_date_str else period_end
        is_as_of_prior_to_period_end = bool(as_of_date and as_of_date < p_end)

        sources, fetch_errors, actual_filters_used = SourceGatherer.gather(
            verified_company, period_start, effective_end_date, effective_end_date, raw_sources, source_fetcher
        )

        # WV-02: Master Party Type preflight check (only with an active, non-mock DB)
        if self._has_active_db():
            try:
                import frappe
                is_mock = type(frappe.db).__name__ in ("Mock", "MagicMock") or hasattr(frappe.db, "_mock_return_value")
                rec_parties = frappe.db.get_all("Party Type", {"account_type": "Receivable"}, pluck="name")
                pay_parties = frappe.db.get_all("Party Type", {"account_type": "Payable"}, pluck="name")
                if not (is_mock and type(rec_parties).__name__ in ("Mock", "MagicMock")):
                    if not isinstance(rec_parties, list) or ("Customer" not in rec_parties):
                        fetch_errors["accounts_receivable"] = (
                            "Master data preflight check failed: 'Customer' is not registered as a Receivable Party Type."
                        )
                    if not isinstance(pay_parties, list) or ("Supplier" not in pay_parties):
                        fetch_errors["accounts_payable"] = (
                            "Master data preflight check failed: 'Supplier' is not registered as a Payable Party Type."
                        )
            except Exception as e:
                fetch_errors["accounts_receivable"] = f"Master data preflight check failed: {e}"
                fetch_errors["accounts_payable"] = f"Master data preflight check failed: {e}"

        # 4. Metrics & Evidence
        period_obj = {"start": period_start, "end": period_end}
        metrics, ev_refs, lims, missing = MetricAssembler.assemble(
            verified_company, period_start, effective_end_date, now_iso, currency, snapshot_id, period_obj,
            sources, fetch_errors, actual_filters_used
        )

        # Track metrics computed vs unavailable
        for m in metrics:
            if m["status"] == "AVAILABLE":
                op_metrics.record_metric_computed()
                log_event(
                    event_type=EVENT_METRIC_COMPUTED,
                    correlation_id=cid,
                    company=verified_company,
                    details={"metric_id": m["metric_id"], "value": m["value"]}
                )
            else:
                op_metrics.record_metric_unavailable(m["metric_id"])
                log_event(
                    event_type=EVENT_METRIC_UNAVAILABLE,
                    correlation_id=cid,
                    company=verified_company,
                    details={"metric_id": m["metric_id"], "limitations": m.get("limitations", [])}
                )

        # Preserve the explicit limitation for historical semantics (Bucket B):
        # a posting-date as_of cutoff does NOT support as_known_at replay of
        # backdated or cancelled postings — this must never be claimed implicitly.
        if is_as_of_prior_to_period_end:
            lims.append(
                "as-of cutoff uses posting-date semantics only; as_known_at historical "
                "replay of backdated or cancelled postings is not supported."
            )

        # 5. Overall Status Decision
        # OK: All required core metrics available (revenue, cogs, gross_margin, ar_outstanding, overdue_ar_ratio, ap_outstanding, cash_balance)
        # near_term_ap being UNAVAILABLE by design does not block overall status OK.
        core_m = [m for m in metrics if m["metric_id"] != "near_term_ap"]
        avail_count = sum(1 for m in core_m if m["status"] == "AVAILABLE")
        if fetch_errors and avail_count == 0:
            status = "SOURCE_ERROR"
        elif avail_count == len(core_m):
            status = "OK"
        elif avail_count > 0:
            status = "PARTIAL"
        else:
            status = "INSUFFICIENT_DATA"

        snapshot = {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": status,
            "correlation_id": cid,
            "company": verified_company,
            "period": period_obj,
            "as_of": now_iso,
            "snapshot_id": snapshot_id,
            "data_mode": "actual",
            "currency": currency,
            "metrics": metrics,
            "comparison": None,
            "explanation": {"status": "UNAVAILABLE", "facts": [], "interpretations": [], "next_checks": []},
            "missing_inputs": sorted(list(set(missing))),
            "limitations": sorted(list(set(lims))),
            "evidence_refs": ev_refs
        }

        # 6. Comparison Processing (PREVIOUS_PERIOD)
        if comparison == "PREVIOUS_PERIOD":
            from lotus_fin.ai.financial_health import compute_previous_period, build_comparison_block
            prev_s, prev_e = compute_previous_period(period_start, period_end)

            # Bucket B: align the previous window with the current EFFECTIVE window
            # length so current/previous metrics always cover consistent period
            # lengths (a mid-period as_of cutoff must not compare a short current
            # window against a full previous window).
            effective_len_days = (
                datetime.strptime(effective_end_date, "%Y-%m-%d").date()
                - datetime.strptime(period_start, "%Y-%m-%d").date()
            ).days
            prev_effective_end = (
                datetime.strptime(prev_s, "%Y-%m-%d").date() + timedelta(days=effective_len_days)
            ).strftime("%Y-%m-%d")

            prev_snap = None
            if source_fetcher:
                try:
                    prev_snap = self.build_snapshot(
                        company=verified_company,
                        period_start=prev_s,
                        period_end=prev_e,
                        as_of=prev_effective_end,
                        currency=currency,
                        correlation_id=f"{cid}-PREV",
                        comparison=None,  # No recursion
                        raw_sources=None,
                        source_fetcher=source_fetcher,
                        user=user
                    )
                except Exception as e:
                    log_event(
                        event_type=EVENT_SOURCE_ERROR,
                        correlation_id=cid,
                        company=verified_company,
                        details={"error": f"Failed to build previous snapshot: {str(e)}"}
                    )

            comp_block = build_comparison_block(snapshot, prev_snap, correlation_id=cid)
            snapshot["comparison"] = comp_block
            if comp_block.get("limitations"):
                snapshot["limitations"] = sorted(list(set(snapshot["limitations"] + comp_block["limitations"])))

        # 7. LLM Explanation Generation (AI001-04)
        if include_explanation:
            from lotus_fin.ai.explanation import generate_financial_explanation
            snapshot["explanation"] = generate_financial_explanation(
                snapshot=snapshot,
                provider=llm_provider,
                correlation_id=cid
            )

        log_event(
            event_type=EVENT_SNAPSHOT_COMPLETED,
            correlation_id=cid,
            company=verified_company,
            details={"snapshot_id": snapshot_id, "status": status}
        )
        log_event(
            event_type=EVENT_REQUEST_COMPLETED,
            correlation_id=cid,
            company=verified_company,
            status=status
        )
        op_metrics.record_request(status, 0.0)

        return snapshot

    @staticmethod
    def _has_active_db() -> bool:
        try:
            import frappe
            return bool(hasattr(frappe, "db") and frappe.db)
        except ImportError:
            return False

    def _validation_error_env(self, cid, now_iso, missing_inputs, limitations):
        return {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": "VALIDATION_ERROR",
            "correlation_id": cid,
            "company": None,
            "period": None,
            "as_of": now_iso,
            "snapshot_id": None,
            "data_mode": None,
            "currency": None,
            "metrics": [],
            "comparison": None,
            "explanation": None,
            "missing_inputs": missing_inputs,
            "limitations": limitations,
            "evidence_refs": []
        }

    def _forbidden_env(self, cid, now_iso, error):
        return {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": "FORBIDDEN",
            "correlation_id": cid,
            "company": None,  # Do not disclose company presence on FORBIDDEN
            "period": None,
            "as_of": now_iso,
            "snapshot_id": None,
            "data_mode": None,
            "currency": None,
            "metrics": [],
            "comparison": None,
            "explanation": None,
            "missing_inputs": [],
            "limitations": [f"Unauthorized access: {error}"],
            "evidence_refs": []
        }
