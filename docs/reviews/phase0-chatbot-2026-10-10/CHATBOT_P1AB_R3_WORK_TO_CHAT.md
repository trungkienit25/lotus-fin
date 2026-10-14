# Work → Chat: P1-A/P1-B Round 3

11/10/2026 · Lotus Fin / FinTechathon Shenzhen 2026.

**P1A_CHANGES_REQUIRED. P1B_CHANGES_REQUIRED. Không đóng combined offline acceptance.** Hai blocker production đã tái hiện; live ERP authorization/G10 vẫn chưa qualified.

Source: develop@`07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, staged empty, existing Panel/Drawer tracked diff unchanged. Current correction changes five production files/two tests/two report appends. 20 code files <200 lines; report prefixes preserved;641 tracked fingerprints and prior history unchanged; B1-S R7 13/13 source hashes unchanged. Relevant GitNexus graph stale61/not found; bounded static tracing, không “safe” inference. Full source/dirty/import/hash manifests linked from [independent recheck](CHATBOT_P1AB_R3_INDEPENDENT_RECHECK.md).

|Current execution|Result|
|---|---|
|Focused existing P1-A/P1-B|59/59 PASS:41 +18; exit0,3.48s.|
|Independent N01–N12/A13–A15/C01–C06 + sequential A16|22/22 PASS; exit0.|
|Additional actual-default A16|6 sequential healthy/outage controls PASS;2 failures: concurrency and suppressed required delivery.|
|Independent B01–B14|13 PASS /1 FAIL (B03),0 ERROR; exit1.|
|B03 public controller confirmation|Both exact-company denial and permission outage still issue200/OK/context_ref.|

Counts overlap; do not sum as unique tests. All network attempts0, actual ERP/LLM imports0, measured synthetic business-read attempts0. Processes exited, owned logging state restored/handlers closed, both controlled threads finished; no source/test/data/dependency/Docker changes. Full historical bytes for three uncommitted B modules were not previously saved; current hashes/source verified, exact historical diff unavailable for those files. This limitation is separate from demonstrated defects.

Only material repairs:

1. **A16 HIGH — builder/backend owner:** default adapters mutate shared/root handleError. Controlled two-request execution yields failed sink returning success/count1 and leaked callback; WARNING suppression also yields0 bytes/count1. Use one owned acknowledgment-capable sink contract without request-time shared callback mutation. Acceptance: real healthy/failing direct/ancestor/root/default, deterministic concurrent failure attribution/count0/callback unchanged, filtered/disabled/no-sink delivery not counted; preserve N01–N12/A13–A15/CID/privacy tests.
2. **B03 HIGH — builder/security owner:** Company check omits exact Company identity; missing/throwing permission interface bypasses authorization. Require trusted current-principal/exact-company proof; unavailable seam produces approved unavailable/denied outcome before context/ref. Acceptance: type-allowed/company-denied, missing interface and exception all fail closed through controller with healthy real sink; valid allowed control passes; search/open remain disabled and ERP reads0.

SID absence, exact reference bindings/config-version transition, opaque SID, absent/direct-failing audit sink, strict request identity and actual POST whitelist/request-ID echo now PASS in offline probes. Actual default A16 sequential propagation is fixed. Keep these improvements; no broad rewrite.

**Closure:** Chat cannot close P1-A or P1-B offline yet. Proposed next batch: only A16 + B03, approved source paths/line limits and graph impact, then Work independent recheck. Không tự dispatch/implement P2-A.

**Qualification remains separate:** P1B_LIVE_AUTHORIZATION NOT_RUN. Before a separately scoped target run, approve exact trusted Lotus Fin→ERP product/site/connection/version mapping, installed app/custom-hook lineage, principal/company/doc/field/revocation oracle, key policy/required observable sink and fresh private fixture baseline/lifecycle/cleanup. Test actual authenticated POST/Guest/GET/CSRF, decoder/envelope/CID/no-store/error delivery and deny-before-read. Direct-call/decorator fakes are not live permission evidence.

Invoice search/open **disabled**, financial automation not authorized. G3 finance/G01–G03 not closed; B1-S prior PASS preserved; **G10 BLOCKED independently**. After offline closure and target qualification, Chat may scope P2-A bounded authorized invoice search/select/open; this packet grants no enable/release permission.
