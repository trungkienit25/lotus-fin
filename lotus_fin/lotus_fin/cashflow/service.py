import time
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from .models import (
    ForecastRequest,
    ForecastResponse,
    ForecastStatus,
    ReasonCode,
    Coverage,
    CoverageScope,
    BreachKind,
)
from .validation import validate_forecast_request
from .adapters import (
    get_opening_cash_ledger,
    get_trade_obligations,
    get_future_cash_events,
)
from .engine import compute_forecast
from .source_interface import FutureEventSource, FailClosedSource
from .cache import (
    compute_cache_key,
    get_cached_response,
    set_cached_response,
    acquire_single_flight,
    release_single_flight,
)

try:
    import frappe
    from lotus_fin.ai.observability import log_ai002_event
except ImportError:
    frappe = None
    def log_ai002_event(**kwargs):
        return {}


def get_cash_forecast(
    request: ForecastRequest,
    user: Optional[str] = None,
    future_event_source: Optional[FutureEventSource] = None,
    skip_cache: bool = False,
) -> ForecastResponse:
    """
    Main AI002 deterministic forecast orchestration service.
    Follows AI002 MASTER SSOT V1.2.1 contract:
    - Zero-is-not-error invariant
    - Server-side authorization & validation
    - O(N) in-memory Decimal running sum
    - Fail-closed behavior
    - If no confirmed future cash events exist, returns FORECAST_UNAVAILABLE with reason_code NO_CONFIRMED_SETTLEMENT_EVENTS
    """
    start_time = time.time()
    correlation_id = request.correlation_id or str(uuid.uuid4())
    request.correlation_id = correlation_id
    
    # Safe user resolution across both web requests and standalone script/test execution
    active_user = user
    if not active_user and frappe:
        try:
            if hasattr(frappe, "session") and frappe.session and hasattr(frappe.session, "user") and frappe.session.user:
                active_user = frappe.session.user
        except Exception:
            active_user = None
    if not active_user:
        active_user = "Administrator"

    # 1. Validation & Server Authorization
    is_valid, reason_code, error_msg = validate_forecast_request(request, user=active_user)
    if not is_valid:
        status = ForecastStatus.FORBIDDEN if reason_code == ReasonCode.UNAUTHORIZED_ACCESS else ForecastStatus.VALIDATION_ERROR
        log_ai002_event(
            event_type="ai002_forecast_rejected",
            correlation_id=correlation_id,
            status=status.value,
            error_class="PermissionError" if status == ForecastStatus.FORBIDDEN else "ValidationError",
            latency_ms=(time.time() - start_time) * 1000,
        )
        return ForecastResponse(
            status=status,
            reason_code=reason_code,
            verified_company=request.company,
            financial_as_of=request.financial_as_of,
            forecast_start=request.forecast_start,
            forecast_end=request.forecast_end,
            currency=request.reporting_currency,
            limitations=[error_msg or "Validation failed"],
            correlation_id=correlation_id,
        )

    # 2. Check Cache
    cache_key = compute_cache_key(
        user_id=active_user,
        company=request.company,
        as_of=request.financial_as_of,
        account_scope=request.cash_account_scope,
        coverage_scope=request.coverage_scope.value,
    )
    if not skip_cache:
        cached = get_cached_response(cache_key)
        if cached:
            return cached

    flight_acquired = acquire_single_flight(f"{request.company}:{request.financial_as_of}")

    try:
        # 3. Data Gathering (Opening cash & obligations)
        opening_cash = get_opening_cash_ledger(
            company=request.company,
            as_of=request.financial_as_of,
            account_scope=request.cash_account_scope,
            currency=request.reporting_currency,
        )

        obligations = get_trade_obligations(
            company=request.company,
            as_of=request.financial_as_of,
            currency=request.reporting_currency,
        )

        # 4. Future settlement events
        source = future_event_source or FailClosedSource()
        cash_events = get_future_cash_events(
            company=request.company,
            start_date=request.forecast_start,
            end_date=request.forecast_end,
            source_adapter=source,
            currency=request.reporting_currency,
            financial_as_of=request.financial_as_of,
        )

        # 5. Contractual Rule: If no confirmed future cash events -> FORECAST_UNAVAILABLE
        limitations: List[str] = [
            "Future event source is synthetic fixture-only or unverified, not a verified production connector",
            "Business obligation coverage incomplete (TRADE_ONLY scope)",
            "No subjective risk rating or liquidity buffer is approved",
        ]
        assumptions: List[str] = [
            "Invoice contractual due dates are obligation markers only, not cash settlement timing",
        ]

        if not cash_events:
            limitations.insert(0, "No eligible future cash date")
            response = ForecastResponse(
                status=ForecastStatus.FORECAST_UNAVAILABLE,
                reason_code=ReasonCode.NO_CONFIRMED_SETTLEMENT_EVENTS,
                forecast_id=f"FC-{uuid.uuid4().hex[:8].upper()}",
                snapshot_id=f"SNAP-{uuid.uuid4().hex[:8].upper()}",
                contract_version="1.2.1",
                method_version="STRICT_BASELINE_V1",
                formula_version="STRICT_BASELINE_V1",
                verified_company=request.company,
                financial_as_of=request.financial_as_of,
                accounting_timezone="Asia/Ho_Chi_Minh",
                forecast_start=request.forecast_start,
                forecast_end=request.forecast_end,
                currency=request.reporting_currency,
                opening_cash=opening_cash,
                opening_cash_deficit=opening_cash.aggregate_amount < Decimal("0"),
                obligations=obligations,
                cash_events=[],
                forecast_points=[],
                coverage=Coverage(
                    scope=CoverageScope.TRADE_ONLY,
                    completeness="PARTIAL",
                ),
                assumptions=assumptions,
                limitations=limitations,
                shortfall_events=[],
                correlation_id=correlation_id,
            )
            log_ai002_event(
                event_type="ai002_forecast_completed",
                correlation_id=correlation_id,
                status=ForecastStatus.FORECAST_UNAVAILABLE.value,
                source_status="VERIFIED_ZERO",
                coverage_scope="TRADE_ONLY",
                record_count=len(obligations),
                latency_ms=(time.time() - start_time) * 1000,
            )
            set_cached_response(cache_key, response)
            return response

        # 6. Compute Deterministic Running Sum
        forecast_points, shortfall_events = compute_forecast(
            opening_cash=opening_cash,
            cash_events=cash_events,
            forecast_start=request.forecast_start,
            forecast_end=request.forecast_end,
        )

        response = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            forecast_id=f"FC-{uuid.uuid4().hex[:8].upper()}",
            snapshot_id=f"SNAP-{uuid.uuid4().hex[:8].upper()}",
            contract_version="1.2.1",
            method_version="STRICT_BASELINE_V1",
            formula_version="STRICT_BASELINE_V1",
            verified_company=request.company,
            financial_as_of=request.financial_as_of,
            accounting_timezone="Asia/Ho_Chi_Minh",
            forecast_start=request.forecast_start,
            forecast_end=request.forecast_end,
            currency=request.reporting_currency,
            opening_cash=opening_cash,
            opening_cash_deficit=opening_cash.aggregate_amount < Decimal("0"),
            obligations=obligations,
            cash_events=cash_events,
            forecast_points=forecast_points,
            coverage=Coverage(
                scope=CoverageScope.TRADE_ONLY,
                completeness="PARTIAL",
            ),
            assumptions=assumptions,
            limitations=limitations,
            shortfall_events=shortfall_events,
            correlation_id=correlation_id,
        )

        # 7. Optional bounded AI Copilot explanation
        if request.include_explanation:
            from .agent import explain_cash_forecast
            response.explanation = explain_cash_forecast(response)

        log_ai002_event(
            event_type="ai002_forecast_completed",
            correlation_id=correlation_id,
            status=ForecastStatus.PARTIAL.value,
            source_status="OK",
            coverage_scope="TRADE_ONLY",
            record_count=len(cash_events),
            latency_ms=(time.time() - start_time) * 1000,
        )

        set_cached_response(cache_key, response)
        return response

    finally:
        if flight_acquired:
            release_single_flight(f"{request.company}:{request.financial_as_of}")


def response_to_dict(response: ForecastResponse) -> Dict[str, Any]:
    """Helper to serialize ForecastResponse into pure JSON serializable dict for REST API."""
    def serialize_obj(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (date,)):
            return obj.isoformat()
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "__dict__"):
            return {k: serialize_obj(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, list):
            return [serialize_obj(i) for i in obj]
        if isinstance(obj, dict):
            return {k: serialize_obj(v) for k, v in obj.items()}
        return obj

    return serialize_obj(response)
