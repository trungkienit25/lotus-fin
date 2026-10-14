# L3 local reminder text preview contract

12 October 2026 · capability implementation **NOT_IMPLEMENTED**; contract **PROPOSED / NOT_FROZEN**; application enablement **BLOCKED pending template/UX approval**. One selected capability: `followup.prepare_text`. No second form-prefill capability in this slice. A local preview is **not an ERP Draft**. See the [implementation handoff and fixture oracle](CHATBOT_L3_ANTIGRAVITY_HANDOFF.md).

## 1. Minimum scope and exact fixed template

Proposed template ID `followup.neutral.vi.v1`, locale `vi-VN`; **template approval is still pending**. The capability starts from an explicit local user button, not agent dispatch. It never receives invoice/context/selection refs, customer name/contact/recipient, balance, due date, payment eligibility, free chat prompt or an LLM suggestion. It has no ERP/HTTP/LLM dependency.

Exact proposed body (UTF-8 NFC, paragraphs separated by one blank line, no trailing newline):

```text
Xin chào,

Tôi muốn trao đổi về nội dung cần theo dõi. Khi thuận tiện, vui lòng phản hồi để chúng ta xác nhận thông tin và bước tiếp theo.

Cảm ơn.
```

This makes no claim about debt, overdue status, document existence or financial correctness. No automatic “Dear [Customer]”, amount/due placeholders, “please pay” or “eligible payment” language. A later fact-bearing template requires authorized financial/source fields and separate approval. The current five-field invoice reader cannot supply those facts. If asked for a debt-specific preview now, show a fixed notice that financial facts are unavailable; never fill them from chat or demo defaults.

## 2. Exact local request/response/presentation contract

```text
PrepareRequest = {
 contract_version:"l3.followup.local.v0.1",
 capability:"followup.prepare_text",
 template_id:"followup.neutral.vi.v1", locale:"vi-VN"
}
```

Exactly four fields, exact literals; any extra field or null invalid. A strict builder rejects `invoice_id`, recipient, amount, due, HTML, secret, signed ref and arbitrary template even if provided by a model. No request ID/CID, signed auth token or fake ERP source is needed: this is an in-process local function, not a P1 action envelope or server endpoint.

```text
PrepareResult = {status:"PREVIEW_READY",contract_version,capability,
 preview:{template_id,locale,body,provenance:"SUGGESTED",
   facts_verified:false,persisted:false,delivery:"NONE",side_effects:[],
   financial_source:null}}
Failure = {status:"INVALID_INPUT"|"CONTEXT_UNAVAILABLE"|"EXPIRED",
 preview:null,user_message:fixed-safe-text}
```

Runtime-only controller wrapper owns `scope_epoch`, `preview_generation`, creation/expiry instants and review/edit state; these never appear in the copied body and never confer ERP permission. It accepts an injected local lifecycle clock and existing app scope signals, with no network request. Missing app lifecycle signals blocks a production mount. Do not call `get_context` just to generate text.

Presentation: title **“Bản nháp cục bộ — chưa lưu, chưa gửi”**; visible **“Nội dung gợi ý; chưa xác minh thông tin tài chính”**. Textarea contains the exact body. Four explicit controls: **Edit**, **Review**, **Copy text**, **Discard**. No Save ERP/Send/Schedule/Pay button, recipient field, success “saved/sent” badge, invoice URL or autocomplete. Show copy failure honestly and keep the local preview editable until expiry. Copy success means only system clipboard write.

## 3. Provenance and bounded editing

All fixed template body is `SUGGESTED`; this is template provenance, not financial evidence. Any user edit changes the **entire body** to `USER_ENTERED`; reverting to the original text does not silently restore `SUGGESTED`. A separate explicit **Reset template** discards the edited preview and creates a new generation. Never infer `ERP_VERIFIED`/authorized debt facts from edits. Display the current provenance alongside the editor; editable source/provenance flags are forbidden.

User body is a local value, max2000 Unicode scalar values and8192 UTF-8 bytes after NFC and CRLF→LF normalization. No trim/change of meaningful text. Allow LF, reject NUL/C0 except LF, DEL, C1 and Unicode bidi override/isolate controls; invalid edit cannot replace valid state or enable Copy. Bound input before expensive parsing. Plain-text `<script>`, HTML-like text and instruction language may be shown literally in a React text node/textarea, never interpreted, linked or sent to a model. Use no `innerHTML`, Markdown/HTML parser, rich editor, remote spellcheck/translation or automatic link preview.

Manual entry is not validated financial truth. Generic secret recognition cannot be guaranteed for arbitrary user text; the enforceable control is that the capability imports **no** secret/ref/document data, never transmits/logs/persists the editor, and only copies its plain body on an explicit reviewed user action. Do not market a secret detector. Clipboard is an intentional local export controlled by the user; no tokens/metadata/provenance wrappers are appended. Persistent free-text memory remains disabled under SecurityV3 SEC-027.

## 4. In-memory lifecycle and review

Proposed absolute TTL600 seconds from preview creation, never extended by edit/copy/focus; requires Product/Security approval. Monotonic local clock governs TTL; wall clock is presentation only. Recheck TTL and scope immediately before every state transition and clipboard call. A background-tab timer delay cannot revive expired data.

```text
EMPTY --explicit Prepare--> EDITABLE(SUGGESTED)
EDITABLE --valid user edit--> EDITABLE(USER_ENTERED), review cleared
EDITABLE --explicit Review--> REVIEWED(current body revision)
REVIEWED --Copy user click + current scope/TTL--> COPYING
COPYING --resolved--> REVIEWED + local COPIED notice
COPYING --rejected--> REVIEWED + local COPY_FAILED notice
any --Discard/logout/scope-change/unmount/expiry--> EMPTY; pending generation fenced
REVIEWED --edit--> EDITABLE; Copy disabled until fresh Review
```

Review is an explicit checkbox/button associated with exact body revision. Copy disabled before Review, on invalid/empty/expired text or while one copy is pending. A repeated click produces no second simultaneous clipboard call. Late promise success/failure after reset must not repopulate state or show “copied”. Copy failure does not claim completion. New Prepare discards old content and resets review.

Protected local scope includes account/session generation, company, product/site/connection version and app logout/switch generation. Client scope signals isolate browser state; they are **not server authorization**. Subscribe to the existing lifecycle owner; never store SID/token/raw user identity in preview. Clear on company/site/connection/user/session/logout change, unmount and expiry; browser refresh starts EMPTY. React state and refs only; no localStorage/sessionStorage/IndexedDB/service worker/history URL/global singleton/chat history/backend cache or draft autosave. Clear DOM textarea on discard too. Detached React instances must not share preview objects.

Clipboard requires explicit user gesture and a qualified local browser API. No fallback hidden form POST/download/persistent draft. Clearing the preview cannot retract text already copied to the user's clipboard; state this precise limitation. No automatic clipboard-read or later clipboard rewrite. If copy was initiated before scope reset, it may complete externally; suppress its stale UI acknowledgment, do not promise atomic rollback of clipboard contents. Review/copy interactions never constitute one-use L4 approval.

## 5. Security negatives and acceptance

Acceptance oracle is the exact literal template and state transitions in the handoff. Cover malicious extra arguments, html/script literal rendering, instruction text, token/PII canaries in surrounding app state, no request/log/storage, provenance downgrade, review invalidation, limits, clipboard deny/double-click, wrong/changed scope, expiry/background clock, unmount and late promise. Store only synthetic fixture sentinels/screenshots; never record live user body or clipboard contents. Feature/UI telemetry must exclude body/prompts/refs/actor data; first local batch emits no telemetry.

Existing B1 rendering/fences are design reuse, not approval to mount into P2-B owned files. No existing Panel/Drawer/invoice action/dataProvider/authProvider edits. ADR001 requires each new cohesive source <200 lines; use independent builder/controller/view ownership, not artificial line splitting. Benchmark obligations apply to the later implemented local use case; do not fabricate throughput from this document.

**Smallest batch:** after template/UX/TTL/clipboard decision, standalone pure local builder + memory controller + preview component and focused tests, with fixture-only injection. No production mount/flags changed. Demo: proposed text examples now; after that batch passes, clearly unsaved synthetic preview/edit/review/copy/discard. Release blockers: approved literals and lifecycle contract, actual mounted app logout/scope ownership, browser clipboard behavior, independent local DOM/security/accessibility verification and later explicitly authorized mount. Finance/source G3 is not needed for the fact-free local template; adding ERP facts reinstates a separate source approval gate.
