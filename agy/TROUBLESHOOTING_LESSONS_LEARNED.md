# 💡 Troubleshooting & Production Lessons Learned

This document provides an exhaustive post-mortem and knowledge transfer detailing architectural traps, production incidents, and verified resolutions encountered during the deployment of **Lotus Fin**.

---

## 1. Routing Dilemma: Headless Frappe vs React SPA

### The Issue
- After logging in successfully, users were redirected to the default Frappe/ERPNext Desk interface (`/desk`) instead of the custom Lotus Fin React frontend.
- Direct navigation to `/login` or `/app/...` rendered native Frappe Jinja2 server-rendered templates rather than the client-side SPA.

### Root Cause Analysis
- The legacy Nginx configuration indiscriminately reverse-proxied user-facing UI routes to the Frappe backend:
  ```nginx
  # Flawed legacy configuration
  location ~ ^/(api|files|socket\.io|app|desk|login)($|/) {
      try_files $uri @frappe_backend;
  }
  ```
- Because `/login`, `/app`, and `/desk` were forwarded to Frappe, the browser received Frappe's Python/Jinja2 web responses, completely bypassing the compiled React bundle.

### Resolution
- **Strict Separation of Concerns**: Frappe is strictly constrained to a headless API role.
- All presentation routes (`/login`, `/app/:doctype`, `/copilot`, `/ai`, `/workspace/*`, `/report/*`, `/page/*`) are routed to `index.html` to be handled by React Router.
- The default ERPNext Desk (`/desk`) is completely blocked and permanently redirected to `/`:
  ```nginx
  # Production configuration in docker/production/nginx.conf
  location ~ ^/desk($|/) {
      return 301 /;
  }

  # Only headless API, files, websocket, and session endpoints hit Frappe
  location ~ ^/(api|files|socket\.io|copilot/session)($|/) {
      try_files $uri @frappe_backend;
  }

  # All user-facing routes load the React 19 SPA
  location / {
      root /usr/share/nginx/html;
      index index.html index.htm;
      try_files $uri $uri/ /index.html;
  }
  ```

---

## 2. The Silent Authentication Loop (`/copilot/session`)

### The Issue
- Entering valid credentials resulted in a `200 OK` response with `{"message": "Logged In"}` from `/api/method/login`.
- However, the page immediately reloaded and bounced the user back to `/login` without accessing the Copilot dashboard.

### Mechanism Breakdown
- The frontend authentication lifecycle in `frontend/src/providers/authProvider.ts`:
  ```typescript
  if (response.data?.message === "Logged In") {
    clearSessionBootstrap();
    await bootstrapSession(); // Critical handshake
    return { success: true, redirectTo: "/copilot" };
  }
  ```
- The `bootstrapSession()` function immediately invokes `GET /copilot/session` to obtain the authenticated username and session CSRF token.
- Because `/copilot/session` was missing from the Nginx proxy whitelist, Nginx routed it to `location /`, returning `index.html` (Content-Type: `text/html`).
- Attempting `response.json()` on HTML text raised a silent `SessionBootstrapError`, leading the auth provider to mark the session as `REVOKED` and trigger a redirect back to `/login`.

### Resolution
- Add `/copilot/session` explicitly to the Nginx backend proxy rule:
  ```nginx
  location ~ ^/(api|files|socket\.io|copilot/session)($|/) {
      try_files $uri @frappe_backend;
  }
  ```
- This endpoint is handled natively in the Frappe backend by `LotusSpaPage` (`lotus_fin/lotus_fin/runtime/spa.py`), returning the required JSON:
  ```json
  {"user": "Administrator", "csrf_token": "..."}
  ```

---

## 3. Preserving `X-Forwarded-Proto` Behind Edge SSL Proxies

### The Issue
- When using DNS/CDN edge proxies (Cloudflare, Tenten VCloud DNS Anycast), end-users connect over **HTTPS**, but the edge proxy connects to the VPS over plain **HTTP (Port 80)**.
- If Nginx specifies:
  ```nginx
  proxy_set_header X-Forwarded-Proto $scheme; # $scheme is "http" on port 80
  ```
  Nginx overwrites the incoming `X-Forwarded-Proto` header with `http`.
- The Frappe backend then assumes an unencrypted session, causing it to omit the `Secure` flag on `sid` session cookies or trigger undesirable protocol redirects.

### Resolution
- Implement an Nginx `map` block to honor the edge proxy's protocol header:
  ```nginx
  map $http_x_forwarded_proto $proxy_x_forwarded_proto {
      default $http_x_forwarded_proto;
      ''      $scheme;
  }

  server {
      ...
      location @frappe_backend {
          ...
          proxy_set_header X-Forwarded-Proto $proxy_x_forwarded_proto;
      }
  }
  ```

---

## 4. Non-Interactive Database Hydration & Root Credentials

### The Issue
- Running automated database restoration:
  `python -m frappe.utils.bench_helper frappe --site frontend --force restore seed.sql.gz`
- Without passing root credentials, Frappe invokes `getpass()` to solicit the MariaDB root password interactively.
- In automated script pipelines (headless `docker exec` without TTY), this resulted in immediate termination or silent hanging.

### Resolution
- Always pass `--db-root-password "${DB_PASSWORD:-admin}"` explicitly:
  ```bash
  docker exec --workdir /home/frappe/frappe-bench/sites "$ACTUAL_BACKEND" \
      /home/frappe/frappe-bench/env/bin/python -m frappe.utils.bench_helper frappe --site frontend --force restore --db-root-password "${DB_PASSWORD:-admin}" "$SEED_FILE"
  ```

---

## 5. Worker Container Python Module & Dependency Parity

### The Issue
- Background jobs (AI Cashflow Digest, What-If simulation engine, and Scheduled Risk Alerts) are executed asynchronously by worker containers:
  `lotus-fin-prod-queue-long-1`, `lotus-fin-prod-queue-short-1`, `lotus-fin-prod-scheduler-1`.
- If `lotus_fin` is only volume-mounted in the `backend` container, workers crash with:
  `ModuleNotFoundError: No module named 'lotus_fin'`.
- Furthermore, scientific computing libraries (`numpy`, `pandas`, `pydantic`) required by the Lotus Fin analytics core were missing in the base Frappe worker image.

### Resolution
1. Mount the `lotus_fin` application volume into **all** worker containers in `compose.prod.yml`:
   ```yaml
   volumes:
     - sites:/home/frappe/frappe-bench/sites
     - logs:/home/frappe/frappe-bench/logs
     - ../../lotus_fin:/home/frappe/frappe-bench/apps/lotus_fin
   ```
2. Automatically synchronize Python packages across all worker environments:
   ```bash
   for c in backend queue-long queue-short scheduler; do
       docker exec --user root "$c" /home/frappe/frappe-bench/env/bin/pip install -e /home/frappe/frappe-bench/apps/lotus_fin
   done
   ```

---

## 6. Host Port 80 Port-Binding Conflicts

### The Issue
- During container startup, Docker fails with:
  `bind: address already in use` on Port 80.

### Resolution
- Audit listening processes: `ss -tulpn | grep :80`.
- If an OS-level standalone Nginx daemon is active, stop and disable it:
  ```bash
  systemctl stop nginx
  systemctl disable nginx
  ```
- Delegate all reverse proxying exclusively to the containerized Gateway.
