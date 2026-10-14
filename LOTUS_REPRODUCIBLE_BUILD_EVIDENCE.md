# Reproducible build evidence

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

The candidate is selected **current working-tree bytes**, including approved
dirty/untracked UI/backend inputs. Git HEAD alone does not represent this release.
557 pre-existing selected source files were preserved byte-for-byte; nine existing
paths changed within authorized runtime/build scope. No unrelated selected source
or AI001/AI002/AI003 numerical algorithm source changed.

Final candidate: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314/rc-auth/candidate`.
Archive: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314/rc-auth/LOTUS_CORE_SOURCE.tar.gz`.

| Artifact/check | Actual value |
| --- | --- |
| Selected files | 616 |
| Copy/archive SHA256 verified | 616/616 |
| Python files parsed | 324 |
| Archive SHA256 | `aea9751864ea8ff88a222014b4768be38a7906207db4cfdb418cae9aa4b84639` |
| Manifest SHA256 | `8f31b9aeb8f4f2603cdd074662c1216ff3ed93ba5d330d5b5f5d3ccc50b7fb23` |
| Baked app/support source files verified | 346 |
| Serving image identity | `sha256:de0aa8d8454af7bf0970d39a9610c41d6acf935d9b8918b942b605ab57edca62` |
| Framework runtime lock | 133 resolved pinned/direct-reference dependencies |
| Frontend | Clean npm ci: 378 packages; TypeScript + Vite PASS; HTML/JS/CSS baked |

`SOURCE_MANIFEST.json`, `INTEGRITY.json`, `IMAGE_SOURCE_INTEGRITY.json` and
`PRESERVATION_CHECK.json` are authoritative per-file evidence. SHA256 values for
all baked frontend assets are in the image integrity file. App/native contracts,
tests, React sources, lockfiles, scripts and configuration examples are included.
Generated caches, installed dependencies, editor metadata and actual `.env`/
`.runtime` secrets are excluded. Concrete credential-pattern scan found no
matches; it is not proof against every possible secret format.

Actual exits: initial clean build 1 (existing TS2367); corrected build 0;
final archived-candidate build 0; package/transfer 0; pip check 0;
image Frappe-only import/hash/registration 0. The final build applies the resolved
`framework.lock` plus `requirements.lock` and checks compatibility. Version locks
and immutable image/source references do not claim wheel-hash/SBOM/vulnerability
acceptance or a byte-identical future image timestamp/attestation.

The first init smoke caught missing asset linkage because init bypassed the image
entrypoint; Compose was corrected and replayed. Real HTTP then caught Frappe's
missing pre-Desk CSRF token gap (422 reaching the disabled handler); the Lotus
native boundary was hardened and its missing-token/valid-token paths replayed.
One build was attempted before its candidate directory finished packaging and
exited 1; that receipt is retained as BUILD_AUTH_CONTEXT_PENDING, then retried.
No failing attempt is converted into PASS.

Backend regression: 438 PASS (offline doubles). Boundary/CSRF: 21 PASS.
Preview lifecycle: 20 PASS. Those counts refer to separate suites; earlier 16
boundary cases are a subset of the final 21, not additional tests.
