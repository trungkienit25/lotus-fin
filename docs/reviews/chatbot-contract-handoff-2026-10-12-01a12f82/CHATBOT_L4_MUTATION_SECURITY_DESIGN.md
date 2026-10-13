# L4 saved ERP record — mutation security design

12 October 2026 · implementation **NOT_IMPLEMENTED**; design **PROPOSED / NOT_FROZEN**; mutation capability **BLOCKED / DISABLED**. Engineering design only. No ERP method, fixture creation, migration, mutation, scheduler, deployment or flag was executed. The current task explicitly excludes them. Read [authority/decisions](CHATBOT_PROPOSAL_COMPLETION_PLAN_UPDATED.md); P1 selection references, chat “yes”, L3 Review/Copy and general frontend CRUD are never mutation approvals.

## 1. One exact operation and unresolved target semantics

**Only proposed operation:** `erp.create_invoice_followup_task_draft.v0.1`, implemented eventually by dedicated Lotus application business method `create_invoice_followup_task_draft_v1`. **Only target DocType:** ERPNext **Task**. Dedicated adapter internally constructs one Task and calls its normal **`insert()`** lifecycle, with no `ignore_permissions`, direct SQL business write, generic `frappe.client.insert`, arbitrary update/delete/submit/cancel or caller-selected method. Source Sales Invoice is read only.

The original proposal mentions Task only as an example; **installed Task/Project schema, permissions, hooks and company isolation have not been qualified here**. Proposed mandatory Project binding is required because a Task cannot be assumed to have direct Company scope. Server verifies selected existing Project belongs to the source invoice's exact authorized Company, current user may read/use that Project, and current Task create/field permissions allow the proposed fields. If Project cannot establish enforceable Task company isolation, the candidate is **BLOCKED**, not substituted with Comment/ToDo/custom DocType.

Proposed fixed Task fields:

```text
subject = "Invoice follow-up review"
description = canonical escaped plain text:
  "Review the selected invoice and confirm the next follow-up step."
status = "Open"
priority = "Low"
project = server-resolved exact authorized Project identity
lotus_followup_operation_id = server-generated unique operation UUID
docstatus = 0 (assert after normal insert; do not bypass lifecycle)
```

`lotus_followup_operation_id` is a **proposed NEW unique immutable custom field**, requiring separate schema/migration/security approval; it does not exist by assertion. It is an operational dedup marker, not a second financial ledger. No invoice balances, due dates, customer names/emails, assignee, notification, payment mandate or free L3 editor content is written. Source invoice linkage/version stays in the restricted operation ledger; no arbitrary Task reference field is invented. `description` field type/encoding must be qualified; for rich-text fields render a fixed canonical escaped text representation, no model/user HTML.

Task is commonly a non-submittable operational record; this must be confirmed for the installed target. A saved `Open` Task with docstatus0 is **persisted ERP state**, not necessarily a formal ERP “Draft” lifecycle. Review UI must say **“Create one saved Open Task in ERP”** once metadata is qualified. If Product requires a genuinely submittable Draft DocType, stop and obtain a different operation contract; do not rename this Task to “invoice draft”. No approved mutation target or contract currently exists.

## 2. Server proposal and exact review surface

Server-owned immutable proposal object (restricted durable store, not client JSON authority):

```text
proposal_id, schema_version, capability, business_method_version
actor_binding, auth_session_binding, site/product/connection/version
authorized_company, policy/security/permission_epoch
source = {doctype:"Sales Invoice",name,modified,read_projection_version,
          source_fingerprint}
project = {doctype:"Project",name,modified,company,scope_fingerprint}
target = {doctype:"Task",identity:null,operation_id,proposed_docstatus:0}
args = fixed fields above (including resolved project and operation_id)
canonical_args_hash, review_projection_hash, created_at, expires_at
state = PROPOSED|APPROVAL_RESERVED|CONSUMED|REJECTED|EXPIRED|INVALIDATED
```

Proposal storage is itself a persistent internal-state action with privacy/retention approval; proposing creates **no Task**. Trusted actor/session/site are the authenticated request, never client/LLM. Exact Company ownership is checked independently of text, selected Project and service credentials. No service-account/Administrator elevation. Connection remap/version, policy/template/security revision or session/logout epoch change invalidates proposal. Proposed expiry120seconds; no refresh on retry. Numbers here require explicit Security/Product approval, not inferred P1 TTL reuse.

Proposed request to the dedicated proposal endpoint contains only strict version, UUIDv4 request_id, current authorized source selection handle and separately issued authorized Project selection handle. If authorized Project picker/handle capability does not exist, proposal is unavailable; generic project IDs cannot fill the gap. Neither handle grants create authority. Reject extra args/fields/method/URL/company/recipient/body/reflection instructions. Proposed commit request contains strict version, proposal opaque ID, one-use review challenge, stable server-issued idempotency key, current request_id and the framework CSRF token via the approved header. No editable payload at commit. Proposed args changes require a new server proposal/challenge; no mutation of previous proposal.

Review UI shows **all** exact written fields, operation/method/version, selected Project/company, selected source invoice identity/version, site/connection label, proposed Task Open/docstatus0, and consequence “one saved ERP Task”. It shows no balances/overdue/recipient claim. Readable source labels are individually authorized. Present **Confirm create Task** and **Discard**. Confirmation is a separate authenticated UI event after review; textual “yes”, model tool call or L3 Copy cannot trigger it. Body hash/review projection binds exact displayed bytes/normalization; mismatch blocks commit. No unreviewed hidden assignee/queue/mail flags or timestamp-dependent business defaults. Framework owner/creation/naming defaults must be disclosed as system generated and qualified; audit their final canonical projection.

Challenge is random, one use, high entropy, stored hashed server-side and bound to proposal/hash/current principal/session/site/company/connection/expiry. Never use a public decodable selection token as approval. An injected script under the app's origin can fake ordinary UI events; event labels alone are not strong user-presence proof. Harden reviewed UI/session/CSP and, if required by risk policy, a separately qualified step-up/user-presence challenge. Do not claim browser “isTrusted” authenticates consent.

## 3. Fresh commit authorization and CSRF

Commit endpoint is authenticated **POST only**, Guest/disabled user/token-as-browser-session fallback denied; framework session must be live and match proposal. Require valid framework CSRF secret/header bound to that session, same-origin Origin and Fetch Metadata where available, secure session cookie settings and qualified middleware. Origin alone, request_id, MAC or chatbot context are not CSRF protection. No CORS write egress, GET mutation or arbitrary remote origin. Real session/logout/multiworker behavior requires ordinary-user tests.

Immediately before insertion, under operation/proposal locks, resolve current principal/company/connection; check Task **create**, target field write/create permlevels/masking, Company read/use authority, Project permissions/company/version and source Sales Invoice document/field rights/version. Review-visible labels must still be readable. Role/document/Project policy revocation must fail closed; no cached role grant or Admin helper. Authorization framework unavailable → unavailable without write. Wrong session/actor/site/company/purpose/expired/reused approval denies before Task construction.

Recheck source and Project versions at the write boundary. Lock or otherwise qualify source/project reads and version consistency in the same transaction. Invoice modification means stale proposal; prepare again, never silently use changed args. For this fact-free task, settlement is not used to authorize debt collection; no overdue/eligible-payment condition is implied. If future content/business eligibility depends on residual, add a settlement revision/fingerprint contract; `modified` alone is insufficient.

Role policies outside lockable ERP rows can change between authorization and commit. Require a tested permission epoch/locking strategy or explicitly accepted narrower revocation linearization boundary; no magical atomic-RBAC claim. If immediate revocation cannot meet the approved gate, remain BLOCKED. Never hold a user permission override across transactions or set a global active user.

## 4. Durable deduplication, concurrency and transaction protocol

The operation ledger is an **operational authorization/outcome ledger**, no accounts or financial truth. Proposed storage: one dedicated application DocType/table with restricted access, durable backups and transactional support; schema/migration/retention are NOT_APPROVED. Unique constraints on `(site, capability_version, operation_id)` and approval/proposal consumption, plus Task unique `lotus_followup_operation_id`. Hash-bound stable idempotency key generated by server on proposal, never client UUID or LLM string. Same key/different args/principal/company → reject; no overwriting.

Ledger fields: scoped opaque owner/session bindings, proposal/hash/source/Project versions, operation key hash, state, attempt lease/fencing counter, target DocType/name/version (restricted), started/ended times, fixed failure class, reconciliation state and redacted CID audit links. Never full free text, credentials, CSRF/challenge/signing refs or customer financial values. Raw target IDs require restricted permission and are not general telemetry.

**A. Reserve:** authenticate/validate approved proposal+review challenge; atomically reserve one operation and consume approval against that operation, committing the reservation durably before business execution. Approval never authorizes a second operation. Reservation has short lease; proposed30seconds/fencing semantics need DB qualification. An operation whose deadline expires can remain reserved for reconciliation; expiry must not authorize fresh execution.

**B. Execute:** acquire DB-backed row lock/fencing ownership; reread reservation/proposal, reauthorize fresh as §3, verify expiry (first execution only), args/hash/source/Project versions, audit readiness. In one qualified ERP database transaction: normal Task.insert lifecycle → assert final fields/docstatus/project/company linkage/operation marker → atomically mark ledger COMMITTED with exact target identity/version → insert required durable terminal audit event. Commit once. No implicit/nested business commit in hooks. Unique key/row-lock/fencing controls must work across actual workers, not one Python mutex/Redis lease.

**C. Finish:** only after known committed Task+ledger+terminal audit is verified, return `COMMITTED`. If transaction rollback is proven, record FAILED_ROLLED_BACK/REJECTED and terminal failure audit in a subsequent safe operational transaction. Approval remains consumed; another operation requires new proposal/review. A definitive permission/stale/validation denial creates no Task. A reservation that expires without execution is terminal EXPIRED with audit, no automatic reschedule.

|Situation|Required behavior|
|---|---|
|Double-click / concurrent same operation|One lock/reservation/insertion. Second request returns IN_PROGRESS or current authorized committed outcome; never inserts again|
|Different idempotency key for same already consumed proposal|Deny; unique proposal-operation consumption prevents bypass|
|Duplicate key with changed args/source/principal/site|Deny/replay-conflict, not cached success|
|Duplicate request after known COMMITTED|Fresh authority to view result, same target/outcome; no business method rerun. Revoked access gives generic denial|
|Worker crash before business transaction|Durable RESERVED state and consumed approval; recovery can classify expired/not-executed; no unreviewed new operation|
|Crash during transaction / rollback|DB transaction should remove Task and COMMITTED marker together. Verify actual rollback and hooks; consumed reservation remains for audit|
|Timeout/lost acknowledgment after possible commit|Client receives/retains **UNKNOWN_OUTCOME**; it never treats timeout as failure-to-write or blindly retries creation|
|Lease expiry/second worker|Fencing+DB locks+unique Task key prevent two commits; expired lease alone never proves first worker stopped|
|Framework commits independently / external hook effects|Reject this target/architecture until repaired and requalified; atomic ledger design cannot compensate automatically|

No exactly-once marketing claim: this design aims for at most one durable Task per approved operation under qualified transaction/uniqueness assumptions. Transport responses/audit forwarding can repeat. No raw retries for `insert()` on network timeout or uncertain DB connection. Only same-operation status retrieval is safe after ambiguity.

## 5. UNKNOWN_OUTCOME and reconciliation

Keep **business ledger state** separate from **client observation**. DB may already say COMMITTED while the client says UNKNOWN_OUTCOME. An inaccessible DB cannot reliably persist an UNKNOWN marker; record uncertainty through the available safe delivery audit and reconcile later. Never overwrite a committed result with timeout failure. `request_id` traces attempts; `operation_id` identifies one immutable operation; neither a browser abort nor UI reset rolls back a server commit.

Dedicated authenticated status/reconcile method reads only this operation under fresh owner/site/company permissions. Under DB operation lock, inspect ledger and Task unique operation marker plus source-linked expected args/hash:

1. Ledger COMMITTED + exactly one matching Task + required terminal audit → current authorized COMMITTED; verify record was not modified/deleted. A later edit/delete is an explicit current record state, not a reason to recreate it.
2. Proven fully rolled-back/never-executed operation with no Task under qualified transaction boundary → FAILED_ROLLED_BACK/EXPIRED; request fresh proposal/review for any new create. Absence in one query during another live transaction is not proof.
3. Ledger RESERVED/EXECUTING and active worker/lock → IN_PROGRESS; poll bounded status, no create retry.
4. Task exists but ledger/audit mismatch, multiple targets, hooks partially committed, or uncertain lock/connection state → REVIEW_REQUIRED/UNKNOWN_OUTCOME, stop automatic mutation. Restricted operator reconciles using operation ID/CID; do not expose hidden target or silently delete/undo Task.

Recovery worker design is restricted operational reconciliation, not an autonomous chatbot action or repeated financial job. Its implementation/credential/scope/retention must be separately approved. No scheduler/jobs created here. Result reads after logout/context switch require new authenticated session and explicit current operation-history access; old approval/challenge/session/idempotency response cannot cause a write. No replay after user/site/company switch. If operation history read permission is absent, give generic unavailable/denied with safe support CID.

## 6. Audit, hooks and failure boundaries

Required terminal security/business audit has operation/proposal opaque IDs, safe CID, actor/company/site bindings, action/policy/source/args hash version, terminal state, duration and protected target ref. Durable audit event and COMMITTED ledger occur in **the same transaction**; audit persistence failure rolls back Task. A later external audit sink forwarding failure is **AUDIT_DELIVERY_PENDING**, not a fabricated rollback or reason to reinsert Task; do not report fully qualified completion until required delivery semantics are met. Same-DB durable audit plus outbox delivery is a proposed infrastructure design requiring sink/ACL/retention/health approval, not an assumed existing P1 StreamHandler guarantee.

All request exits get one redacted terminal attempt per request/CID; one business operation terminal event, deduplicated durably, is a distinct audit level. IN_PROGRESS/UNKNOWN_OUTCOME transport events do not claim business finality. Denial/invalid payload logs contain no full body/ref/token. If audit unavailable before execution, deny new mutation; if DB committed and sink later fails, retain exact committed outcome for reconciliation and make audit failure visible. Do not hide successful Task creation behind an ordinary error encouraging another create.

Normal ERP validation/controllers/hooks/notifications must be catalogued on the exact installed site. Target field metadata, mandatory fields, autoname, project/status rules, DocType permissions, field permlevels, server scripts, assignments, version logs and transactional notification behavior all qualify independently. No blanket `ignore_mandatory`, skipped hooks, explicit database commit inside adapter, third-party credentials or service-account mutation. Any email, bank/payment, autonomous job or nontransactional external side effect discovered in Task hooks blocks this candidate until a separate scope decision and isolated proof; do not silently disable system hooks to get a PASS.

Cleanup/reversal: snapshots/baselines and fixture-approved normal ERP cleanup only on a named private site. No production auto-delete as compensation. Actual rollback success includes Task, operational ledger/audit consistency, framework hook state/queue/mail and child/Version writes; ledger reservation/audit may intentionally remain. If business hook commits early, a DB rollback is insufficient. Site lifecycle cannot be inherited from shared frontend/AI003 sites. No ERP fixture/cleanup operations in this task.

## 7. Threat model and independent acceptance

|Threat|Attack|Controls and decisive ordinary-user negative|
|---|---|---|
|Confused deputy|LLM/client picks foreign company/source/Project or uses elevated generic CRUD|One exact method/DocType/fields; current session identity; fresh Company/source/Project/create rights. U-A/Company B and unauthorized Project →0Task, no existence|
|Replay|Captured approval reused after expiry/logout/mapping change; alternate key bypass|One-use hashed challenge, session/site/company/hash binding, durable unique proposal consumption. Replay and multi-tab/multiworker tests create0additionalTask|
|Stale proposal|Invoice/Project/schema/policy/args changes after review|Immutable hash+versions, new proposal on edits, fresh checks under transaction. Stale denial preserves0Task|
|TOCTOU|Role revoked between review/check/insert; duplicate worker acquires stale lease|Qualified permission epoch/locks/linearization; DB fencing+uniqueness. Real revoke race must satisfy recorded policy or block|
|Prompt/HTML injection|Invoice text/chat/L3 editor says “send/pay” or overrides method|Fixed args/no untrusted content, escaped exact review, no tool dispatcher/free body. Injected data never changes fields/side effects|
|Partial commit|Hook commit, process crash, lost DB reply, external audit failure|Atomic Task+ledger+terminal audit, normal qualified hooks, UNKNOWN_OUTCOME/reconcile. Fault after commit yields1Task and same outcome, no retry insertion|
|Session/CSRF|Forged POST/origin/guest/disabled user/client-called commit|Real framework CSRF/session checks + binding;0Task, safe denied audit|
|Result/privacy leakage|Replayed operation status or foreign target label; logs contain challenge/raw invoice|Fresh result auth, restricted audit/ledger, null-data denial, sentinel tests; no signed refs/secrets in client/logs|

Minimum future fixtures: non-Administrator **U-A allowed**, **U-B denied company**, **U-C source read but no Task create**, **U-D Task create but denied Project/field**, disabled/revoked user, and two isolated companies with distinct Projects/invoices. Bind independently reviewed permission matrix and expected writes before builder implementation. Administrator setup, if approved for fixture creation, is not execution/permission evidence.

Acceptance cases: exact fields/normal ERP validation; wrong/missing/extra args; CSRF absent/wrong/stale/cross-origin/GET/Guest; changed source/project/version/policy; field/read/create/role revoke at each boundary; two-worker duplicate/double-click; proposal replay with alternate operation key; crash after reservation/before insert/before commit/after commit-before-response; unique-key contention/lease expiry; audit preflight/write/forward failure; timeout reconciliation/multiple target mismatch; source fields unchanged; no email/job/payment; logout/connection/company switch and late UI success clearing; ledger/audit ACL/retention/recovery. All **DESIGNED / NOT_RUN**.

## 8. Smallest future batches and release blockers

1. **L4-G0, metadata/contract only:** owner explicitly approves Task-via-Project choice, Open/docstatus meaning, exact fields+unique custom marker, normal hooks/no-email/no-jobs, permissions/company scope, source/project-picker contract, retention/120sTTL/30slease and reviewed target baseline. No mutation yet. Missing schema/Project isolation means BLOCKED.
2. **L4-D1, only after mutation design approval:** offline immutable proposal/state-machine/dedup/reconciliation abstractions and independent fault gold under `domain/schema/task_draft_proposal.py`, `domain/model/draft_operation.py`, `application/port/i_draft_operation_store.py`, `application/service/propose_task_draft.py`, `application/service/commit_task_draft.py`, `application/service/reconcile_task_draft.py`; focused tests. All NEW/proposed, <200 lines/cohesive ownership. No production executor or unrestricted CRUD.
3. **L4-S1, separately authorized private-site mutation batch:** approved migrations/Task unique marker/ledger/audit schema, dedicated Task adapter and transactional operation store, exact HTTP/CSRF delivery and review UI, approved non-Administrator fixtures. Freeze an exact source allowlist after actual metadata; no speculative current filenames imply ready dispatch. Independent multiworker/fault/security/rollback tests mandatory.

Demo now: disabled-action review design only; no “saved” success simulation presented as capability. Release blockers: all above decisions, real create/field/company/CSRF/revocation/hook/unique/transaction/fencing/audit/recovery proofs, exact final-field review, ordinary-user tests, artifact/site lineage and separate release approval. Generic read/P2 or L3 acceptance cannot close these gates. L5 remains disabled even if this single L4 operation is later accepted.
