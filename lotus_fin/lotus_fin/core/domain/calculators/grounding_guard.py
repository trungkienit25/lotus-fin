from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Set, Tuple

DEFAULT_TOLERANCE = Decimal("0.05")


def sanitize_text(text: str) -> str:
    """Sanitizes text against XSS injection, canary leaks, and dangerous script tags."""
    if not isinstance(text, str):
        return str(text)
    cleaned = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'onerror\s*=', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'onload\s*=', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def extract_numbers(text: str) -> List[Decimal]:
    """
    Extracts all candidate numbers from prose.
    cleaned = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', text)
    cleaned = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', '', cleaned)
    cleaned = re.sub(r'\b(20[1-3][0-9])\b', '', cleaned)

    cleaned = re.sub(r'^\s*\d+[\.\)]\s*', '', cleaned)
    tokens = re.findall(r'-?\d+(?:,\d+)*(?:\.\d+)?', cleaned)
    numbers: List[Decimal] = []
    for tok in tokens:
        raw_str = tok.replace(',', '')
        try:
            val = Decimal(raw_str)
            numbers.append(val)
        except InvalidOperation:
            continue
    return numbers


class GroundingGuard:
    """
    Validates numeric grounding invariant INV-GROUNDING.
    Ensures LLM synthesis does not fabricate hallucinated financial metrics.
    """

    @staticmethod
    def collect_allowed_numbers(snapshot: Dict[str, Any]) -> Set[Decimal]:
        """Gathers all verified numbers from snapshot metrics and comparison points."""
        allowed: Set[Decimal] = set()

        # Handle list or dict format metrics
        metrics = snapshot.get("metrics")
        if isinstance(metrics, list):
            for m in metrics:
                val = m.get("value")
                if val is not None:
                    GroundingGuard._expand_number(Decimal(str(val)), allowed)
        elif isinstance(metrics, dict):
            for m in metrics.values():
                val = m.get("amount") or m.get("ratio") or m.get("value")
                if val is not None:
                    GroundingGuard._expand_number(Decimal(str(val)), allowed)

        # Comparison metrics
        comp = snapshot.get("comparison")
        if isinstance(comp, dict) and comp.get("metrics"):
            for comp_m in comp["metrics"].values():
                for key in ["current", "previous", "absolute_change", "relative_change"]:
                    val = comp_m.get(key)
                    if val is not None:
                        GroundingGuard._expand_number(Decimal(str(val)), allowed)

        return allowed

    @staticmethod
    def _expand_number(val: Decimal, allowed: Set[Decimal]) -> None:
        try:
            allowed.add(val)
            allowed.add((val * 100).quantize(Decimal("0.01")))
            allowed.add((val * 100).quantize(Decimal("0.1")))
            allowed.add((val * 100).quantize(Decimal("1")))
            allowed.add(val.quantize(Decimal("1")))
        except Exception:
            pass

    @classmethod
    def verify(
        cls,
        prose_blocks: List[str],
        allowed_numbers: Set[Decimal],
        tolerance: Decimal = DEFAULT_TOLERANCE
    ) -> Tuple[bool, List[str]]:
        """
        Verifies that every number mentioned in prose matches an allowed number within tolerance.
        Returns (is_valid, list_of_errors).
        """
        errors: List[str] = []
        for block in prose_blocks:
            for num in extract_numbers(block):
                matched = any(abs(num - allowed) < tolerance for allowed in allowed_numbers)
                if not matched:
                    errors.append(f"Ungrounded number '{num}' detected in text: '{block[:80]}...'")

            lower = block.lower()
            if "guaranteed profit" in lower or "tax exempt" in lower:
                errors.append(f"Prohibited non-grounded claim detected: '{block[:80]}'")

        return (len(errors) == 0, errors)
