from datetime import datetime, timezone
import uuid
from typing import Any, Callable, Dict, Optional

from lotus_fin.core.use_cases.source_gatherer import SourceGatherer
from lotus_fin.core.use_cases.metric_assembler import MetricAssembler

FEATURE_ID = "AI001"
CONTRACT_VERSION = "1.0.0"


class SnapshotCoordinator:
    """Coordinates deterministic financial health snapshot aggregation conforming to AI001."""

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

        # 1. Period bounds validation
        try:
            p_start = datetime.strptime(period_start, "%Y-%m-%d").date()
            p_end = datetime.strptime(period_end, "%Y-%m-%d").date()
            if p_start > p_end:
                return self._error_env(cid, now_iso, "VALIDATION_ERROR", ["period_start cannot be after period_end"])
        except (ValueError, TypeError) as e:
            return self._error_env(cid, now_iso, "VALIDATION_ERROR", [f"Malformed period date: {str(e)}"])

        # 2. Company authorization guard
        verified_company = company
        try:
            import frappe
            if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
                from lotus_fin.security.access import get_verified_company
                verified_company = get_verified_company(company, user=user)
            elif not company:
                raise ValueError("Company cannot be empty")
        except Exception as e:
            return self._error_env(cid, now_iso, "FORBIDDEN", [str(e)])

        # 3. Source Gathering
        as_of_date_str = str(as_of)[:10] if as_of else period_end
        effective_end_date = min(period_end, as_of_date_str) if as_of_date_str else period_end
        sources, fetch_errors, filters_used = SourceGatherer.gather(
            verified_company, period_start, period_end, effective_end_date, raw_sources, source_fetcher
        )

        # 4. Metrics & Evidence
        period_obj = {"start": period_start, "end": period_end}
        metrics, ev_refs, lims, missing = MetricAssembler.assemble(
            verified_company, period_start, effective_end_date, now_iso, currency, snapshot_id, period_obj,
            sources, fetch_errors, filters_used
        )

        # Status Decision
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

        # 5. Period Comparison
        if comparison == "PREVIOUS_PERIOD":
            from lotus_fin.ai.financial_health import compute_previous_period, build_comparison_block
            prev_s, prev_e = compute_previous_period(period_start, period_end)
            prev_snap = None
            if source_fetcher:
                try:
                    prev_snap = self.build_snapshot(
                        company=verified_company, period_start=prev_s, period_end=prev_e,
                        currency=currency, correlation_id=f"{cid}-PREV", source_fetcher=source_fetcher, user=user
                    )
                except Exception:
                    pass
            comp_block = build_comparison_block(snapshot, prev_snap, correlation_id=cid)
            snapshot["comparison"] = comp_block
            if comp_block.get("limitations"):
                snapshot["limitations"] = sorted(list(set(snapshot["limitations"] + comp_block["limitations"])))

        # 6. Explanation
        if include_explanation:
            from lotus_fin.ai.explanation import generate_financial_explanation
            snapshot["explanation"] = generate_financial_explanation(snapshot=snapshot, provider=llm_provider, correlation_id=cid)

        return snapshot

    def _error_env(self, cid, now_iso, status, errors):
        return {
            "feature_id": FEATURE_ID,
            "contract_version": CONTRACT_VERSION,
            "status": status,
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
            "missing_inputs": errors,
            "limitations": ["Encountered request validation or permission failure."],
            "evidence_refs": []
        }
