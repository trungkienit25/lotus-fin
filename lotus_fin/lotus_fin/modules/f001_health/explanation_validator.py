"""
Module F001 - Explanation Schema & Grounding Validation.
Enforces strict JSON schema, numeric grounding, and prohibited guarantee checks.
"""

from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from lotus_fin.core.domain.calculators.grounding_guard import GroundingGuard, sanitize_text

SYSTEM_PROMPT = """You are Lotus Fin AI-F001 Financial Health Analyst.
Your role is to produce a grounded, factual, professional explanation of an SME's financial snapshot.
Output strictly JSON: {"status": "AVAILABLE", "facts": [...], "interpretations": [...], "next_checks": [...]}
"""

PROHIBITED_PHRASES = [
    "guaranteed profit", "guarantee profit", "will definitely grow",
    "certified compliant", "audit certified", "exempt from taxes",
    "risk-free", "certain return", "100% safe"
]


def build_minimized_model_payload(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    metrics_summary = [
        {
            "metric_id": m.get("metric_id"),
            "status": m.get("status"),
            "value": m.get("value"),
            "unit": m.get("currency_or_unit"),
            "limitations": m.get("limitations", [])
        }
        for m in snapshot.get("metrics", [])
    ]
    comparison_summary = None
    if snapshot.get("comparison") and snapshot["comparison"].get("status") == "AVAILABLE":
        comp = snapshot["comparison"]
        comparison_summary = {
            "status": comp.get("status", "AVAILABLE"),
            "type": comp.get("type"),
            "previous_period": comp.get("previous_period"),
            "metrics": comp.get("metrics")
        }

    return {
        "feature": "AI-F001 Financial Health Analyst",
        "company": snapshot.get("company"),
        "period": snapshot.get("period"),
        "currency": snapshot.get("currency"),
        "status": snapshot.get("status"),
        "metrics": metrics_summary,
        "comparison": comparison_summary,
        "missing_inputs": snapshot.get("missing_inputs", []),
        "limitations": snapshot.get("limitations", [])
    }



def extract_numbers_from_text(text: str) -> List[Decimal]:
    cleaned = re.sub(r'\b(20[1-3][0-9])\b', '', text)
    cleaned = re.sub(r'^\s*\d+[\.\)]\s*', '', cleaned)
    tokens = re.findall(r'-?\d+(?:,\d+)*(?:\.\d+)?', cleaned)
    numbers = []
    for tok in tokens:
        raw_str = tok.replace(',', '')
        try:
            numbers.append(Decimal(raw_str))
        except InvalidOperation:
            continue
    return numbers


def validate_explanation_schema(response: Any) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
    errors = []
    if not isinstance(response, dict):
        return False, None, ["Root explanation response must be a JSON object."]

    required_keys = ["status", "facts", "interpretations", "next_checks"]
    for k in required_keys:
        if k not in response:
            errors.append(f"Missing required key: '{k}'")

    if response.get("status") not in ["AVAILABLE", "UNAVAILABLE", "PARTIAL"]:
        errors.append(f"Invalid status '{response.get('status')}'.")

    for list_key in ["facts", "interpretations", "next_checks"]:
        val = response.get(list_key)
        if not isinstance(val, list):
            errors.append(f"Field '{list_key}' must be an array of strings.")
        elif not all(isinstance(item, str) for item in val):
            errors.append(f"All elements in '{list_key}' must be strings.")

    if errors:
        return False, None, errors

    clean = {
        "status": response["status"],
        "facts": [sanitize_text(s) for s in response["facts"]],
        "interpretations": [sanitize_text(s) for s in response["interpretations"]],
        "next_checks": [sanitize_text(s) for s in response["next_checks"]]
    }
    return True, clean, []


def validate_grounding(explanation: Dict[str, Any], snapshot: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    allowed_numbers = GroundingGuard.collect_allowed_numbers(snapshot)

    all_prose = explanation.get("facts", []) + explanation.get("interpretations", [])
    for text in all_prose:
        text_lower = text.lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in text_lower:
                errors.append(f"Prohibited forward-looking or guaranteed claim detected: '{phrase}'")

        for num in extract_numbers_from_text(text):
            matched = any(abs(num - allowed) < Decimal("0.05") for allowed in allowed_numbers)
            if not matched:
                errors.append(f"Ungrounded number '{num}' cited in text '{text[:60]}...'")

    return len(errors) == 0, errors
