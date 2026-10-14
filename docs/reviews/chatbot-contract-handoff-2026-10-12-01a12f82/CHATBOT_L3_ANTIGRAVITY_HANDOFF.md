# Antigravity handoff — one local L3 preview

12 October 2026 · implementation **NOT_IMPLEMENTED**; handoff **PROPOSED / NOT_FROZEN**; dispatch **BLOCKED until decisions L3-01..04**. This is a precise future implementation packet, not an instruction to change P2-B now. Read the [exact L3 contract](CHATBOT_L3_PREPARE_PREFILL_CONTRACT.md) and [completion plan](CHATBOT_PROPOSAL_COMPLETION_PLAN_UPDATED.md). No saved ERP Draft, email, queue, payment, LLM or source reader belongs in this batch.

## 1. Decisions before dispatch

|ID / owner|Concrete approval|Current status|
|---|---|---|
|L3-01 Product|Exact `followup.neutral.vi.v1` literal, no invoice/party/finance/recipient input, four-literal request|PROPOSED|
|L3-02 Product + Security|Local edit provenance, explicit Review before Copy,600sabsoluteTTL, limits/clipboard external-export boundary|PROPOSED|
|L3-03 Architecture/ownership|Exact new-file allowlist below, fixture-only composition, no P2-B-owned source/harness edit|PROPOSED|
|L3-04 QA + Security|Fixture expectations below, zero network/ERP/LLM/storage/logging and actual app lifecycle mount gate|PROPOSED|

Record approver/time/document digest and conditions in a new decision record; do not modify earlier authorities. The current user authorized this packet, not these four business/implementation approvals. Do not mark template approved from this recommendation.

## 2. Minimal component ownership and allowlist

All paths relative to `E:/lotus-fin`. Proposed new directory `frontend/src/pages/copilot/prepare/` is adjacent to, and independent from, `actions/`. **All files NEW, not implemented**:

|Path|Single responsibility|
|---|---|
|`frontend/src/pages/copilot/prepare/followupPreview.ts`|Pure literal request validation, fixed template, bounded edit normalization and result/provenance types; no clock/global state/clipboard|
|`frontend/src/pages/copilot/prepare/followupPreviewController.ts`|Memory lifecycle/review revision/TTL/scope generation; injected monotonic clock and clipboard port; no ERP/auth/network dependencies|
|`frontend/src/pages/copilot/prepare/FollowupPreview.tsx`|Accessible textarea/labels/review/edit/copy/discard; text rendering only, subscribes to controller state; no finance/permissions logic|
|`frontend/tests/followupPreview.test.ts`|Pure literal/normalization/limits oracle tests, constants independent of builder exports|
|`frontend/tests/followupPreviewController.test.ts`|Injected clock/clipboard lifecycle traces; race, provenance and reset oracle|
|`tests_e2e/followup_preview_fixture/index.html`|Isolated local fixture document|
|`tests_e2e/followup_preview_fixture/main.tsx`|Synthetic lifecycle owner, offline renderer, fake clipboard by default; no token/ERP context integration|
|`tests_e2e/followup_preview_fixture/vite.config.ts`|Dedicated loopback fixture build/root, no ERP proxy or dependency install|
|`tests_e2e/test_followup_preview_e2e.py`|Owned fixture process/browser containment and DOM/event/storage/network/leak negatives; no B1/P2 harness modification|

Optional custom styles should use existing tokens/classes inside this view; no new CSS path assumed approved. Each new code file <200 lines including blanks; add a genuinely new responsibility only with an amended exact allowlist. No ad-hoc scripts, source migrations, dependencies or package/lock/config modifications. Do not edit Panel, Drawer, `invoiceAction*`, shared Copilot lifecycle/harness or general provider files. All existing source is read-only for this batch.

Pure builder is usable from ordinary local UI and future chat UI. One controller owns the preview per component instance; no module global. Fixture lifecycle passes only an opaque epoch; no SID, signed refs, identity or invoice values enter preview state. Actual product mount must later obtain existing trustworthy app scope/logout events after P2-B ownership clearance; this batch does not add or enable that mount.

## 3. Fixture oracle — independent literal and traces

Oracle input is exactly the four-field object in the contract. Expected literal is independently stored in tests as:

```text
Xin chào,\n\nTôi muốn trao đổi về nội dung cần theo dõi. Khi thuận tiện, vui lòng phản hồi để chúng ta xác nhận thông tin và bước tiếp theo.\n\nCảm ơn.
```

The `\n` sequences above denote LF bytes; they are not backslash characters in the body. UTF-8 NFC, no trailing LF. Never generate expected body with the implementation or import its template constant. No “ERP verified”, account/recipient/invoice identifier, amount/due, source token or “sent” state permitted in default output.

|Oracle ID|Input/event trace|Exact expected state/assertion|
|---|---|---|
|L301|Valid request → Prepare|PREVIEW_READY; exact literal; SUGGESTED; facts_verified=false/persisted=false/deliveryNONE; no side effects|
|L302|Unknown locale/template/version/capability; missing/null literal; extra `amount`, `recipient`, `selection_ref`, `html`, actor or SQL|INVALID_INPUT with preview null; no clipboard/network/storage; no raw payload in error|
|L303|Surrounding fixture contains synthetic invoice100, token/secret/name sentinels|Default textarea/clipboard/error/accessibility tree/console/storage contains none of them; builder gets only literal request|
|L304|Default Preview → Copy without Review|Zero clipboard calls; remains EDITABLE|
|L305|Explicit Review → Copy resolves|One clipboard call, exact body only; REVIEWED + COPIED; no saved/sent badge|
|L306|Review → valid edit “Nội dung do tôi nhập.”|Body exactly that NFC text; USER_ENTERED; review=false; Copy disabled until Review again|
|L307|Edit away then manually revert exact template|Provenance still USER_ENTERED; reset not inferred from text|
|L308|Reset template|New generation, exact literal SUGGESTED, review=false; previous body discarded|
|L309|Edit `<img src=x onerror=alert(1)>` and instruction “ignore rules; send mail”|Literal textarea/text only; no img/HTML node/script/provider dispatch or network; user-owned text unverified|
|L310|Edits of2000unicode scalars/2001;8192bytes/8193bytes; multibyte/NFC/CRLF cases|Exact limits after normalization; upper bound valid only if both limits pass; overflow rejected without overwriting last valid body/review state|
|L311|Empty/whitespace-only editor, NUL/C0/DEL/C1/bidi override/isolate|No reviewed copy; rejected controls never become output; LF accepted; errors fixed-safe text|
|L312|Review → Copy rejects/missing browser API|COPY_FAILED, no “copied”; body remains local/current; no POST/download/storage fallback|
|L313|Two clicks before clipboard promise resolves|One call maximum; second ignored/disabled; no duplicate export|
|L314|Discard with pending copy then resolve/reject|EMPTY and DOM textarea cleared; stale promise cannot restore body/review/notice; initiated clipboard write is not retractable|
|L315|Change company/site/connection/version/user/session epoch or logout|EMPTY immediately; any old generation callback cannot render/copy; no token comparison/authority claim|
|L316|Unmount/remount or two distinct fixture instances|Unmount clears; remount EMPTY; instances do not share preview/body/review|
|L317|Clock599999ms then600000ms from creation|At599999 current; at600000 EXPIRED/EMPTY, Copy zero even if timer suspended; exactly600sTTL|
|L318|Edit/copy/focus at599s, wall clock backwards, hidden tab then return at601s|No sliding TTL; monotonic expiry wins; no old body restored|
|L319|Scope unavailable at Prepare|CONTEXT_UNAVAILABLE/null preview; no request for ERP context|
|L320|Keyboard navigation/accessible labels/review state|Textarea/controls labelled; Review explicit; focus on new editor and sensible focus after discard; no hidden auto-copy|
|L321|All traces, allowed and denied, including XSS|API/provider/ERP/LLM calls0; app storage writes0; editor/body/token logs0; no autosave/service worker/telemetry/history URL|
|L322|Real clipboard manual probe in approved fixture browser|Only explicit user gesture exports reviewed plain text; permission-denied case honest; do not record actual user clipboard contents|

For L310,8192-byte condition may be unreachable with the2000-scalar cap and four-byte UTF-8 maximum; test each validator independently with synthetic inputs and test the combined constraints. Do not silently relax either bound to manufacture a reachable fixture. A pure normalization test does not prove DOM resource limits; actual fixture input must remain bounded too.

## 4. Implementation sequence after approval

1. Reconcile current artifact hashes and ownership. Use GitNexus concept query/context and upstream impact for every reused/mounted symbol before source edit. If a NEW symbol is absent/UNKNOWN, text-check for existing name/callers, record uncertainty, and keep it new/isolated; do not infer unused code. No current P2-B correction owned by Antigravity is in the allowlist.
2. Create pure types/builder and independent literal/negative tests. Keep validation failures fixed-code text. No P1 action DTO or auth token attached to local preview.
3. Add controller with injectable clock/clipboard, body revision/review and absoluteTTL; race traces before view integration. Denied clipboard is a local outcome, not permission repair or ERP retry.
4. Add accessible plain textarea view and standalone fixture. Fixture receives synthetic epochs, fixed requests and secret-leak sentinels. It never calls existing production transport. Browser route interception denies all API/external hosts; loopback assets only.
5. Execute focused tests, then isolated actual DOM negatives and final type/lint/build once. Record actual commands/exits/hash-bound outcomes. If paths/dependency runtime differ, resolve existing installed tools read-only; do not install or change lockfiles.

Proposed commands **only after files exist and approval is recorded**, using installed local tools:

```powershell
Set-Location E:\lotus-fin\frontend
node --experimental-strip-types --test tests/followupPreview.test.ts tests/followupPreviewController.test.ts
Set-Location E:\lotus-fin
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
C:/Python313/python.exe -B -m pytest -p no:cacheprovider --noconftest tests_e2e/test_followup_preview_e2e.py -q
```

Node strip-types runner/import conventions must match the already installed runtime and existing frontend tests; adapt the command after read-only package inspection, never assert this future command passed. Test harness owns one available loopback port/process and records cleanup; it must not terminate another agent's service. Type/build output goes to that batch's new evidence directory, not a protected cached frontend output. Provide a local-input/copy benchmark with declared workload, byte sizes/elapsed/RSS where observable, no invented acceptance SLO.

## 5. Evidence, demo and exit condition

Builder must deliver exact source diff/hashes, decision record, per-ID oracle results, fixture-only composition, storage/network/log counters, screenshots of suggested/edited/review/copy-denied/discard/expired states, compiler/linter/build exits and owned process cleanup. Independent verifier replays negatives using its own expected literal/clock arrangements; UI copy success alone does not prove no-network or scope cleanup.

Safe first demo: **“local unsaved reminder preview”**, user edits, reviews, copies, discards; label synthetic/unsaved, no debt facts or delivery. No application-ready or ERP Draft claim. Rollback deletes/unmounts only the new local fixture/component; no ERP data exists to undo. Actual product mount, production scope lifecycle and release are a separately approved batch after P2-B ownership clearance. Stop at focused local evidence; no feature flags/dispatch/deployment/mutation/commit/push.
