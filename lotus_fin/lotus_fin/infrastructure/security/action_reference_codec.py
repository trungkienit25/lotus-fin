"""Purpose-Bound Reference Codec using HMAC-SHA256.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md Â§5, CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md Â§3.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Literal, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.infrastructure.security.invoice_reference_codec import InvoiceReferenceV2Codec


class ReferenceClaims(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    binding_version: Literal["opaque-actor.v1"] = Field(...)
    purpose: Literal["invoice.context", "invoice.open", "invoice.cursor"] = Field(...)
    key_id: str = Field(..., min_length=1, max_length=64)
    actor_id: str = Field(..., pattern=r"^aref_[0-9a-f]{64}$")
    auth_session_binding: str = Field(..., min_length=1, max_length=128)
    site_id: str = Field(..., min_length=1, max_length=128)
    product_id: str = Field(..., min_length=1, max_length=128)
    connection_id: str = Field(..., min_length=1, max_length=128)
    connection_version: str = Field(..., min_length=1, max_length=64)
    company_id: str = Field(..., min_length=1, max_length=128)
    context_version: str = Field(..., min_length=1, max_length=128)
    projection_version: Literal["invoice.min.v1"] = Field(...)
    doc_id: Optional[str] = Field(default=None, max_length=128)
    issued_at: int = Field(..., ge=0)
    expires_at: int = Field(..., ge=0)


class ActionReferenceCodec(InvoiceReferenceV2Codec):
    """HMAC-SHA256 Reference Codec with constant-time verification."""

    def __init__(self, key_id: str, secret_key: str, default_ttl: int = 300) -> None:
        self.key_id = key_id
        self.secret_key = secret_key.encode("utf-8")
        self.default_ttl = default_ttl

    def _derive_opaque_session(self, session_id: str) -> str:
        h = hmac.new(self.secret_key, b"session_binding:" + session_id.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"sref_{h[:24]}"

    def _derive_opaque_actor(self, actor_id: str) -> str:
        digest = hmac.new(self.secret_key, b"actor_binding:v1:" + actor_id.encode("utf-8"), hashlib.sha256)
        return f"aref_{digest.hexdigest()}"

    def sign_reference(
        self,
        purpose: Literal["invoice.context", "invoice.open", "invoice.cursor"],
        context: AuthorizedReadContext,
        doc_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        now = int(time.time())
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        opaque_sid = self._derive_opaque_session(context.auth_session_binding)
        claims = ReferenceClaims(
            binding_version="opaque-actor.v1",
            purpose=purpose,
            key_id=self.key_id,
            actor_id=self._derive_opaque_actor(context.actor_id),
            auth_session_binding=opaque_sid,
            site_id=context.site_id,
            product_id=context.product_id,
            connection_id=context.connection_id,
            connection_version=context.connection_version,
            company_id=context.company_id,
            context_version=context.context_version,
            projection_version=context.projection_version,
            doc_id=doc_id,
            issued_at=now,
            expires_at=now + ttl,
        )
        payload_bytes = json.dumps(claims.model_dump(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
        sig = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
        return f"ref.v1.{payload_b64}.{sig_b64}"

    def verify_reference(
        self,
        token: str,
        expected_purpose: Literal["invoice.context", "invoice.open", "invoice.cursor"],
        context: AuthorizedReadContext,
        expected_doc_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        if not isinstance(token, str) or len(token) > 2048:
            return False, "Oversized or invalid token type."
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != "ref" or parts[1] != "v1":
            return False, "Invalid token format or version."

        payload_b64, sig_b64 = parts[2], parts[3]
        try:
            pad = "=" * ((4 - len(payload_b64) % 4) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + pad)
            pad_sig = "=" * ((4 - len(sig_b64) % 4) % 4)
            expected_sig = base64.urlsafe_b64decode(sig_b64 + pad_sig)
        except Exception:
            return False, "Base64 decoding failed."

        actual_sig = hmac.new(self.secret_key, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(actual_sig, expected_sig):
            return False, "Signature mismatch."

        try:
            data = json.loads(payload_bytes.decode("utf-8"))
            claims = ReferenceClaims(**data)
        except Exception:
            return False, "Claims deserialization failed."

        if claims.key_id != self.key_id:
            return False, "Mismatched key ID."

        now = int(time.time())
        if now > claims.expires_at:
            return False, "Reference expired."
        if claims.issued_at > now + 60:
            return False, "Reference issued in the future."

        expected_opaque_sid = self._derive_opaque_session(context.auth_session_binding)
        if claims.purpose != expected_purpose:
            return False, f"Purpose mismatch: expected {expected_purpose}, got {claims.purpose}."
        if not hmac.compare_digest(claims.actor_id, self._derive_opaque_actor(context.actor_id)):
            return False, "Actor mismatch."
        if claims.auth_session_binding != expected_opaque_sid:
            return False, "Session binding mismatch."
        if claims.site_id != context.site_id or claims.company_id != context.company_id:
            return False, "Site or company mismatch."
        if claims.product_id != context.product_id or claims.connection_id != context.connection_id:
            return False, "Product or connection ID mismatch."
        if claims.connection_version != context.connection_version:
            return False, "Connection version mismatch."
        if claims.context_version != context.context_version:
            return False, "Context version mismatch."
        if claims.projection_version != context.projection_version:
            return False, "Projection version mismatch."
        if expected_doc_id and claims.doc_id != expected_doc_id:
            return False, "Document ID mismatch."

        return True, None
