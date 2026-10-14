# P4-C serving image provenance

Date: 2026-10-13. Final frozen source: [`CANDIDATE_SOURCE_R5.json`](docs/reviews/evidence/p4c-2026-10-13/CANDIDATE_SOURCE_R5.json), SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e`, 517 image-input files. The immutable build context is [`candidate-r5`](docs/reviews/evidence/p4c-2026-10-13/candidate-r5). It includes the available P4-A and P4-B handoff source and the P4-C route, bootstrap and asset corrections. Final image tag: `lotus-fin:core-p4c-01a13415-r5`.

**PASS:** image ID `sha256:f7eda114867f2ea8803a5dafbef8e9927eeed0cb070b32766723cb1ea92325b3`. The cached image-config timestamp is 2026-10-13 15:54:00 Asia/Saigon (08:54 UTC); r5 reuses the verified runtime layers and has a new build attestation for the final source artifact. The builder pins Frappe v16.35.0 to commit `012667b9c4e7f66d5e1ff5858d2e922331d4300a` and the official build/base image digests in [`Dockerfile`](docker/lotus-core/Dockerfile). It runs `npm ci` from `frontend/package-lock.json`, produces a Vite bundle with base `/assets/lotus_fin/core/`, and copies the entry to a private Lotus template. The public static `index.html` is removed. The app stage installs only `frappe` and `lotus_fin`; neither a runtime ERPNext import nor an ERPNext app install is part of the recipe.

The final runtime receipt [`RUNTIME_PROVENANCE.json`](docs/reviews/evidence/p4c-2026-10-13/RUNTIME_PROVENANCE.json) confirms all seven Lotus app containers use that exact image ID; 334 packaged backend files match the frozen SHA-256 list with no mismatch or live-source drift. The private HTML is SHA-256 `e2e42734b757dee2e703da94b495fa7d2aa1bfbc02f86a75d5a300b4acc2490b`; the served JavaScript is `assets/index-CeY-kyfF.js`, SHA-256 `52fc47074a33fac873fa56c1b976b6151cbcf12030fedb4cb6fe239a3e0f88ad`; the CSS is `assets/index-j6L4zPa6.css`, SHA-256 `0126d0bd8d95741b35163e1b8a5a4394e2245908b5ddffa445a507663da91f41`. The pre-restart receipt is retained separately.

| Build input lock | SHA-256 |
| --- | --- |
| `frontend/package-lock.json` | `4530fd8c3e9496a684a8569ee6a47dd0f3eb8d010b3def7a6d4222db67f23dd9` |
| `docker/lotus-core/framework.lock` | `c378b14ca9e669989a5e18164ca3084a32a2c6b54e49be34689587f87f9c8e0a` |
| `docker/lotus-core/requirements.lock` | `98a0e096f85b3d99b8ec6d0def15daff317cb850af5598764b5aab911b3c99ac` |

The installed app list is exactly `frappe, lotus_fin`. ERPNext import, Company/Sales Invoice schemas and invoice tables are absent; legacy default hooks are empty; framework CSRF enforcement is active. The ordinary actor is enabled and lacks Administrator/System Manager roles. The post-restart receipt repeated these checks with the same image ID and zero drift.

The P4-B boundary and its two security test files still match their handoff manifest hashes. The hooks file includes P4-C's renderer registration while retaining P4-B's boundary hooks. r5's final Compose dependency restart policies are also checked in the runtime receipt. Developer metadata, dependency directories, generated builds and secrets are excluded from the source snapshot.

The r4-to-r5 source-manifest comparison changes only `docker/compose.lotus-core.yml`; all frontend/backend/build inputs are identical. Therefore the 114 frontend checks, 9 renderer checks, lint and successful bundle build apply unchanged to r5. Final r5 startup, automatic dependency recovery, provenance and browser/HTTP checks were executed afresh. The four prohibited source files match the first P4-C snapshot.

The earlier r2 receipt matched 334 packaged backend files, had zero live-source drift, contained exactly `frappe` and `lotus_fin`, and observed no ERPNext or invoice schema. r2 is superseded by r5 for final acceptance. The frozen build log is [`image-build-frozen-r5.log`](docs/reviews/evidence/p4c-2026-10-13/image-build-frozen-r5.log). No commit or push was made.
