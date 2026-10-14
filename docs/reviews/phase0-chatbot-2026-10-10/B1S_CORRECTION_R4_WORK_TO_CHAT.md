# Work → Chat — B1-S Correction Round 4

2026-10-10 → 2026-10-11 (Asia/Saigon) · FinTechathon Shenzhen · independent targeted F07 inspection/E2E. **B1S_G4B_CHANGES_REQUIRED / B1S_R4_PARTIAL.** No freeze/dispatch.

`develop` HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, implementation uncommitted. [Current manifest](../evidence/b1s-g4b-correction-r4-2026-10-10/SOURCE_BEFORE.json) identifies artifact. Round3→4 only native test/report changed; five production files, fixture/package/lock preserved. Test300lines≤approved320.333protected fingerprints,286historical raw hashes/12deliverables preserved. Graph61commits stale/context notfound; UNKNOWN unresolved; subsequent fixer impact required.

**Verified progress:** four exact Round3 failures nowPASS (alias, outbound, foreignWS, readiness-error cleanup). Ordinary native4PASS/pytest0 with direct owned PID22680=listener, cleanupPASS. Original native qualification17PASS. **Application52/52PASS**, previous48gold +four F05 probes; F05CLOSED; actualPage/Drawer0POST, scope/races/reset/unmount/CID/XSS preserved. Exact-message32checksPASS over captured results, not additional cases. Build/typecheck/lint NOT_RUN Round4 because test-only/current config unchanged; Round3 results historical.

**Eight further failing scenarios group into four remaining root causes:**

1. Registry incomplete: GETCopilot200, undeclaredCompanyquery200, encodedAPIpath200HTML, arbitraryasset200HTML, arbitrarylocalWS all leave pytest0. Validate exact method/query/normalized path and bounded asset/exactWS policy. ForeignWS no upstream is now verified from installed Playwright semantics.
2. Readiness trusts socket: post-preflight sentinelPID23932 accepted/yielded while ownedVitePID11308 running. Require expected HTTP readiness and listenerPID ownership.
3. Final ledger checked before browser close: native aborts/records late event but pytest0. Shared per-test guard owner must assert after settled context teardown, even on setup/error.
4. IDLE not current-case proof: omitted22nd action leaves25requests/26clicks, repeatedFORBIDDEN readsoldresult, pytest0. Bind request/response/generation or cleared result; retain exact expected messages.

Native unique records31PASS/8FAIL; one duplicate LOCAL_WS assertion excluded from count, raw preserved. No application permission/financial runtime conclusion from harness probes. Offline containment prevents external traffic; private copy fully cleaned.

| Gate | Current |
|---|---|
| G1/G2 | PASS narrow identity/UI contract |
| G3 | PARTIAL, financial qualification NOT_RUN |
| G4A/G4B | FAIL / CHANGES_REQUIRED |
| G10 | BLOCKED independently |
| G01–G03 | NOT_CLOSED |

**Small next batch:** F07 root-cause fixes only, approved test/fixture paths; preserve52application/17originalqualificationPASS, make eight failing scenarios deny/fail or reject wrong-readiness and clean owned resources. Do not reopen production. If clean implementation exceeds cap320/allowlist, submit one test-helper SCOPE_CHANGE_REQUIRED proposal before adding it. Append reproducible commands/PIDs/Q evidence; builder currently references absent run_q_probes.py. Chat decides scope/approval; Work rechecks.

LotusFin/ERPNext identities remain separate. RealERP/LLM/financial authority, backend/sessionpermissions, SDK/topology, G10 deployment and performance budgets unqualified in this batch; F102unchanged. Financial automation demo acceptance remains pending.

[Review](B1S_CORRECTION_R4_INDEPENDENT_RECHECK.md) · [Ledger](B1S_CORRECTION_R4_TEST_RESULTS.json) · [Raw/reproduction](../evidence/b1s-g4b-correction-r4-2026-10-10/REPRODUCTION.md).
