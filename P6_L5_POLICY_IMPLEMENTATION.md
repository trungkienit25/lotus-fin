# LOTUS FIN P6-2: L5 POLICY IMPLEMENTATION

## 1. Server-Side Policy Engine Structure

The server policy engine is implemented in [`lotus_fin.domain.l5.policy.engine`](file:///e:/lotus-fin/lotus_fin/lotus_fin/domain/l5/policy/engine.py).

### Evaluation Checks (Fail-Closed Execution Pipeline)

1. **Catalog Registration**:
   Verifies `action_name in self.catalog`. Unknown actions return `DENIED` with `UNKNOWN_ACTION_NAME`.

2. **Capability / Approval Level Qualification**:
   If an action's approval level is `BLOCKED_DISALLOWED`, returns `CAPABILITY_DISABLED`.

3. **Tenant & Company Isolation**:
   Matches `context.authorized_company == context.target.company`. Cross-tenant attempts return `COMPANY_MISMATCH`.

4. **Role Permission Enforcement**:
   Validates that the authenticated actor holds at least one role specified in `action_def.required_roles`.

5. **Target DocType Integrity**:
   Confirms `context.target.doctype in action_def.allowed_source_doctypes`.

6. **Resource Freshness (Optimistic Concurrency)**:
   Asserts `context.current_resource_version == context.target.resource_version`. Stale versions return `STALE_RESOURCE_VERSION`.

7. **DocStatus Transition Validation**:
   Checks whether the requested target transition is allowlisted in `action_def.allowed_transitions`.

8. **Domain Allowlists (Email Actions)**:
   Extracts recipient email domain and verifies membership in `action_def.recipient_domain_allowlist`.

9. **Financial Guardrails (Payment Requests)**:
   Ensures amounts are strictly positive, below `max_amount`, and within `allowed_currencies`.

---

## 2. Dynamic Policy Context

```python
class L5PolicyContext(BaseModel):
    actor: str
    actor_roles: List[str]
    tenant_id: str
    site: str
    authorized_company: str
    target: L5TargetSpec
    parameters: Dict[str, Any]
    current_resource_version: str
    current_docstatus: int
```

All evaluations are stateless and deterministic, preventing side-channel leaks or cross-request pollution.
