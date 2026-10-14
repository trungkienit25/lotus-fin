# V1 independent financial gold specification

12 October 2026 · implementation **NOT_IMPLEMENTED**; specification **PROPOSED / NOT_FROZEN**; live oracle **BLOCKED / NOT_RUN**. Expected values below are independently specified synthetic arithmetic, not observed ERP facts or approved accounting policy. Read the [V1 contract](CHATBOT_V1_PAST_FINAL_DUE_CONTRACT.md) and [authority register](CHATBOT_PROPOSAL_COMPLETION_PLAN_UPDATED.md) first.

## 1. Oracle ownership and stages

**Gold author:** Finance/QA independent of the future builder. Expected values must be reviewed and frozen before implementation output is examined. Do not import the future evaluator, adapter, report parser, fixture builders or AI001/AI002/AI003 calculators to generate expectations. An expected value copied from `outstanding_amount` only proves field transport, not reconciliation.

**Stage D — offline deterministic:** hand-authored input rows, calendar facts, finite decimal strings, exact expected IDs/residuals/currencies/classifications. No Frappe/network/LLM/ERP imports. Only after G2 approval may these become code tests. **Stage S — source qualification:** separately approved isolated ordinary-user ERP fixtures; finance oracle derives invoice-account residual from independently frozen accounting vouchers and actual explicit allocations/credits/writeoffs/reversals in the correct party-account currency. Then compare oracle ↔ actual authorized parent fields ↔ delivered DTO. Any mismatch blocks G3; never adjust expected values to green the adapter. **Stage A — delivery/UI/security/resources:** actual allowed methods/auth/field masking/source bytes/audit/no-write/HTTP/selected view, after S. These stages are not interchangeable.

Manifest for every case: unique ID/stage, synthetic/ERP label, contract/formula/policy/precision versions, actor permission matrix (opaque fixture aliases), product/site/company/connection, installed versions/image/worker/source hashes, observation UTC/IANA timezone/local date, posting interval, source rows/voucher identities+versions/settlement allocations, independent derivation, exact expected outcome/items/units/coverage, public nullability, expected reads/writes/log leakage, commands/exits, actual result and cleanup baseline. Include independently reviewed schema/precision metadata and source coverage variant. Preserve original expectations and all failures.

## 2. Synthetic baseline and exact arithmetic

Unless overridden: Sales Invoice `S-A`, Company A, ordinary authorized U-A, docstatus1, is_return0, is_pos0, posting `2026-10-01`, final due `2026-10-11`, lossless current residual `"100"`, party currency `USD`, invoice currency `USD`, storage scale4/presentation scale2, policy-qualified normal settlement, source version `v1`. Observation `2026-10-12T05:00:00Z`, site `Asia/Ho_Chi_Minh`, D=`2026-10-12`; posting interval `2026-01-01..2026-10-12`. Scope/predicate/source permission and complete one-row enumeration are fixture facts, never demo-company grants.

`INCLUDE` means exact identity/current residual/unit; `EXCLUDE` means valid nonmatch; `INVALID/UNSUPPORTED` means no fabricated value and incomplete coverage; `DENY` means no data/source/handles or existence disclosure. Exclusions are not error rows. For isolated valid nonmatches, exhausted complete enumeration yields OK/EMPTY_RESULT. For invalid/unsupported rows, zero matches yields PARTIAL, not EMPTY_RESULT. If qualification itself is absent, NOT_AVAILABLE rather than evaluating rows.

|ID|Independent fixture override|Expected oracle|
|---|---|---|
|D01|Due yesterday `2026-10-11`|INCLUDE `S-A`, residual100/USD, display100.00|
|D02|Due today `2026-10-12`|EXCLUDE, strict `<`|
|D03|Due tomorrow `2026-10-13`|EXCLUDE|
|D04|Residual `"0"` or `"-0.0000"`|EXCLUDE; canonical zero, no debt|
|D05|Residual `"-25"`|EXCLUDE credit balance; no clamp/absolute value|
|D06|Residual `"0.0001"`, s4/p2|INCLUDE exact0.0001/USD, display0.00 plus below-display-precision label; never settled|
|D07|Residual `"0.0049"`, s4/p2|INCLUDE exact0.0049, display0.00 plus tiny-positive label|
|D08|Residual `"0.0050"`, s4/p2|INCLUDE exact0.005, display0.01, HALF_UP boundary|
|D09|Residual `"0.0051"`, s4/p2|INCLUDE exact0.0051, display0.01|
|D10|Residual `"-0.0001"`, s4/p2|EXCLUDE; rounding does not change sign predicate|
|D11|JPY party unit, s4/p0; residual0.4 and0.5|Both INCLUDE; display0/tiny-label and1 respectively; no2-decimal default|
|D12|KWD party unit, s4/p3; residual0.0004 /0.0005|Both INCLUDE; display0.000/tiny-label and0.001|
|D13|VND fixture metadata s2/p0; residual1250.5|INCLUDE exact1250.5/VND, display1251; scale is fixture-defined, not currency assumption|
|D14|USD invoice, EUR party currency, VND company; residual12.34|INCLUDE12.34 **EUR**, display12.34; no FX/invoice-currency relabelling|
|D15|USD100, EUR20, JPY300 authorized invoices|Three separate unit values; no combined420 total|
|D16|Missing/null/empty unit; absent scale; p>s; unsupported scale10|INVALID/UNSUPPORTED; no VND/2-decimal fallback|
|D17|Float0.1, bool true, null, `NaN`, `Infinity`, exponent/whitespace/comma string, 31 integer digits|INVALID; no Decimal(str(float)) recovery or zero substitution|
|D18|Residual more nonzero fractional digits than storage scale|INVALID; no precision loss before classification|
|D19|Due null/empty/`2026-02-30`/timestamp/locale date|INVALID; PARTIAL even if server query would otherwise omit it|
|D20|Posting null/malformed or due earlier than posting|INVALID; no synthetic chronology repair|
|D21|docstatus0 or2|EXCLUDE Draft/cancelled; status text “Overdue” cannot override|
|D22|is_return1 with residual positive or negative|EXCLUDE return/credit candidate; no fake collectible balance|
|D23|Posting `2026-10-13`, due11th|EXCLUDE future posting by policy; no current→historical balance claim|
|D24|Posting outside displayed interval, otherwise eligible|EXCLUDE; UI says within interval, not all-company debt|
|D25|Terms due10th and20th, parent final20th, residual100|EXCLUDE despite overdue first term; zero runtime child reads|
|D26|Terms due1st and11th, parent final11th, residual40|INCLUDE40 parent residual; no40-labelled installment balance|
|D27|Fully settled parent0; original schedule rows100/200 remain positive|EXCLUDE; no schedule residual/cash recreation|
|D28|Stored status Paid but qualified positive residual100/past final|INCLUDE by fields; no status updater invocation|
|D29|Stored status Overdue but qualified residual0|EXCLUDE; status string is not current truth|
|D30|At UTC `2026-10-11T16:59:59Z`, Ho_Chi_Minh; due11th|D11th, EXCLUDE due-today|
|D31|At UTC `2026-10-11T17:00:00Z`, Ho_Chi_Minh; due11th|D12th, INCLUDE; page window crossing next midnight forces new search|
|D32|Same UTC instant as D31, site UTC|D11th, EXCLUDE; host/browser timezone has no effect|
|D33|Leap day/year boundary, frozen D=`2028-03-01` /`2027-01-01`|Feb29/Dec31 are yesterday; INCLUDE if otherwise valid|

Representation cases additionally assert canonical exact fixed-point strings, presentation scale/rounding, negative-zero normalization, no float JSON finance values, no cross-currency totals and no material-value changes by explanatory text. Validate maximum input lengths before expensive Decimal/date processing.

## 3. Independent settlement/source cases

The arithmetic below is a **proposed synthetic accounting basis**. Actual fixture construction and ERP permissions require their own explicit approval. No fixture script or ERP mutation is executed in this task.

|ID|Independent voucher/allocation basis|Expected parent and V1 behavior after source qualification|
|---|---|---|
|S01|Invoice account debit100; explicit allocated receipt30, party currencyUSD|Current residual70/USD, INCLUDE past-final; invoice creation balance100 is not returned|
|S02|Same invoice; allocated receipt100|Residual0, EXCLUDE, even with positive original terms|
|S03|Debit100, allocated payment120 if installed rules permit negative residual|Residual−20, EXCLUDE. If ERP rejects over-allocation, record that business rejection; never force-invalid fixture|
|S04|Debit100; allocated credit25|Residual75, INCLUDE original parent; credit document excluded|
|S05|Debit100; unallocated party credit25 and `return_against` only|Residual100 if not allocated by qualified ERP rules; no local75 netting. Party aggregate claim forbidden|
|S06|Debit100; allocated payment60 + posted writeoff40|Residual0, EXCLUDE; writeoff is not money collected|
|S07|Debit100; receipt30 reversed through approved ERP lifecycle|Current residual returns100; INCLUDE fresh version/fingerprint, historical residual70 not reused|
|S08|Allocated credit25 cancelled/reversed|Parent residual100 if independent accounting reversal confirms it; no cached75|
|S09|Cancelled old invoice; amended submitted replacement|Old excluded; only new eligible identity returned, no double record|
|S10|POS fully settled / POS partially residual20|0 excluded;20 included only if POS policy approved and oracle qualified; otherwise PARTIAL/UNSUPPORTED_POLICY, including apparent empty scope|
|S11|Invoice100, actual allowed cash discount2 + payment98|Residual0 if qualified accounting confirms it; no2 called overdue; unsupported discount behavior→PARTIAL|
|S12|Invoice currencyUSD100; independent qualified party-accountEUR90; receiptEUR20|Residual70 **EUR**; compare accounting allocations in EUR; no implicit rate calculation at V1 runtime|
|S13|Multiple schedules; partial payment lacks verified term mapping|Parent residual allowed if qualified; installment residual UNAVAILABLE, no FIFO inference; B final due determines match|
|S14|Backdated receipt entered after prior observation|Current residual changes at new read; no AS_KNOWN_AT replay or historical-source badge|
|S15|Parent due_date differs from independently approved final schedule date|SOURCE_DATA_INVALID / G3 failure; do not guess max in runtime child expansion|
|S16|Parent outstanding disagrees with independent allocated-voucher oracle|G3 FAIL; block source, preserve original mismatch, no local patch or “verified” badge|

AI002 Amendment A1 supplies the invoice-level-vs-original-schedule distinction, not automatic V1 approval. AI003's unallocated-credit and duplicate-row findings are relevant failure precedents; neither its historical gold nor AI001's demo totals are the current V1 oracle. Read installed permission/hook/metadata lineage before relying on source behavior.

## 4. Authorization, integrity, race and resource negatives

|ID|Arrangement|Exact negative expectation|
|---|---|---|
|A01|U-A requests Company B / foreign site/product/connection|DENY before financial query; null data/source, no hidden ID/count|
|A02|Select-only rights without invoice read|DENY; select/search privilege is not financial permission|
|A03|Denied/masked `outstanding_amount`, `due_date`, party currency, any classification/order/filter field|Financial query blocked; no hidden predicate inference, no partial zero substitute|
|A04|Document revoked after search and before open|FORBIDDEN dominates stale; old facts/selection clear|
|A05|Field rights revoked/masked between search and open|FORBIDDEN, no old financial detail; ordinary-user regrant needs new request/handle|
|A06|Permission source unavailable/cache stale/disabled user/session logout|Fail closed; a signed handle cannot restore authority|
|A07|Record modified/deleted or due/unit/policy changed|STALE_REFERENCE or generic deny; no automatic navigation/cached success|
|A08|Payment settles100 to0 while parent modified timestamp stays unchanged|Settlement fingerprint catches change; STALE_REFERENCE, no old100 rendered on open|
|A09|Forged/expired/wrong-purpose handle; generic P1 selection used for V1; query/page-size change|REFERENCE_DENIED before invoice lookup; no token payload disclosure|
|A10|Context switch + same RID/CID with foreign source/company or late same-generation response|UI rejects/clears before render; generation fence alone is insufficient|
|A11|Prompt/HTML/SQL/URL in prefix or invoice identifier|Literal normalized bounded data; escaped prefix/DOM; cannot choose fields/action/route or invoke mutation|
|Q01|Missing due data exists alongside valid match|PARTIAL; valid observed match may display but no handles/cursor; missing rows not erased by query filter|
|Q02|No matches plus inaccessible rows vs authorized invalid rows|Hidden rows never disclosed; valid exhausted authorized scope may empty; authorized invalid rows force PARTIAL|
|Q03|Exact duplicate sameID/version within page/across fetch lookahead|No duplicate output/count; source integrity PARTIAL, fetched copies still consume budget|
|Q04|Conflicting duplicate versions/settlement fingerprint|Remove affected identity, mark integrity PARTIAL; no “pick latest” without proof|
|Q05|Stale cache/vendor rows/unknown read instant|Reject as current qualification; no stale-source financial claim|
|Q06|0/1/49/50/51 valid rows, requested page50|Correct page/has-more and explicit selection flags;51 requires counted lookahead/resume, no lost row; no fabricated total|
|Q07|249/250/251 scanned including nonmatches/malformed/lookahead|250 is hard per-invocation cap; no251st read. Exact250 can complete only with reliable exhaustion proof, otherwise PARTIAL|
|Q08|Five full physical pages, no proven exhaustion|No sixth probe; PARTIAL, not EMPTY_RESULT|
|Q09|1MiB source /256KiB response exact limit and +1 byte|Boundary enforced on UTF-8 bytes; +1 safe failure, no truncated JSON or protected fallback|
|Q10|Huge parent/children lazy hydration or uncapped metadata/auth N+1|Physical cap failure before unbounded materialization; no bypass to achieve success|
|Q11|Source timeout, deadline expired before/after fetch, audit sink outage|TIMEOUT or SOURCE_ERROR/no protected success; no automatic retry or fake0/no-match|
|Q12|Concurrent insert/update/rights change during live keyset|Declared live observation limitations; unstable membership →PARTIAL; cursor not historical snapshot|
|Q13|Search page context expires/clock date rolls over|Fresh search required; no mixing evaluation dates or extension by replay|
|Q14|Provider emits missing/extra source anchors or bad amount under outer OK|Reject entire malformed envelope before UI display; do not repair from mocks|

Source test measures actual API/list/auth/document calls separately from SQL statements/examined rows, retrieved bytes, peak memory and hard deadline. Include denied-user workload, large nonmatching data and cold/warm caches. Generic100scan/64KiB tests do not qualify these250scan/256KiB financial-source bounds.

## 5. Acceptance and stop rules

* D acceptance: each table case becomes independently reviewed input/expected output, including positive controls adjacent to all denials. All exact finance/units match; no network/Frappe/LLM; this remains synthetic. Current execution **NOT_RUN**.
* S acceptance: current image/source/site/schema/timezone lineage, approved non-Administrator fixtures, explicit allocations/reversals/currencies and field/document revoke cases. No Administrator-only permission evidence. Real policy mismatches keep G3 blocked. Current execution **NOT_RUN**.
* A acceptance: exact wire/source/context/CID/HTTP/nullability, selected current reader, paging and no-write controls; source/audit failures never fabricate finance. Real accounting/document/status/seen/view/queue/email/provider before-after baselines unchanged for read tests; reviewed audit metadata writes listed separately. Current execution **NOT_RUN**.
* No count inflation: do not add reused/overlapping historical suites, Stage D tests and ERP probes into one financial-verification total. Report separate PASS/FAIL/NOT_RUN and source fingerprints.
* Release: G2 signatures and G3 source/security oracle, actual hard-resource proof, independent delivery/UI acceptance, canonical release artifact and separate deployment authorization. No ERP fixture creation, mutation, commit, deployment or enablement follows from this specification.

**Next executable batch:** obtain G2-V1-01..04 decision records from the contract, freeze these expectations/digests, then implement only V1-D1 under its named three-file allowlist and run focused policy cases with network/ERP imports denied. Until then, these are reviewable gold definitions, not an implemented capability.
