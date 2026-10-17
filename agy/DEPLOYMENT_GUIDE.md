# 🚀 Production Cloud Deployment Manual

Comprehensive guide for provisioning, orchestrating, and operating **Lotus Fin** on cloud Linux VPS instances (Ubuntu 22.04 / 24.04 LTS).

---

## 1. Hardware & System Prerequisites

- **Operating System**: Ubuntu 22.04 LTS or 24.04 LTS (x86_64)
- **Minimum Resources**: 2 vCPU, 4GB RAM (Recommended: 4 vCPU, 8GB RAM).
- **Swap Memory**: Minimum 2GB Swapfile (automatically provisioned by deployment scripts if absent).
- **Disk Storage**: At least 25GB free SSD storage.
- **Firewall & Security Groups**: Inbound HTTP Port `80` and HTTPS Port `443` open.

---

## 2. 1-Click Deployment Pipeline

### Step 1: Clone Repository & Grant Execution Permissions
```bash
git clone https://github.com/trungkienit25/lotus-fin.git
cd lotus-fin
git checkout release/beta-1.0
chmod +x run.sh scripts/*/*.sh
```

### Step 2: Configure Production Environment Variables
Create `docker/production/.env.production` (or `.env` in the repository root):
```env
SERVER_NAME=_
PROD_PORT=80
LOTUS_SITE=frontend
DB_PASSWORD=admin
ADMIN_PASSWORD=admin
LOTUS_AI_PROVIDER=gemini
LOTUS_LLM_PROVIDER=gemini
LOTUS_LLM_MODEL=gemini-flash-latest
LOTUS_AI_MODEL=gemini-flash-latest
LOTUS_AI_TIMEOUT_SECONDS=45
LOTUS_AI_MAX_REACT_ITERATIONS=4
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=lotusfin.notifications@gmail.com
LOTUS_SMTP_PASSWORD=btcyjmbjnykrrpol
LOTUS_SMTP_USE_TLS=1
```

### Step 3: Ensure Port 80 Is Unbound
If a standalone Nginx daemon is already running on the host OS from a previous setup, disable it so the Docker Gateway container can bind directly to Port 80:
```bash
systemctl stop nginx
systemctl disable nginx
```

### Step 4: Execute Automated Cloud Deployer
```bash
./scripts/deploy/run-deploy.sh
```

The pipeline automatically handles all stages:
1. **Host Audit**: Checks CPU, RAM, and automatically activates a 2GB Swapfile to protect against Out-Of-Memory (OOM) crashes during Frappe compilation.
2. **Docker Engine Verification**: Inspects and bootstraps Docker Engine & Compose plugin if not already installed.
3. **Gateway Packaging**: Compiles the React 19 SPA (`npm run build`) and builds `lotus-fin/gateway:latest` packaging static assets with reverse-proxy rules.
4. **Multi-Container Orchestration**: Spins up all 10 services defined in `docker/production/compose.prod.yml`.
5. **Database Hydration**: Waits for site `frontend` initialization, uploads and restores the General Ledger snapshot `initial_db_seed.sql.gz`.
6. **Worker Synchronization**: Installs `lotus_fin` and required scientific runtime dependencies (`numpy`, `pandas`, `pydantic`) across all queue workers and scheduler.
7. **Schema Migration**: Executes `bench migrate` and applies demo accounting dataset & SMTP notification configuration.
8. **End-to-End Audit**: Performs health checks on Port 80 and prints out access endpoints.

---

## 3. Container Lifecycle Operations

All day-to-day operations can be managed via the unified [run-container.sh](file:///root/lotus-fin/scripts/container/run-container.sh) script:

```bash
# Check status and health of all production containers
./scripts/container/run-container.sh status

# Stream aggregated logs in real time
./scripts/container/run-container.sh logs

# Gracefully restart the multi-container stack
./scripts/container/run-container.sh restart

# Stop all running containers
./scripts/container/run-container.sh stop

# Tear down containers and clean up networks
./scripts/container/run-container.sh clean
```

---

## 4. Custom Domain & SSL Configuration

Because the Nginx Gateway uses a wildcard catch-all `server_name _;`, you can map any custom domain to your server IP immediately:

1. **DNS Records (Cloudflare, Tenten VCloud DNS, Namecheap, etc.)**:
   - `A` Record: `@` -> `<SERVER_PUBLIC_IP>` (Enable Proxy if available)
   - `A` Record: `www` -> `<SERVER_PUBLIC_IP>` (Enable Proxy if available)
2. **Edge Proxy / CDN Auto-SSL**:
   - If using Cloudflare or Tenten VCloud DNS with proxy enabled, SSL certificates are automatically terminated at the Edge CDN layer.
   - Traffic is forwarded securely to Port 80 on your VPS, and the Nginx Gateway automatically preserves the HTTPS protocol context via `X-Forwarded-Proto`.
