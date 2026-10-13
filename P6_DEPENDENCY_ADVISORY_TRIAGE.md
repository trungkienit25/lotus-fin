# Dependency advisory triage

The user selected retained advisory evidence instead of disclosing dependency metadata to a fresh npm audit. No new audit request was sent after that selection. This is triage of the October 13 P4 evidence, not a clean current advisory qualification.

The current frontend lock still includes path-to-regexp 8.2.0 through @ant-design/pro-layout and @refinedev/antd. P4's retained production audit marks this chain HIGH and cites regex denial-of-service advisory ranges including >=8.0.0 <8.4.0. It is present in the shipped client dependency graph. Static route use alone does not close the advisory; dynamic router/module reachability must be reviewed before a minimally scoped lock update. No blanket major `audit fix` was applied.

Retained full npm audit also contains development-chain advisories. They must be distinguished from production inclusion, not summed as independent flaws. Retained runtime PyPI metadata flags oauthlib, pdfkit, PyJWT, pypdf, weasyprint and Werkzeug package versions; metadata presence is not proof of exploitability. Compare the actual new image's runtime lock with each advisory's affected ranges and enabled OAuth/JWT/printing routes before closing. The app/framework packages are not qualified by PyPI lookup alone.

Evidence: docs/reviews/evidence/p4-independent-2026-10-13/npm-audit-production.txt, npm-audit.txt, npm-explain.txt and python-advisory-review.txt. Current package/source hashes are in the P6 manifests. Verdict: advisory release gate unresolved; severity is not downgraded.
