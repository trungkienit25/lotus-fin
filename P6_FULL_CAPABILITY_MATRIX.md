# Integrated capability matrix

| Capability | CORE | Explicit DEMO | Authority / effect |
|---|---|---|---|
| L0 explanation/clarification | READY | READY | Bounded local explanation; no finance assertions |
| L1 invoice search | AWAITING_DATA | DEMO_ONLY | Existing isolated synthetic provider; explicit source badge |
| L2 selection/read | AWAITING_DATA | DEMO_ONLY | Explicit selection and current instance handle; no guessed target |
| L3 prepare/edit/review/copy/discard | READY after verified login | READY | Local unsaved/unsent draft, absolute TTL; explicit transfer to L4 |
| L4 proposal/confirm/track | AWAITING_DATA | DEMO_ONLY when server enables | Isolated audit/receipt transaction; SIMULATED_SUCCEEDED only |
| L4 native write | DISABLED | DISABLED | N0 BLOCKED; real adapter never composed |
| L5 policy/approval review | DISABLED | DEMO_ONLY | Typed policy evaluation and denial/unavailable approval status |
| L5 real side effects | DISABLED | DISABLED | No send, payment, submit, cancel or scheduler route |
| V1 PastFinalDue | AWAITING_DATA | DEMO_ONLY | Actual predicate over fixed fictional observations |
| Native V1 drilldown | UNAVAILABLE | UNAVAILABLE | No qualified native source or signed V1 selection handle |
| Unverified/revoked actor | AWAITING_PERMISSION | AWAITING_PERMISSION | Protected controls/state invalidated |
| Audit/store/transport failure | UNAVAILABLE | UNAVAILABLE | No success receipt returned |

READY, DEMO_ONLY, AWAITING_DATA, AWAITING_PERMISSION, DISABLED and UNAVAILABLE are distinct. DEMO profile selection requests a simulator; it cannot enable an execution adapter or approve native policy.
