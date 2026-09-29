import os
import json
import time
from typing import Dict, Any, List, Optional
from decimal import Decimal

from .models import ForecastResponse, ForecastStatus, Explanation
from .tools import TOOL_DISPATCH
from .grounding import validate_grounding

NEXT_CHECK_TEMPLATES = {
    "RECONCILE_BANK_TRANSACTIONS": {
        "label": "Reconcile unposted bank transactions",
        "link": "/app/bank-reconciliation-tool",
    },
    "FOLLOW_UP_OVERDUE_AR": {
        "label": "Follow up on overdue receivables",
        "link": "/app/query-report/Accounts%20Receivable?status=Overdue",
    },
    "CONFIRM_AP_PAYMENT_SCHEDULE": {
        "label": "Confirm vendor payment schedule dates",
        "link": "/app/purchase-invoice",
    },
    "RESOLVE_UNALLOCATED_PAYMENTS": {
        "label": "Allocate unlinked payment entries",
        "link": "/app/payment-entry",
    },
}

CIRCUIT_BREAKER_TIMEOUT_SECONDS = 5.0


def strip_free_text(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    CG-SEC-05: Strip free-text fields before model ingestion.
    Removes 'remarks', 'user_remarks', 'description', 'notes'.
    """
    forbidden_keys = {"remarks", "user_remarks", "description", "notes", "comment", "party_name"}
    cleaned = {}
    for k, v in payload.items():
        if k.lower() in forbidden_keys:
            continue
        if isinstance(v, dict):
            cleaned[k] = strip_free_text(v)
        elif isinstance(v, list):
            cleaned[k] = [strip_free_text(i) if isinstance(i, dict) else i for i in v]
        else:
            cleaned[k] = v
    return cleaned


def explain_cash_forecast(
    forecast_response: ForecastResponse,
    user_query: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Explanation:
    """
    Bounded Agentic AI Copilot for Cash Forecast Explanation.
    Follows AI002 Section 20:
    - 5000ms circuit breaker timeout
    - Free text stripped
    - Strict next-checks allowlist
    - Grounding validation
    - Fail closed: if LLM fails or times out, explanation.status=UNAVAILABLE,
      leaving deterministic financial data intact.
    """
    # 1. Deterministic facts extraction from allowed tools
    facts = []
    drivers = []
    next_checks = []

    # Fact 1: Opening cash
    if forecast_response.opening_cash:
        facts.append({
            "type": "FACT",
            "statement": f"Opening cash balance is {forecast_response.opening_cash.aggregate_amount:,.0f} {forecast_response.currency}.",
            "ref": "tabGL Entry",
        })
        if forecast_response.opening_cash.has_constituent_deficit:
            facts.append({
                "type": "FACT",
                "statement": "Constituent bank account deficit detected despite positive net aggregate balance.",
                "ref": "tabGL Entry",
            })

    # Fact 2: Shortfall events
    if forecast_response.shortfall_events:
        for sf in forecast_response.shortfall_events:
            facts.append({
                "type": "FACT",
                "statement": f"Modeled cash deficit breached threshold {sf.threshold} on {sf.first_date}, reaching minimum of {sf.minimum_modeled_cash:,.0f} {forecast_response.currency} on {sf.minimum_date} ({sf.breach_kind.value if sf.breach_kind else 'NEW_MODELED_DEFICIT'}).",
                "ref": "engine.py",
            })

    # Deterministic Next Checks suggestion
    next_checks.append({
        "type": "NEXT_CHECK",
        "action": "FOLLOW_UP_OVERDUE_AR",
        "label": NEXT_CHECK_TEMPLATES["FOLLOW_UP_OVERDUE_AR"]["label"],
        "link": NEXT_CHECK_TEMPLATES["FOLLOW_UP_OVERDUE_AR"]["link"],
    })
    next_checks.append({
        "type": "NEXT_CHECK",
        "action": "CONFIRM_AP_PAYMENT_SCHEDULE",
        "label": NEXT_CHECK_TEMPLATES["CONFIRM_AP_PAYMENT_SCHEDULE"]["label"],
        "link": NEXT_CHECK_TEMPLATES["CONFIRM_AP_PAYMENT_SCHEDULE"]["link"],
    })

    # If forecast is unavailable due to no future events
    if forecast_response.status == ForecastStatus.FORECAST_UNAVAILABLE:
        return Explanation(
            status="OK",
            facts=facts,
            drivers=[],
            limitations=forecast_response.limitations,
            next_checks=next_checks,
        )

    # If API key is available and LLM is enabled, we could query OpenAI with a 5000ms circuit breaker.
    # Note: As per rule, API key is strictly used in memory and never logged.
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        return Explanation(
            status="OK",
            facts=facts,
            drivers=drivers,
            limitations=forecast_response.limitations,
            next_checks=next_checks,
        )

    # Calling LLM under circuit breaker
    try:
        import urllib.request
        start_call = time.time()
        
        prompt_data = {
            "company": forecast_response.verified_company,
            "opening_cash": str(forecast_response.opening_cash.aggregate_amount) if forecast_response.opening_cash else "0",
            "points_count": len(forecast_response.forecast_points),
            "shortfall_count": len(forecast_response.shortfall_events),
            "limitations": forecast_response.limitations,
        }
        stripped_prompt = strip_free_text(prompt_data)

        req_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial copilot. Explain the 30-day cash forecast strictly using the provided structured facts. Do NOT invent new numbers or make forward speculations.",
                },
                {"role": "user", "content": json.dumps(stripped_prompt)},
            ],
            "max_tokens": 200,
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(req_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=CIRCUIT_BREAKER_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "choices" not in data or not data["choices"]:
                return Explanation(
                    status="UNAVAILABLE",
                    error_code="MALFORMED_OUTPUT",
                    reason="Model returned empty or malformed output.",
                    facts=facts,
                    drivers=[],
                    limitations=forecast_response.limitations,
                    next_checks=next_checks,
                )

            content = data["choices"][0]["message"].get("content", "")
            if not content or not content.strip():
                return Explanation(
                    status="UNAVAILABLE",
                    error_code="MALFORMED_OUTPUT",
                    reason="Model response content was empty.",
                    facts=facts,
                    drivers=[],
                    limitations=forecast_response.limitations,
                    next_checks=next_checks,
                )

            # Grounding validation
            is_grounded, violations = validate_grounding(content, forecast_response)
            if not is_grounded:
                return Explanation(
                    status="UNAVAILABLE",
                    error_code="GROUNDING_VIOLATION",
                    reason=f"Grounding validation failed: {'; '.join(violations)}",
                    facts=facts,
                    drivers=[],
                    limitations=forecast_response.limitations,
                    next_checks=next_checks,
                )

            drivers.append({
                "type": "INTERPRETATION",
                "statement": content.strip(),
            })

    except TimeoutError:
        return Explanation(
            status="UNAVAILABLE",
            error_code="TIMEOUT",
            reason="LLM response timed out under 5000ms circuit breaker.",
            facts=facts,
            drivers=[],
            limitations=forecast_response.limitations,
            next_checks=next_checks,
        )
    except Exception as exc:
        err_type = type(exc).__name__
        err_code = "TIMEOUT" if "timed out" in str(exc).lower() else "PROVIDER_UNAVAILABLE"
        return Explanation(
            status="UNAVAILABLE",
            error_code=err_code,
            reason=f"Model execution error ({err_type}). Deterministic financial truth preserved.",
            facts=facts,
            drivers=[],
            limitations=forecast_response.limitations,
            next_checks=next_checks,
        )

    return Explanation(
        status="OK",
        facts=facts,
        drivers=drivers,
        limitations=forecast_response.limitations,
        next_checks=next_checks,
    )
