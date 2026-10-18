import re
from typing import Dict, Any, List, Optional, Tuple, Set
from decimal import Decimal
from datetime import date
from .models import ForecastResponse, ForecastStatus


def _extract_amounts(text: str) -> Set[Decimal]:
    """
    Extract all financial-like numeric tokens including:
    0, 1, 12, 9999, 11,550,000, -450000, 0.00.
    Does NOT ignore short numbers (Fix D).
    Ignores numbers that are part of dates (YYYY-MM-DD or DD/MM/YYYY) or words.
    """
    amounts = set()
    # Mask out dates first so year/month/day aren't treated as standalone amounts
    masked_text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', text)
    masked_text = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', ' ', masked_text)

    pattern = r'(?<![A-Za-z0-9_])-?\b\d{1,3}(?:[,\.]\d{3})+(?:[,\.]\d+)?\b|(?<![A-Za-z0-9_])-?\b\d+(?:[,\.]\d+)?\b'
    matches = re.findall(pattern, masked_text)
    for m in matches:
        s = m.strip()
        if ',' in s and '.' in s:
            if s.rfind('.') > s.rfind(','):
                s = s.replace(',', '')
            else:
                s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            parts = s.split(',')
            if len(parts[-1]) == 3 and len(parts) > 1:
                s = s.replace(',', '')
            else:
                s = s.replace(',', '.')
        elif '.' in s:
            parts = s.split('.')
            if len(parts[-1]) == 3 and len(parts) > 1:
                s = s.replace('.', '')
        try:
            amounts.add(Decimal(s))
        except Exception:
            pass
    return amounts



def _extract_dates(text: str) -> Set[str]:
    """Extract dates in YYYY-MM-DD or DD/MM/YYYY format."""
    pattern = r'\b(\d{4}-\d{2}-\d{2})\b|\b(\d{2}/\d{2}/\d{4})\b'
    matches = re.findall(pattern, text)
    dates = set()
    for iso, vn in matches:
        if iso:
            dates.add(iso)
        elif vn:
            parts = vn.split("/")
            dates.add(f"{parts[2]}-{parts[1]}-{parts[0]}")
    return dates


def validate_grounding(explanation_text: str, forecast_response: ForecastResponse) -> Tuple[bool, List[str]]:
    """
    Grounding Validator (CG-REL-01, CG-SEC-05, P0 AI Safety):
    Ensures that any monetary claims, dates, company references, or currencies
    made in the explanation are strictly grounded in the deterministic financial result.
    """
    violations: List[str] = []
    text_lower = explanation_text.lower()

    # 1. Unallowed risk claims (no subjective safety rating allowed)
    forbidden_risk_terms = ["safe", "low risk", "high risk", "guaranteed liquidity", "no risk"]
    for term in forbidden_risk_terms:
        # Check term as word boundary
        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
            violations.append(f"Explanation contains unapproved subjective risk rating or guarantee: '{term}'")

    # 2. Company integrity
    # If a specific company is mentioned, it must not contradict verified_company
    if forecast_response.verified_company:
        comp_lower = forecast_response.verified_company.lower()
        # If text explicitly mentions another company keyword or wrong company
        if "company:" in text_lower or "công ty:" in text_lower:
            if comp_lower not in text_lower:
                violations.append("Explanation refers to unverified or mismatching company.")

    # 3. Currency check
    # Supports USD standard or legacy VND; reject EUR, GBP, etc.
    if "eur" in text_lower or "€" in text_lower or "gbp" in text_lower or "£" in text_lower:
        violations.append("Explanation mentions unsupported currency; only USD and VND are valid.")

    # 4. If forecast itself is unavailable, explanation must not assert positive cash or imaginary forecasts
    if forecast_response.status == ForecastStatus.FORECAST_UNAVAILABLE:
        if ("cash balance is" in text_lower or "số dư là" in text_lower) and "unavailable" not in text_lower and "không khả dụng" not in text_lower:
            violations.append("Explanation asserts specific cash balance when forecast is unavailable.")

    # 5. Extract all grounded amounts from deterministic result
    grounded_amounts: Set[Decimal] = set()
    if forecast_response.opening_cash:
        grounded_amounts.add(forecast_response.opening_cash.aggregate_amount)
        for acc in forecast_response.opening_cash.accounts:
            grounded_amounts.add(acc.amount)

    for pt in forecast_response.forecast_points:
        grounded_amounts.add(pt.modeled_cash)

    for ev in forecast_response.cash_events:
        grounded_amounts.add(ev.amount)

    for ob in forecast_response.obligations:
        grounded_amounts.add(ob.remaining_amount)

    for sf in forecast_response.shortfall_events:
        grounded_amounts.add(sf.minimum_modeled_cash)
        grounded_amounts.add(sf.threshold)

    # Validate numbers in text against grounded_amounts
    claimed_amounts = _extract_amounts(explanation_text)
    for claimed in claimed_amounts:
        # Check absolute value equality or exact equality
        if claimed not in grounded_amounts and abs(claimed) not in grounded_amounts:
            violations.append(f"Claimed amount {claimed} is not grounded in deterministic result or evidence.")

    # 6. Extract all grounded dates
    grounded_dates: Set[str] = set()
    if forecast_response.financial_as_of:
        grounded_dates.add(forecast_response.financial_as_of.isoformat())
    if forecast_response.forecast_start:
        grounded_dates.add(forecast_response.forecast_start.isoformat())
    if forecast_response.forecast_end:
        grounded_dates.add(forecast_response.forecast_end.isoformat())

    for pt in forecast_response.forecast_points:
        grounded_dates.add(pt.date.isoformat())

    for ev in forecast_response.cash_events:
        grounded_dates.add(ev.date.isoformat())

    for ob in forecast_response.obligations:
        if ob.due_date:
            grounded_dates.add(ob.due_date.isoformat())

    for sf in forecast_response.shortfall_events:
        grounded_dates.add(sf.first_date.isoformat())
        grounded_dates.add(sf.minimum_date.isoformat())

    claimed_dates = _extract_dates(explanation_text)
    for cdate in claimed_dates:
        if cdate not in grounded_dates:
            violations.append(f"Claimed date {cdate} is not grounded in deterministic horizon or event dates.")

    return len(violations) == 0, violations
