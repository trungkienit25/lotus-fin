"""Frappe Invoice Authorizer - Strict Fail-Closed Security Adapter.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §4.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import json
from zoneinfo import ZoneInfo
from typing import Optional, Tuple
from lotus_fin.application.port.i_read_authorizer import AuthCheckResult, IReadAuthorizerPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.infrastructure.config.invoice_actions_config import InvoiceActionsConfig


class FrappeInvoiceAuthorizer(IReadAuthorizerPort):
    """Authorizer adapter that resolves server-side context and verifies access fail-closed."""
    def __init__(
        self,
        config: InvoiceActionsConfig,
        session_user: Optional[str] = None,
        session_id: Optional[str] = None,
        site_name: Optional[str] = None,
    ) -> None:
        self._config = config
        self._session_user = session_user
        self._session_id = session_id
        self._site_name = site_name
    def _get_active_user(self) -> Optional[str]:
        if self._session_user:
            return self._session_user
        try:
            import frappe  # type: ignore
            user = getattr(frappe.session, "user", None)
            return user if user and user != "Guest" else None
        except Exception:
            return None
    def _get_session_binding(self) -> Optional[str]:
        if self._session_id:
            return self._session_id
        try:
            import frappe  # type: ignore
            sid = getattr(frappe.session, "sid", None)
            return sid if sid else None
        except Exception:
            return None
    def _get_site_name(self) -> Optional[str]:
        if self._site_name:
            return self._site_name
        try:
            import frappe  # type: ignore
            return getattr(frappe.local, "site", None)
        except Exception:
            return None
    def resolve_context(
        self,
        candidate_company: str,
        capability: str,
        client_request_id: str,
        correlation_id: str,
    ) -> Tuple[Optional[AuthorizedReadContext], AuthCheckResult]:
        # 1. Capability check against config
        if capability not in self._config.allowed_capabilities:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.FORBIDDEN,
                reason_code=ActionReasonCode.CAPABILITY_DENIED,
                denial_message="Chức năng yêu cầu không nằm trong danh sách được phép.",
            )
        # 2. Authenticated user and session check
        user = self._get_active_user()
        sid = self._get_session_binding()
        if not user or user == "Guest" or not sid:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.FORBIDDEN,
                reason_code=ActionReasonCode.AUTH_REQUIRED,
                denial_message="Yêu cầu phiên đăng nhập hợp lệ để thực hiện.",
            )

        site = self._get_site_name()
        # 3. Connection mapping check
        conn = self._config.connections.get(site) if site else None
        if not conn:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.NOT_AVAILABLE,
                reason_code=ActionReasonCode.TARGET_UNQUALIFIED,
                denial_message="Mục tiêu kết nối chưa được cấu hình hoặc không đủ điều kiện.",
            )
        # 4. Company candidate check against allowed companies
        if candidate_company not in conn.allowed_companies:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.FORBIDDEN,
                reason_code=ActionReasonCode.COMPANY_DENIED,
                denial_message="Không có quyền truy cập vào công ty được chỉ định.",
            )
        # 5. Identity injection never substitutes for a live permission interface.
        try:
            import frappe  # type: ignore
            permission = getattr(frappe, "has_permission", None)
            if not callable(permission):
                raise RuntimeError("Permission interface unavailable")
            allowed = permission("Company", ptype="read", doc=candidate_company, user=user)
        except Exception:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.NOT_AVAILABLE,
                reason_code=ActionReasonCode.TARGET_UNQUALIFIED,
                denial_message="Giao diện xác thực quyền không khả dụng.",
            )
        if allowed is not True:
            return None, AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.FORBIDDEN,
                reason_code=ActionReasonCode.COMPANY_DENIED,
                denial_message="Quyền truy cập công ty bị từ chối bởi hệ thống.",
            )

        try:
            site_timezone = frappe.get_system_settings("time_zone")
            if type(site_timezone) is not str or not site_timezone:
                raise ValueError("Missing site timezone")
            ZoneInfo(site_timezone)
        except Exception:
            return None, AuthCheckResult(is_authorized=False, status=ActionStatus.NOT_AVAILABLE,
                reason_code=ActionReasonCode.TARGET_UNQUALIFIED, denial_message="Múi giờ site chưa đủ điều kiện.")
        # Stable read-family scope; capability authorization above remains per execution.
        policy = self._config.model_dump(exclude={"signing_secret"})
        policy["allowed_capabilities"] = sorted(policy["allowed_capabilities"])
        raw_fp = json.dumps(["p1.invoice.v1", "invoice.min.v1", user, sid, site,
            conn.product_id, conn.site_id, conn.connection_id, conn.connection_version,
            candidate_company, site_timezone, policy, hashlib.sha256(self._config.signing_secret.encode()).hexdigest()],
            sort_keys=True, separators=(",", ":"))
        ctx_ver = f"ctx_{hashlib.sha256(raw_fp.encode('utf-8')).hexdigest()[:16]}"
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(milliseconds=self._config.deadline_ms)

        context = AuthorizedReadContext(
            actor_id=user,
            auth_session_binding=sid,
            site_id=conn.site_id,
            product_id=conn.product_id,
            connection_id=conn.connection_id,
            connection_version=conn.connection_version,
            company_id=candidate_company,
            capability=capability,  # type: ignore
            projection_version="invoice.min.v1",
            context_version=ctx_ver,
            observed_at_utc=now.isoformat(),
            timezone=site_timezone,
            deadline_at_utc=deadline.isoformat(),
            correlation_id=correlation_id,
            request_id=client_request_id,
            adapter_mode="ERP_READ",
        )
        return context, AuthCheckResult(
            is_authorized=True,
            status=ActionStatus.OK,
            reason_code=ActionReasonCode.CONTEXT_READY,
        )
    def authorize_document_read(
        self, context: AuthorizedReadContext, invoice_id: str
    ) -> AuthCheckResult:
        user = self._get_active_user()
        if not user or user != context.actor_id:
            return AuthCheckResult(
                is_authorized=False,
                status=ActionStatus.FORBIDDEN,
                reason_code=ActionReasonCode.ACCESS_DENIED,
                denial_message="Người dùng không khớp với ngữ cảnh được ủy quyền.",
            )
        try:
            import frappe  # type: ignore
            if hasattr(frappe, "has_permission") and not frappe.has_permission(
                "Sales Invoice", ptype="read", doc=invoice_id, user=user
            ):
                return AuthCheckResult(
                        is_authorized=False,
                        status=ActionStatus.FORBIDDEN,
                        reason_code=ActionReasonCode.ACCESS_DENIED,
                        denial_message="Không có quyền xem hóa đơn chỉ định.",
                    )
        except Exception:
            pass
        return AuthCheckResult(
            is_authorized=False,
            status=ActionStatus.NOT_AVAILABLE,
            reason_code=ActionReasonCode.CAPABILITY_DISABLED,
            denial_message="Chức năng đọc hóa đơn chưa được kích hoạt.",
        )
