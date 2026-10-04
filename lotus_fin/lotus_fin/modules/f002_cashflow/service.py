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
    resolve_cash_account_scope,
    ObligationSourceError,
    ObligationPermissionError,
    VERIFIED_RECONCILIATION_STATUSES,
)
from .engine import compute_forecast
from .source_interface import FutureEventSource, FailClosedSource
from .cache import (
    compute_cache_key,
    get_cached_response,
    set_cached_response,
    evict_cached_response,
    acquire_single_flight,
    release_single_flight,
)

try:
    import frappe
    from lotus_fin.security.access import get_verified_company
    from lotus_fin.ai.observability import log_ai002_event
except ImportError:
    frappe = None
    get_verified_company = None
    def log_ai002_event(**kwargs):
        return {}


def build_fail_closed_response(
    request: ForecastRequest,
    status: ForecastStatus,
    reason_code: ReasonCode,
    limitation: str,
    correlation_id: str,
    include_company: bool = False,
) -> ForecastResponse:
    """
    Build a typed fail-closed response with NO financial payload
    (no opening cash, obligations, events, points or shortfall).
    Used for FORBIDDEN / SOURCE_ERROR / TIMEOUT outcomes per SSOT §12.
    """
    return ForecastResponse(
        status=status,
        reason_code=reason_code,
        verified_company=request.company if include_company else "",
        financial_as_of=request.financial_as_of,
        accounting_timezone="Asia/Ho_Chi_Minh",
        forecast_start=request.forecast_start,
        forecast_end=request.forecast_end,
        currency=request.reporting_currency,
        limitations=[limitation],
        correlation_id=correlation_id,
    )


def resolve_request_scope(company: str, user: Optional[str] = None) -> Dict[str, Any]:
    """
    Fix D (round 5): verify company authorization BEFORE any account-scope query,
    then resolve the approved scope under the caller's Account read permissions.
    Raises ObligationPermissionError (generic "Access Denied" — no company or
    account names) when the caller is not authorized for the company or cannot
    read the Account doctype/records, and ObligationSourceError when the
    authorized scope cannot be resolved.
    """
    if get_verified_company is None:
        raise ObligationSourceError("Authorization primitives are unavailable.")
    try:
        verified_company = get_verified_company(company, user=user)
    except Exception as e:
        raise ObligationPermissionError("Access Denied") from e
    try:
        return resolve_cash_account_scope(verified_company, user=user)
    except ObligationPermissionError:
        # Preserve the typed permission failure (mapped to generic FORBIDDEN upstream)
        raise
    except Exception as e:
        raise ObligationSourceError(
            "Cash account scope could not be resolved."
        ) from e


def _resolve_active_user(user: Optional[str]) -> str:
    active_user = user
    if not active_user and frappe:
        try:
            if hasattr(frappe, "session") and frappe.session and hasattr(frappe.session, "user") and frappe.session.user:
                active_user = frappe.session.user
        except Exception:
            active_user = None
    return active_user or "Administrator"


def _telemetry_source_status(source: Any, cash_events: List[Any]) -> str:
    """
    SSOT §10: an authorized, successful, correctly scoped empty read may be
    VERIFIED_ZERO_RECORDS; a fail-closed default source with no verified
    production connector is NOT_AVAILABLE — never a verified zero.
    """
    if isinstance(source, FailClosedSource):
        return "NOT_AVAILABLE"
    return "VERIFIED" if cash_events else "VERIFIED_ZERO_RECORDS"


def _reauthorize_cached_resources(user: Optional[str]) -> bool:
    """
    AI003 foundation remediation (Bucket D): a cache hit must never bypass
    resource/report reauthorization. Request validation re-runs on every call,
    but report-level permissions are otherwise only enforced inside the report
    adapters during computation — which a cache hit short-circuits. Re-check
    the AI002 report allowlist permission for the caller before any cached
    financial data is returned.
    """
    if frappe is None:
        # Non-Frappe unit environment: request validation already ran.
        return True
    try:
        from lotus_fin.security.access import AI002_PERMITTED_REPORTS, check_ai002_report_permission
    except ImportError:
        return True
    try:
        for report_name in AI002_PERMITTED_REPORTS:
            check_ai002_report_permission(report_name, user=user)
        return True
    except Exception:
        return False


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
    - Fail-closed behavior:
        * AR/AP source errors -> typed SOURCE_ERROR (never zero/empty-leg)
        * AR/AP permission denial -> generic FORBIDDEN
        * unverified opening cash reconciliation -> no forecast points/shortfall
    - If no confirmed future cash events exist, returns FORECAST_UNAVAILABLE with reason_code NO_CONFIRMED_SETTLEMENT_EVENTS
    - Fail-closed and error responses are never cached; a later call re-reads the sources
    """
    start_time = time.time()
    correlation_id = request.correlation_id or str(uuid.uuid4())
    request.correlation_id = correlation_id
    active_user = _resolve_active_user(user)

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
            verified_company="" if status == ForecastStatus.FORBIDDEN else request.company,
            financial_as_of=request.financial_as_of,
            forecast_start=request.forecast_start,
            forecast_end=request.forecast_end,
            currency=request.reporting_currency,
            limitations=[error_msg or ("Access Denied" if status == ForecastStatus.FORBIDDEN else "Validation failed")],
            correlation_id=correlation_id,
        )

    # Resolve event source
    source = future_event_source or FailClosedSource()
    source_mode = getattr(source, "source_mode", "LIVE")
    source_provider_ver = getattr(source, "provider_version", "v1")

    # 2. Check Cache (Isolated by source_mode & horizon)
    cache_key = compute_cache_key(
        user_id=active_user,
        company=request.company,
        as_of=request.financial_as_of,
        forecast_start=request.forecast_start,
        forecast_end=request.forecast_end,
        account_scope=request.cash_account_scope,
        coverage_scope=request.coverage_scope.value,
        source_mode=source_mode,
        source_provider_version=source_provider_ver,
    )
    if not skip_cache:
        cached = get_cached_response(cache_key)
        if cached:
            # Bucket D: reauthorize the underlying resources on every cache hit.
            # Permission changes inside the TTL must yield FORBIDDEN with no
            # cached financial payload, and the stale entry is evicted.
            if _reauthorize_cached_resources(active_user):
                return cached
            evict_cached_response(cache_key)
            log_ai002_event(
                event_type="ai002_forecast_rejected",
                correlation_id=correlation_id,
                status=ForecastStatus.FORBIDDEN.value,
                error_class="PermissionError",
                latency_ms=(time.time() - start_time) * 1000,
            )
            return build_fail_closed_response(
                request=request,
                status=ForecastStatus.FORBIDDEN,
                reason_code=ReasonCode.UNAUTHORIZED_ACCESS,
                limitation="Access Denied",
                correlation_id=correlation_id,
                include_company=False,
            )

    flight_acquired = acquire_single_flight(f"{request.company}:{request.financial_as_of}:{source_mode}")

    try:
        # 3. Data Gathering (Opening cash & obligations) — typed fail-closed errors
        # PB-SEC-01: fresh-path report authorization evaluates the checked
        # user, mirroring the cache-hit reauthorization contract.
        try:
            opening_cash = get_opening_cash_ledger(
                company=request.company,
                as_of=request.financial_as_of,
                account_scope=request.cash_account_scope,
                currency=request.reporting_currency,
                user=active_user,
            )

            obligations = get_trade_obligations(
                company=request.company,
                as_of=request.financial_as_of,
                currency=request.reporting_currency,
                user=active_user,
            )
        except ObligationPermissionError:
            # SSOT §12: permission denied is generic FORBIDDEN with no financial payload
            log_ai002_event(
                event_type="ai002_forecast_rejected",
                correlation_id=correlation_id,
                status=ForecastStatus.FORBIDDEN.value,
                error_class="PermissionError",
                latency_ms=(time.time() - start_time) * 1000,
            )
            return build_fail_closed_response(
                request=request,
                status=ForecastStatus.FORBIDDEN,
                reason_code=ReasonCode.UNAUTHORIZED_ACCESS,
                limitation="Access Denied",
                correlation_id=correlation_id,
                include_company=False,
            )
        except ObligationSourceError as e:
            # SSOT §12: preserve typed source failure, never map to zero;
            # error text carries no party/invoice/amount. Not cached.
            log_ai002_event(
                event_type="ai002_forecast_rejected",
                correlation_id=correlation_id,
                status=ForecastStatus.SOURCE_ERROR.value,
                error_class="SourceError",
                latency_ms=(time.time() - start_time) * 1000,
            )
            return build_fail_closed_response(
                request=request,
                status=ForecastStatus.SOURCE_ERROR,
                reason_code=ReasonCode.DATA_PIPELINE_ERROR,
                limitation=f"Financial data source unavailable: {e}",
                correlation_id=correlation_id,
                include_company=True,
            )

        # 4. Fix B gate: opening cash must be verified against the independent
        # Trial Balance BEFORE any response branch — including the no-events
        # FORECAST_UNAVAILABLE baseline. Unverified financial data is never
        # returned or cached as a valid result.
        if opening_cash.reconciliation not in VERIFIED_RECONCILIATION_STATUSES:
            if opening_cash.reconciliation == "INCONSISTENT_DATA":
                status = ForecastStatus.INCONSISTENT_DATA
                limitation = (
                    "Opening cash GL could not be reconciled with the independent "
                    "Trial Balance for the authorized account set; forecast computation is blocked."
                )
            else:
                status = ForecastStatus.INSUFFICIENT_DATA
                limitation = (
                    "Opening cash reconciliation evidence is unavailable; "
                    "forecast computation is blocked."
                )
            log_ai002_event(
                event_type="ai002_forecast_rejected",
                correlation_id=correlation_id,
                status=status.value,
                error_class="ReconciliationError",
                latency_ms=(time.time() - start_time) * 1000,
            )
            # Not cached: a later call re-reads and may succeed
            return build_fail_closed_response(
                request=request,
                status=status,
                reason_code=ReasonCode.DATA_PIPELINE_ERROR,
                limitation=limitation,
                correlation_id=correlation_id,
                include_company=True,
            )

        # 5. Future settlement events
        source = future_event_source or FailClosedSource()
        cash_events = get_future_cash_events(
            company=request.company,
            start_date=request.forecast_start,
            end_date=request.forecast_end,
            source_adapter=source,
            currency=request.reporting_currency,
            financial_as_of=request.financial_as_of,
        )

        # 6. Contractual Rule: If no confirmed future cash events -> FORECAST_UNAVAILABLE
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
                source_status=_telemetry_source_status(source, cash_events),
                coverage_scope="TRADE_ONLY",
                record_count=len(obligations),
                latency_ms=(time.time() - start_time) * 1000,
            )
            set_cached_response(cache_key, response)
            return response

        # 7. Compute Deterministic Running Sum (opening cash is verified above)
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

        # 8. Optional bounded AI Copilot explanation
        if request.include_explanation:
            from .agent import explain_cash_forecast
            response.explanation = explain_cash_forecast(response)

        log_ai002_event(
            event_type="ai002_forecast_completed",
            correlation_id=correlation_id,
            status=ForecastStatus.PARTIAL.value,
            source_status=_telemetry_source_status(source, cash_events),
            coverage_scope="TRADE_ONLY",
            record_count=len(cash_events),
            latency_ms=(time.time() - start_time) * 1000,
        )

        set_cached_response(cache_key, response)
        return response

    finally:
        if flight_acquired:
            release_single_flight(f"{request.company}:{request.financial_as_of}:{source_mode}")


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
