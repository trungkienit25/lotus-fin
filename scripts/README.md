# 🌿 Lotus Fin — Operations & Deployment Manual (Run Scripts Guide)

Comprehensive operational guide covering local environment setup, dependency verification, Docker container packaging, and 1-click cloud server deployment on HTTP Port 80.

---

## 📁 Operational Scripts Directory Structure (`/scripts`)

```
scripts/
├── deploy/                 # Automated deployment pipeline for Cloud / Web servers
│   └── run-deploy.sh       # 🚀 1-Click Pipeline: audits env, restores DB seed, exposes Port 80
├── dev/                    # Developer scripts for local setup and rapid iteration
│   ├── run-dev.sh          # Linux / macOS / WSL: Auto-detects OS, starts backend & Vite (port 5173)
│   ├── run-dev.ps1         # Windows PowerShell: Automated local dev stack launcher
│   ├── run-fe.sh           # Linux / macOS: Dedicated frontend operations (dev, build, preview)
│   └── run-fe.ps1          # Windows PowerShell: Dedicated frontend operations
├── packaging/              # Production container packaging
│   └── run-packaging.sh    # Builds multi-stage lotus-fin/gateway image (React SPA + Nginx)
├── container/              # Production container lifecycle management
│   └── run-container.sh    # Start, stop, restart, logs, and status on Port 80
└── data/                   # Server migration backups & ledger snapshots
    └── database/           
        └── initial_db_seed.sql.gz  # Full General Ledger database snapshot for instant hydration
```

---

## 🚀 1. 1-Click Cloud Server Deployment (`run-deploy.sh`)

When provisioning a fresh VPS (Ubuntu 22.04 / 24.04, Debian, AWS EC2, DigitalOcean, Aliyun, Tencent Cloud), run the unified entrypoint:

```bash
chmod +x run.sh scripts/*/*.sh
./run.sh deploy
# Or run directly:
./scripts/deploy/run-deploy.sh
```

### Automated 7-Step Deployment Pipeline:
1. **Host Resource Audit:** Inspects CPU, RAM, and Swap. Automatically configures a **2GB Swapfile** if host memory is low, preventing Frappe backend Out-Of-Memory (OOM) crashes.
2. **Docker Engine Verification:** Automatically verifies or installs official Docker Engine and Compose plugin if missing on Linux.
3. **Configuration Verification:** Inspects and initializes production variables in `docker/production/.env.production`.
4. **Gateway Packaging:** Builds the `lotus-fin/gateway:latest` container image packaging the React SPA with optimized Nginx reverse-proxy configuration.
5. **Container Orchestration:** Launches the production multi-container stack exposed on **Port 80**.
6. **Automated Database Hydration:**
   - Automatically unpacks and restores the database snapshot [`scripts/data/database/initial_db_seed.sql.gz`](data/database/initial_db_seed.sql.gz) onto site `frontend`.
   - Runs `bench migrate` to synchronize DocType schemas.
   - Configures default SMTP outgoing email settings and loads the corporate demo accounting ledger (`Lotus-fin Demo`).
7. **Readiness & Health Verification:** Conducts end-to-end HTTP health checks and outputs the public server IP for immediate browser access.

---

## 💻 2. Local Developer Workflows (`run-dev.sh` / `run-dev.ps1`)

For local development and feature work:

### Linux / macOS / WSL / Git Bash:
```bash
./run.sh dev
# Or directly:
./scripts/dev/run-dev.sh
```

### Windows PowerShell:
```powershell
.\run.ps1 dev
# Or directly:
.\scripts\dev\run-dev.ps1
```

- Automatically detects the host OS, boots backend support containers (MariaDB 11.8, Redis 6.2, Frappe Backend), synchronizes the `lotus_fin` app, and launches the Vite Dev Server at `http://localhost:5173`.

---

## 🎨 3. Dedicated Frontend Management (`run-fe.sh` / `run-fe.ps1`)

When working exclusively on frontend React 19 / TailAdmin code:

```bash
# POSIX (Linux / macOS / WSL)
./scripts/dev/run-fe.sh [dev|build|install|check|preview|clean]

# Windows (PowerShell)
.\scripts\dev\run-fe.ps1 -Action [dev|build|install|check|preview|clean]
```

---

## 📦 4. Production Container Packaging (`run-packaging.sh`)

To rebuild container images prior to a release or after frontend updates:

```bash
./run.sh packaging
# Or directly:
./scripts/packaging/run-packaging.sh
```

- Packages `lotus-fin/gateway:latest` via a multi-stage Dockerfile:
  - **Stage 1:** Compiles React/TypeScript SPA using `node:20-alpine`.
  - **Stage 2:** Copies compiled static assets into `nginx:alpine` alongside optimized reverse-proxy rules.

---

## 🐳 5. Production Container Management (`run-container.sh`)

```bash
./scripts/container/run-container.sh start    # Launch production stack on Port 80
./scripts/container/run-container.sh status   # Check health and resource usage
./scripts/container/run-container.sh logs     # Stream aggregated container logs
./scripts/container/run-container.sh restart  # Gracefully restart services
./scripts/container/run-container.sh stop     # Gracefully stop containers
./scripts/container/run-container.sh clean    # Tear down containers and networks
```

---

## 🌐 6. Single Port 80 Entrypoint (Nginx Gateway)

Lotus Fin exposes all services through a single unified HTTP **Port 80**:
- **Route `/`:** Serves the compiled React 19 SPA (TailAdmin & Lotus Copilot).
- **Routes `/api`, `/desk`, `/assets`, `/socket.io`:** Reverse-proxies directly to the Frappe/ERPNext backend (`frappe-frontend:8080`).
- End-users and finance executives access the application directly at `http://<SERVER-IP>/` without needing to remember custom port numbers like `:8080`.
