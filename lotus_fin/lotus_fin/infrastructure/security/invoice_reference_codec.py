"""P2 HMAC wire/claims codec, isolated from unchanged P1 compatibility."""
import base64
import hashlib
import hmac
import json
import re
import time
from lotus_fin.infrastructure.security.invoice_reference_claims import SelectionClaimsV2, CursorClaimsV2


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate claim")
        result[key] = value
    return result


class InvoiceReferenceV2Codec:
    def _v2_scope(self, context):
        return {"key_id": self.key_id, "actor_id": self._derive_opaque_actor(context.actor_id),
            "auth_session_binding": self._derive_opaque_session(context.auth_session_binding),
            **{k: getattr(context, k) for k in ("site_id", "product_id", "connection_id",
                "connection_version", "company_id", "context_version", "projection_version")}}

    def _sign_v2(self, claims):
        payload = json.dumps(claims.model_dump(), sort_keys=True, separators=(",", ":")).encode()
        encode = lambda data: base64.urlsafe_b64encode(data).decode().rstrip("=")
        token = "ref.v2." + encode(payload) + "." + encode(hmac.digest(self.secret_key, payload, "sha256"))
        if len(token) > 2048:
            raise ValueError("Reference exceeds wire limit")
        return token

    def sign_selection_v2(self, context, doc_id, record_version, ttl_seconds=None, query_fingerprint=None):
        now = int(time.time())
        digest = query_fingerprint or hashlib.sha256(
            json.dumps([doc_id, record_version], separators=(",", ":")).encode()).hexdigest()
        claims = SelectionClaimsV2(**self._v2_scope(context), doc_id=doc_id, record_version=record_version,
            query_fingerprint=digest, issued_at=now,
            expires_at=now + (self.default_ttl if ttl_seconds is None else ttl_seconds))
        return self._sign_v2(claims)

    def sign_cursor_v2(self, context, query_fingerprint, last_id, upper_id, page_index, page_size, ttl_seconds=None):
        now = int(time.time())
        claims = CursorClaimsV2(**self._v2_scope(context), query_fingerprint=query_fingerprint,
            last_id=last_id, upper_id=upper_id, page_index=page_index, page_size=page_size,
            issued_at=now, expires_at=now + (self.default_ttl if ttl_seconds is None else ttl_seconds))
        return self._sign_v2(claims)

    def _verify_v2(self, token, context, model):
        if not isinstance(token, str) or len(token) > 2048:
            return False, None, "Oversized or invalid token type."
        try:
            prefix, version, payload64, signature64 = token.split(".")
            if (prefix, version) != ("ref", "v2"):
                raise ValueError("Wire version")
            def decode(value):
                if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
                    raise ValueError("Noncanonical encoding")
                raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
                if base64.urlsafe_b64encode(raw).decode().rstrip("=") != value:
                    raise ValueError("Noncanonical encoding")
                return raw
            payload, signature = decode(payload64), decode(signature64)
            if not hmac.compare_digest(hmac.digest(self.secret_key, payload, "sha256"), signature):
                return False, None, "Signature mismatch."
            data = json.loads(payload.decode(), object_pairs_hook=unique_object)
            required = set(model.model_fields)
            if not isinstance(data, dict) or not required.issubset(data):
                raise ValueError("Missing versioned bindings")
            claims = model(**data)
            for key, expected in self._v2_scope(context).items():
                if not hmac.compare_digest(str(getattr(claims, key)).encode(), str(expected).encode()):
                    return False, None, "Scope mismatch."
            now = int(time.time())
            if now >= claims.expires_at:
                return False, None, "Reference expired."
            if claims.issued_at > now + 60:
                return False, None, "Reference issued in the future."
            return True, claims, None
        except (ValueError, TypeError, UnicodeError, AttributeError):
            return False, None, "Invalid authenticated reference."

    def verify_selection_v2(self, token, context):
        return self._verify_v2(token, context, SelectionClaimsV2)

    def verify_cursor_v2(self, token, context):
        return self._verify_v2(token, context, CursorClaimsV2)
