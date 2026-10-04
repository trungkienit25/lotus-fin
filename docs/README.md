# Lotus Fin — Competition Documentation

ERPNext/Frappe SME Finance Copilot (Topic E in the supplied International Track rules).

Scope: AI003 **DEMO_ONLY / COMPETITION**, Contract V2.2,
`AI003_DEMO_POLICY_V1`, `production_calibrated=false`.

## Technical and security documentation

| Feature | Architecture, algorithms and technical assessment | Security design, permission tiers and known risks |
|---|---|---|
| AI001 | [Technical documentation](features/AI001/AI001_TECHNICAL_DOCUMENTATION.md) | [Security self-assessment](features/AI001/AI001_SECURITY_SELF_ASSESSMENT.md) |
| AI002 | [Technical documentation](features/AI002/AI002_TECHNICAL_DOCUMENTATION.md) | [Security self-assessment](features/AI002/AI002_SECURITY_SELF_ASSESSMENT.md) |
| AI003 | [Technical documentation](features/AI003/AI003_TECHNICAL_DOCUMENTATION.md) | [Security self-assessment](features/AI003/AI003_SECURITY_SELF_ASSESSMENT.md) |

AI001 documentation is retrospective, not a fresh penetration-test result.
ISO references describe alignment only, not certification. AI004 and AI005
have not been assessed in this submission-readiness check.



## Source, deployment and evidence

- [App installation README](../lotus_fin/README.md).
- [AI003 reproduction guide](features/AI003/AI003_REPRODUCTION_GUIDE.md).
- [Execution evidence index](features/AI003/evidence/AI003_EVIDENCE_INDEX.md).
- [Final independent AI003 verification](reviews/AI003_FINAL_INDEPENDENT_REVERIFY_3eb8207_2026-10-03.md).
- [Demo test recording](../tests_e2e/videos/ai003_risk_signal_e2e.webm); screenshots in `tests_e2e/screenshots/`.
- Controlled method/policy gold manifests and independent oracles under
  `features/AI003/` prove arithmetic and boundaries, not business calibration.
- Source, automated tests and deployment configuration remain in the repository.

## Remaining submission checks

No tracked presentation deck was found. Prepare English submission material
and a presentation of at most 10 minutes. The rules label the demo video
optional in one item but request it with non-on-chain execution evidence;
prepare a submission video of at most 5 minutes or obtain organizer clarification.
The existing test recording has not been assessed as a final submission video.

Team eligibility, third-party/data licenses and clean-machine deployment
remain unverified. Reproduction describes an existing local sandbox stack,
not a proven one-command fresh deployment. The full submission package and
production readiness are not approved by this document.

Historical authority and verification records are retained for traceability.
Unreferenced agent prompts and empty design placeholders are excluded from
the shared submission tree. See also [system security documentation](security/README.md).
