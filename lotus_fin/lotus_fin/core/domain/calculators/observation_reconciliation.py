"""Observation identity reconciliation for ledger report rows (PB-DATA-02).

A source observation is identified by its voucher identity (`voucher_no` or
`name`, already enforced fail-closed by the parsers). Rows sharing one
identity are reconciled before any summation or obligation construction:

- exact duplicate observations (identical content) collapse to a single
  observation so a repeated row can never double-count, with an audit note;
- distinct contents stay separate observations only when each pair differs
  in at least one allocation discriminator field (payment terms, account, or
  due date) — legitimate payment-term/account allocations remain distinct;
- contents that differ without any allocation discriminator are ambiguous
  (the same voucher claiming two different financial contents) and fail
  closed through the caller's typed source error.
"""

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Tuple

# Fields that legitimately distinguish multiple observations of one voucher
# (installment schedules / account-level allocations). A content difference
# confined to the amount alone is a conflict, not an allocation.
ALLOCATION_DISCRIMINATOR_FIELDS = (
    "payment_terms",
    "payment_term",
    "payment_terms_name",
    "party_account",
    "account",
    "account_name",
    "due_date",
)


def observation_identity(row: Dict[str, Any]) -> str:
    """Voucher identity of a validated report row (`voucher_no` / `name`)."""
    return str(row.get("voucher_no") or row.get("name") or "").strip()


def _canonical(value: Any) -> str:
    """Canonical text form: numerically-normalized for amounts, plain for text."""
    if value is None:
        return ""
    try:
        return str(Decimal(str(value)).normalize())
    except (InvalidOperation, ValueError):
        return str(value)


def content_signature(row: Dict[str, Any]) -> str:
    """Deterministic full-content signature of a report row."""
    canonical = {key: _canonical(val) for key, val in row.items()}
    return json.dumps(canonical, sort_keys=True, default=str)


def _differs_in_discriminator(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    for field in ALLOCATION_DISCRIMINATOR_FIELDS:
        if _canonical(left.get(field)) != _canonical(right.get(field)):
            return True
    return False


def reconcile_observations(
    rows: List[Dict[str, Any]],
    source_label: str,
    error_factory: Callable[[str], Exception],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Reconcile validated report rows by observation identity.

    Returns (deduplicated rows in original order, audit notes). Raises
    error_factory(...) when same-identity rows carry conflicting financial
    content without an allocation discriminator. Rows must already carry
    voucher identity (the parsers raise on voucher-less rows before this).
    """
    first_seen: Dict[Tuple[str, str], int] = {}
    duplicated_identities = set()
    for index, row in enumerate(rows):
        key = (observation_identity(row), content_signature(row))
        if key in first_seen:
            duplicated_identities.add(key[0])
        else:
            first_seen[key] = index

    kept = [
        row
        for index, row in enumerate(rows)
        if first_seen[(observation_identity(row), content_signature(row))] == index
    ]

    notes: List[str] = []
    for identity in sorted(duplicated_identities):
        notes.append(
            f"{source_label}: exact duplicate observation '{identity}' "
            "deduplicated; counted once."
        )

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in kept:
        groups.setdefault(observation_identity(row), []).append(row)

    for identity, group_rows in groups.items():
        if len(group_rows) < 2:
            continue
        for i in range(len(group_rows)):
            for j in range(i + 1, len(group_rows)):
                if not _differs_in_discriminator(group_rows[i], group_rows[j]):
                    raise error_factory(
                        f"{source_label} observation '{identity}' has conflicting "
                        "duplicate rows without an allocation discriminator; "
                        "source data is ambiguous."
                    )

    return kept, notes
