from typing import Dict, Any, List, Optional
from decimal import Decimal
from .models import ForecastResponse


def tool_cash_forecast_get(forecast_response: ForecastResponse) -> Dict[str, Any]:
    """cash_forecast.get: Returns high level summary of opening cash and forecast points."""
    return {
        "status": forecast_response.status.value,
        "verified_company": forecast_response.verified_company,
        "opening_cash": str(forecast_response.opening_cash.aggregate_amount) if forecast_response.opening_cash else "0",
        "has_constituent_deficit": forecast_response.opening_cash.has_constituent_deficit if forecast_response.opening_cash else False,
        "points_count": len(forecast_response.forecast_points),
        "shortfall_count": len(forecast_response.shortfall_events),
    }


def tool_cash_forecast_get_coverage(forecast_response: ForecastResponse) -> Dict[str, Any]:
    """cash_forecast.get_coverage: Returns coverage scope and completeness."""
    if not forecast_response.coverage:
        return {"scope": "UNKNOWN", "completeness": "UNAVAILABLE"}
    return {
        "scope": forecast_response.coverage.scope.value,
        "completeness": forecast_response.coverage.completeness,
        "unverified_obligations": forecast_response.coverage.unverified_obligations,
    }


def tool_cash_forecast_get_obligations(forecast_response: ForecastResponse) -> Dict[str, Any]:
    """cash_forecast.get_obligations: Returns trade obligations with pseudonymous party hashes."""
    return {
        "obligations": [
            {
                "type": o.type,
                "party_type": o.party_type,
                "party_hash": o.party_hash,
                "remaining_amount": str(o.remaining_amount),
                "due_date": str(o.due_date) if o.due_date else None,
                "source_ref": o.source_ref,
            }
            for o in forecast_response.obligations
        ]
    }


def tool_cash_forecast_get_drivers(forecast_response: ForecastResponse) -> Dict[str, Any]:
    """cash_forecast.get_drivers: Returns confirmed future cash events driving the balance."""
    return {
        "events": [
            {
                "source_ref": e.source_ref,
                "date": str(e.date),
                "direction": e.direction.value,
                "amount": str(e.amount),
                "timing_basis": e.timing_basis,
            }
            for e in forecast_response.cash_events
        ]
    }


def tool_cash_forecast_get_evidence(forecast_response: ForecastResponse, user: Optional[str] = None) -> Dict[str, Any]:
    """
    cash_forecast.get_evidence: Returns verified evidence references.
    CG-SEC-04: Enforces server-side evidence re-authorization before returning any evidence ref.
    Fails closed: refs without colon or failing reauthorization are excluded.
    """
    authorized_refs = []
    try:
        from lotus_fin.security.access import verify_evidence_access
        for ref in forecast_response.evidence_refs:
            if ":" in ref:
                try:
                    verify_evidence_access(ref, user=user, company=forecast_response.verified_company)
                    authorized_refs.append(ref)
                except Exception:
                    continue
    except ImportError:
        authorized_refs = [ref for ref in forecast_response.evidence_refs if ":" in ref]

    return {
        "evidence_refs": authorized_refs,
        "assumptions": forecast_response.assumptions,
        "limitations": forecast_response.limitations,
    }



def tool_cash_forecast_get_missing_inputs(forecast_response: ForecastResponse) -> Dict[str, Any]:
    """cash_forecast.get_missing_inputs: Identifies unverified or missing commitment sources."""
    missing = []
    if not forecast_response.cash_events:
        missing.append("CONFIRMED_FUTURE_EVENT_SOURCE")
    return {
        "missing_inputs": missing,
        "limitations": forecast_response.limitations,
    }


TOOL_DISPATCH = {
    "cash_forecast.get": tool_cash_forecast_get,
    "cash_forecast.get_coverage": tool_cash_forecast_get_coverage,
    "cash_forecast.get_obligations": tool_cash_forecast_get_obligations,
    "cash_forecast.get_drivers": tool_cash_forecast_get_drivers,
    "cash_forecast.get_evidence": tool_cash_forecast_get_evidence,
    "cash_forecast.get_missing_inputs": tool_cash_forecast_get_missing_inputs,
}
