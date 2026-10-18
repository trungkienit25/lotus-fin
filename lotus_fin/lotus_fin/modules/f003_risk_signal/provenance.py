"""AI003 provenance: source hashing and V2.2 observation identity (S2).

Identity rules (SSOT §16.5 + §17.4 V2-01 + §18.1):
- economic_voucher_identity = (company, voucher_type, voucher_no)
- observation_identity      = economic identity + (party_account, currency)
- count basis is the cardinality of economic_voucher_identity among eligible
  observations — separate from observation identity.
- Currency is validated/rejected BEFORE identity/dedup; same-identity conflicts
  concern payload fields not in the key (amount/due/party/type).
- No identity is ever derived from amount or due_date; no whitespace/case
  folding that could merge distinct IDs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, Mapping, Optional, Tuple

from lotus_fin.modules.f003_risk_signal.contracts import ReasonCode, Status


class SourceFailure(Exception):
    """Typed fail-closed source failure mapped onto the A1..A11 pipeline.

    ``status``/``reason_code`` are contract enums; ``message`` is sanitized
    (no raw exception text, no report row content) and may surface in safe
    debug metadata only.
    """

    def __init__(self, status: Status, reason_code: ReasonCode, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.reason_code = reason_code
        self.message = message


def sanitize_reason(exc: BaseException) -> str:
    """Map an unexpected exception to a safe error class name (no raw text)."""
    return "EXC_%s" % type(exc).__name__


def canonical_payload_hash(payload) -> str:
    """Scope-bound sha256 over canonical JSON (sort_keys, str-typed values)."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def gate_company_currency(currency: str) -> None:
    """Supported currency gate (USD or legacy VND) — must run BEFORE identity/dedup."""
    if currency not in ["VND", "USD"]:
        raise SourceFailure(
            Status.VALIDATION_ERROR,
            ReasonCode.UNSUPPORTED_COMPANY_CURRENCY,
            f"company accounting currency '{currency}' is not supported (expected USD or VND)",
        )


def economic_voucher_identity(company: str, voucher_type: str, voucher_no: str) -> Tuple[str, str, str]:
    if not company or not voucher_type or not voucher_no:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.SOURCE_INVALID,
            "AP row lacks complete voucher identity fields",
        )
    return (company, voucher_type, voucher_no)


def observation_identity(
    economic: Tuple[str, str, str], party_account: str, currency: str
) -> Tuple[str, str, str, str, str]:
    if not party_account or not currency:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.SOURCE_INVALID,
            "AP row lacks account or currency provenance",
        )
    return economic + (party_account, currency)


@dataclass(frozen=True)
class ReconciledObservation:
    """A validated, deduplicated AP observation with provenance."""

    identity: Tuple[str, str, str, str, str]
    economic_identity: Tuple[str, str, str]
    count_key: Tuple[str, str, str]
    voucher_type: str
    voucher_no: str
    party_account: str
    currency: str
    amount: Decimal
    due_date: Optional[object]
    party_ref: Optional[str]
    duplicate_count: int = 1


def parse_amount(raw: object, row_label: str) -> Decimal:
    """Finite Decimal from typed report field; malformed -> SOURCE_ERROR."""
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.SOURCE_INVALID,
            "non-numeric outstanding amount on %s" % row_label,
        ) from exc
    if not value.is_finite():
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.SOURCE_INVALID,
            "non-finite outstanding amount on %s" % row_label,
        )
    return value


def reconcile_observations(
    rows,
    company: str,
    allocation_provenance: Optional[Mapping[Tuple[str, str], bool]] = None,
) -> Tuple[ReconciledObservation, ...]:
    """Dedupe exact duplicates; fail closed on conflicts and unproved allocation.

    ``rows`` are normalized interfaces.APRow objects already currency-gated.
    ``allocation_provenance`` maps economic identity (voucher_type, voucher_no)
    to True when verified account-allocation provenance exists (schedule
    metadata bridge). Multiple account observations of one voucher without
    provenance are INCONCLUSIVE/UNSUPPORTED_ALLOCATION_SCOPE — never summed
    or silently collapsed (gold: AP_UNVERIFIED_ACCOUNT_SCOPE).
    """
    by_identity: Dict[Tuple, dict] = {}
    order: list = []
    for row in rows:
        economic = economic_voucher_identity(company, row.voucher_type, row.voucher_no)
        identity = observation_identity(economic, row.party_account, row.currency)
        content = (row.outstanding_amount, row.due_date, row.party_ref, row.voucher_type)
        existing = by_identity.get(identity)
        if existing is None:
            by_identity[identity] = {"row": row, "content": content, "duplicates": 1}
            order.append(identity)
            continue
        if existing["content"] != content:
            raise SourceFailure(
                Status.SOURCE_ERROR,
                ReasonCode.CONFLICTING_OBSERVATION,
                "same observation identity with conflicting payload fields",
            )
        existing["duplicates"] += 1  # exact duplicate: validated, deduped with provenance count

    per_voucher_accounts: Dict[Tuple[str, str], set] = {}
    for identity, entry in by_identity.items():
        key = (identity[0], identity[1], identity[2])  # (company, voucher_type, voucher_no)
        per_voucher_accounts.setdefault(key, set()).add(identity[3])
    for key, accounts in per_voucher_accounts.items():
        if len(accounts) > 1 and not (allocation_provenance or {}).get(key, False):
            raise SourceFailure(
                Status.INCONCLUSIVE,
                ReasonCode.UNSUPPORTED_ALLOCATION_SCOPE,
                "multiple account observations of one voucher without verified allocation provenance",
            )

    reconciled = []
    for identity in order:
        entry = by_identity[identity]
        row = entry["row"]
        economic = identity[:3]
        reconciled.append(
            ReconciledObservation(
                identity=identity,
                economic_identity=economic,
                count_key=economic,
                voucher_type=row.voucher_type,
                voucher_no=row.voucher_no,
                party_account=row.party_account,
                currency=row.currency,
                amount=row.outstanding_amount,
                due_date=row.due_date,
                party_ref=row.party_ref,
                duplicate_count=entry["duplicates"],
            )
        )
    return tuple(reconciled)


def distinct_voucher_count(observations) -> int:
    return len({obs.count_key for obs in observations})
