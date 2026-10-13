"""Frozen P6 integration boundary. Real write adapters are never composed here."""
from datetime import datetime, timedelta, timezone
import uuid

from lotus_fin.application.service.l4_mutation_service import L4MutationService
from lotus_fin.application.service.search_overdue_invoices import SearchOverdueInvoicesService
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.l5.models.proposals import L5TargetSpec
from lotus_fin.domain.l5.policy.engine import L5PolicyContext, L5PolicyEngine, L5_ACTION_CATALOG
from lotus_fin.infrastructure.persistence.demo_overdue_provider import DemoOverdueObservationProvider
from lotus_fin.presentation.controller.l4_mutation_controller import L4MutationController

DEMO_COMPANY = "Lotus Demo Corp"


class CopilotIntegrationService:
    def __init__(self, store):
        self.store = store

    def dispatch(self, user, roles, session_binding, site, demo_enabled, body):
        if not user or user.lower() in ("guest", "anonymous"):
            return 401, {"reason_code": "AUTH_REQUIRED"}
        if body.get("profile") not in ("CORE", "DEMO"):
            return 400, {"reason_code": "INVALID_PROFILE"}
        if body["profile"] == "CORE":
            return 503, {"reason_code": "NOT_AVAILABLE", "availability": "AWAITING_DATA",
                         "message": "Native source and write policy unapproved. N0 BLOCKED."}
        if not demo_enabled:
            return 403, {"reason_code": "DEMO_DISABLED", "availability": "DISABLED"}
        action = body.get("action")
        principal = UserPrincipal(user_id=user, roles=roles, company=DEMO_COMPANY)
        # Scope is server-derived; user-supplied actor/session/company is forbidden by API DTO.
        scope = f"{site}:{user}:{session_binding}:DEMO"
        with self.store.transaction(scope, str(action)) as (ledger, adapter):
            if action == "past_final_due":
                return 200, self.overdue(user, session_binding)
            if action == "l5_review":
                return 200, self.review_l5(user, roles, site, body.get("action_name"))
            controller = L4MutationController(L4MutationService(ledger, adapter))
            request = dict(body.get("payload") or {})
            if action == "l4_propose":
                request["simulated"] = True
                status, result = controller.propose_action(principal, session_binding, site, request)
            elif action == "l4_confirm":
                status, result = controller.confirm_action(principal, session_binding, request)
            elif action == "l4_cancel":
                status, result = controller.cancel_pending_proposal(principal, session_binding, request)
            elif action == "l4_status":
                status, result = controller.get_operation_status(principal, request)
            elif action == "l4_reconcile":
                status, result = controller.reconcile_operation(principal, request)
            else:
                return 400, {"reason_code": "UNKNOWN_ACTION"}
            # Never expose raw framework session identifiers or internal binding values.
            for key in ("proposal", "operation"):
                if result.get(key):
                    result[key]["session_id"] = "server-bound"
            result["source_label"] = "DEMO DATA (FICTIONAL) — SIMULATION ONLY"
            return status, result

    def overdue(self, user, binding):
        stamp = "2026-10-13T12:00:00+00:00"
        context = AuthorizedReadContext(
            actor_id=user, auth_session_binding=binding, site_id="site_demo",
            product_id="lotus-fin", connection_id="demo", connection_version="demo.v1",
            company_id=DEMO_COMPANY, capability="invoice.search", context_version="demo.v1",
            observed_at_utc=stamp, timezone="Asia/Ho_Chi_Minh",
            deadline_at_utc=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()), adapter_mode="DEMO_ISOLATED",
        )
        data, _, status, reason = SearchOverdueInvoicesService(
            DemoOverdueObservationProvider(), provider_mode="DEMO").execute(context)
        return {"status": status.value, "reason_code": reason.value,
                "data": data.model_dump(mode="json") if data else None,
                "source_label": "Fixed fictional observation at 2026-10-13; no native selection handle"}

    def review_l5(self, user, roles, site, name):
        definition = L5_ACTION_CATALOG.get(name)
        if not definition:
            return {"status": "DENIED", "reason_code": "UNKNOWN_ACTION_NAME"}
        target = L5TargetSpec(doctype="Sales Invoice", doc_id="DEMO-INV-001",
                              resource_version="v_demo_1", company=DEMO_COMPANY,
                              expected_docstatus=2 if "cancel" in name else 1)
        policy = L5PolicyEngine().evaluate_intent(name, L5PolicyContext(
            actor=user, actor_roles=roles, tenant_id=site, site=site,
            authorized_company=DEMO_COMPANY, target=target,
            parameters={"recipient_email": "demo@example.invalid"},
            current_resource_version="v_demo_1", current_docstatus=0))
        return {"status": "DENIED", "action_name": name, "family": definition.family.value,
                "risk_level": definition.risk_level.value,
                "required_approval_level": definition.required_approval_level.value,
                "target": target.model_dump(), "consequence_description": definition.description,
                "reason_code": "APPROVAL_PROVIDER_UNAVAILABLE" if policy.decision.value == "PERMITTED"
                               else policy.reason_code,
                "details": {"policy": policy.model_dump(mode="json"),
                            "source": "DEMO FICTIONAL POLICY REVIEW", "side_effects": "DISABLED"}}
