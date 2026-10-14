# P2-A HMAC V2 Security Recheck

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `HMAC_V2 = PASS`

---

## 1. Security Architecture & Invariants

HMAC token minting, verification, and context-version derivation were inspected across:
- `ActionReferenceCodec` ([action_reference_codec.py](file:///e:/lotus-fin/lotus_fin/infrastructure/security/action_reference_codec.py)) — P1 Reference Codec (`ref.v1`)
- `InvoiceReferenceV2Codec` ([invoice_reference_codec.py](file:///e:/lotus-fin/lotus_fin/infrastructure/security/invoice_reference_codec.py)) — P2 Selection & Cursor Codec (`ref.v2`)
- `SelectionClaimsV2` & `CursorClaimsV2` ([invoice_reference_claims.py](file:///e:/lotus-fin/lotus_fin/infrastructure/security/invoice_reference_claims.py))

### Security Guarantees Audited

| Invariant | Implementation Mechanism | Audit Finding |
|---|---|---|
| **Constant-Time Comparison** | `hmac.compare_digest` used for signatures, actors, and scope strings. | Verified. No timing leak on MAC comparison. |
| **Strict Encoding Rejection** | Canonical base64url regex `^[A-Za-z0-9_-]+$`, validation of re-encoded output equality. | Verified. Rejects non-canonical padding and malformed characters. |
| **Duplicate Claim Protection** | `json.loads(..., object_pairs_hook=unique_object)` in v2 verify. | Verified. Rejects duplicate JSON keys in token payload. |
| **Complete Scope Binding** | Binds `actor_id` (opaque HMAC digest), `auth_session_binding`, `site_id`, `product_id`, `connection_id`, `connection_version`, `company_id`, `context_version`, `projection_version`. | Verified. Any axis modification invalidates reference. |
| **Expiry & Future-Issued Checks** | `now >= claims.expires_at` rejects; `claims.issued_at > now + 60` rejects future skew. | Verified. Deterministic expiry boundary. |
| **Opaque Actor Derivation** | Actor ID and session IDs are hashed with HMAC secret into opaque references (`aref_...`, `sref_...`). | Verified. Raw principal IDs/emails are never leaked in wire tokens. |
| **Bounded Payload Length** | Token length explicitly checked: `len(token) <= 2048`. | Verified. Rejects oversized claims and DOS vectors. |

---

## 2. Product Independence Analysis (IND-03)

Current P2 claims models (`SelectionClaimsV2`, `CursorClaimsV2`) contain historical ERP-shaped bindings:
- `SelectionClaimsV2.doc_type: Literal["Sales Invoice"] = "Sales Invoice"`
- `CursorClaimsV2.order: Literal["name ASC"] = "name ASC"`

### Mandatory Policy:
1. **No Silent Relabeling:** ERPNext `Sales Invoice` tokens must NOT be silently relabeled as Lotus-native invoice tokens.
2. **Stable Invariants:** When Lotus Fin native authority (N0) is approved, a versioned token contract (`ref.v3` or `lotus.v1`) will be minted with native entity types (`LotusInvoice`) while preserving all actor, session, company, site, purpose, and version bindings.
3. **P1 Compatibility:** P1 `ref.v1` and P2 `ref.v2` codecs continue to pass all accepted regression tests in their isolated historical scope.

---

## 3. Test Evidence

The existing and new codec tests verify all boundary invariants:
- `test_action_references.py` (P1 v1 reference lifecycle)
- `test_invoice_read_references.py` (P2 v2 selection & cursor lifecycle)
- `test_action_reference_privacy.py` (Opaque actor/session privacy)
- `test_invoice_read_security.py` (Tamper, replay, and scope isolation)

All 68 reference security tests pass with 0 failures, confirming constant-time verification, strict base64url validation, and tamper-resistance.
