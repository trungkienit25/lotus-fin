# P4-C canonical route and session CSRF

Date: 2026-10-13. Candidate: frozen `candidate-r5`; manifest SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e`.

## Serving decision

Frappe's `page_renderer` hook serves only `/copilot`, `/ai`, `/home`, and `/copilot/session`. The React entry is a private app template copied from the Vite build. Guests requesting an application route receive a 302 to `/login?redirect-to=%2Fcopilot`; guests requesting the bootstrap receive a private, no-store 401. A persisted enabled user and active session are checked using the existing P4-B principal validator before either the entry or token is returned. Unsupported paths, API methods, Desk paths, and static files stay with their normal Frappe handlers. `/copilot/unknown` remains 404. The old public `/assets/lotus_fin/core/index.html` is absent.

Vite builds JavaScript, CSS, branding images and favicon against `/assets/lotus_fin/core/`. The authenticated entry remains same-origin with the Frappe API; no production proxy or second backend is involved. The Frappe-only Compose project is bound to loopback for qualification.

## Session and CSRF decision

`GET /copilot/session` calls the installed Frappe v16 `frappe.sessions.get_csrf_token()` for the *current* authenticated `sid`, then commits the session update required by token generation on a GET request. The actual pinned token generator, session persistence, framework validator and Desk commit call are retained in [`FRAPPE_CSRF_SEMANTICS.txt`](docs/reviews/evidence/p4c-2026-10-13/FRAPPE_CSRF_SEMANTICS.txt); this is an internal framework facility used through Lotus's authenticated renderer, not an invented RPC API. The response is exactly `{user, csrf_token}` with `Cache-Control: private, no-store`, `Vary: Cookie`, and `nosniff`. It cannot mint a token for a guest, disabled user or revoked session; POST to the bootstrap is 405. Tokens are held only in React memory and never placed in a URL, persistent storage, or a build artifact.

The auth provider rechecks the bootstrap on login, authentication check, identity read and logout. The invoice transport bootstraps before protected POST, uses `credentials: same-origin` and `X-Frappe-CSRF-Token`, and checks the session again before accepting a reply. A login/logout generation change or external cookie switch fences the old reply. Frappe's server-side CSRF check remains active. Framework 401/403 and the actual Frappe `CSRFTokenError` HTTP 400 become denied session outcomes; an arbitrary 400 or malformed invoice envelope still fails strict validation. No retry can turn a failed POST into a second invoice action.

## Validation

The source checks passed: 9 renderer tests, 114 frontend tests and frontend lint. The final r5 image passed 19 real browser/HTTP checks both before and after a cold stack restart. That run made one native CORE POST per login session, checked current-session CSRF, exact disabled envelope, guest and old-cookie denial, and every rendered image. The runtime provenance report records zero source drift. P4-B security files, `useInvoiceActions.ts`, `VercelChatPanel.tsx`, `demoInvoiceProvider.ts`, and `runtime/boundary.py` were not edited by P4-C.

N0 remains BLOCKED; a valid request returns `NOT_AVAILABLE`/`CAPABILITY_DISABLED`, never a native invoice result.
