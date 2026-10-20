# END-TO-END DEPLOYMENT PLAN: LOTUS FIN ON LINUX CLOUD SERVER

> **Document:** End-to-End Cloud Deployment & Verification Plan  
> **System:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Target Environment:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / 2 vCPU / 8 GB RAM / 40 GB SSD)  
> **Document Version:** v1.0 — October 2026  

---

## 1. ARCHITECTURE OVERVIEW & DEPLOYMENT OBJECTIVES

### 1.1. Cloud Network & Single Virtual Machine Architecture
The system operates self-contained inside a dedicated Cloud VPC subnet on **a single Compute Virtual Machine** without requiring external cloud load balancers:

```text
[ Public Internet / Clients & Administrators ]
                       │
                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CLOUD PROVIDER VPC (Virtual Private Cloud — 10.0.0.0/16)                               │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ VPC INTERNET GATEWAY (IGW)                                                     │   │
│   │ - Public IPv4 Allocation / Elastic IP (e.g., 203.0.113.10)                     │   │
│   │ - 1:1 NAT Routing & Internet Ingress/Egress Gateway                            │   │
│   └──────────────────────────────────────┬─────────────────────────────────────────┘   │
│                                          │ Route: 0.0.0.0/0 via IGW                    │
│                                          ▼                                             │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ PUBLIC DMZ SUBNET (10.0.1.0/24)                                                │   │
│   │                                                                                │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ CLOUD SECURITY GROUP (Stateful Packet Filter)                          │   │   │
│   │   │ ────────────────────────────────────────────────────────────────────── │   │   │
│   │   │ [INBOUND RULES]                                                        │   │   │
│   │   │ • TCP 22  (SSH)   ───► Whitelisted Admin CIDR (Remote Management)       │   │   │
│   │   │ • TCP 80  (HTTP)  ───► 0.0.0.0/0 (SSL Certbot & HTTPS Redirect)         │   │   │
│   │   │ • TCP 443 (HTTPS) ───► 0.0.0.0/0 (Encrypted Web Traffic & API)          │   │   │
│   │   │ [OUTBOUND RULES]                                                       │   │   │
│   │   │ • ALL Traffic     ───► 0.0.0.0/0 (Stateful Tracking; OS, Docker, LLM)  │   │   │
│   │   │ ────────────────────────────────────────────────────────────────────── │   │   │
│   │   │                                                                        │   │   │
│   │   │   ┌────────────────────────────────────────────────────────────────┐   │   │   │
│   │   │   │ VIRTUAL MACHINE INSTANCE (Ubuntu 22.04 LTS / 10.0.1.15)         │   │   │   │
│   │   │   │                                                                │   │   │   │
│   │   │   │  [Host OS Packet Filter — UFW (Uncomplicated Firewall)]        │   │   │   │
│   │   │   │  • Default Policy: Inbound DROP | Outbound ALLOW               │   │   │   │
│   │   │   │  • Filtered Ports: 22/tcp, 80/tcp, 443/tcp                     │   │   │   │
│   │   │   │                            │                                   │   │   │   │
│   │   │   │                            ▼                                   │   │   │   │
│   │   │   │  ┌──────────────────────────────────────────────────────────┐  │   │   │   │
│   │   │   │  │ HOST NGINX REVERSE PROXY (Layer 7 Application Gateway)   │  │   │   │   │
│   │   │   │  │ • TLS 1.3 Termination (Let's Encrypt automated certs)    │  │   │   │   │
│   │   │   │  │ • Security Headers (HSTS, CSP, X-Frame-Options: DENY)    │  │   │   │   │
│   │   │   │  │ • Rate Limiting: 10 req/s per IP (Burst: 20 nodelay)     │  │   │   │   │
│   │   │   │  │ • Payloads bounded: Client body max 50 MB (Invoices)     │  │   │   │   │
│   │   │   │  │ • WebSockets proxy: /socket.io/ (real-time chat)         │  │   │   │   │
│   │   │   │  └─────────────┬────────────────────────────┬───────────────┘  │   │   │   │
│   │   │   │                │ Static Assets (/)          │ API / Desk       │   │   │   │
│   │   │   │                ▼                            ▼ (:8080 loopback) │   │   │   │
│   │   │   │  ┌───────────────────────────┐  ┌───────────────────────────┐  │   │   │   │
│   │   │   │  │ React Frontend SPA        │  │ Frappe Frontend Container │  │   │   │   │
│   │   │   │  │ (/var/www/lotus-fin-fe)   │  │ (127.0.0.1:8080)          │  │   │   │   │
│   │   │   │  └───────────────────────────┘  └─────────────┬─────────────┘  │   │   │   │
│   │   │   │                                               │                │   │   │   │
│   │   │   │  ┌────────────────────────────────────────────┴─────────────┐  │   │   │   │
│   │   │   │  │ ISOLATED DOCKER BRIDGE NETWORK (Internal non-routable)   │  │   │   │   │
│   │   │   │  │ • backend (Gunicorn WSGI)  • db (MariaDB 11.8 - 3306)    │  │   │   │   │
│   │   │   │  │ • redis-cache (6379)       • redis-queue (6379)          │  │   │   │   │
│   │   │   │  │ • queue-short & queue-long • websocket (SocketIO)        │  │   │   │   │
│   │   │   │  └──────────────────────────────────────────────────────────┘  │   │   │   │
│   │   │   └────────────────────────────────────────────────────────────────┘   │   │   │
│   │   └────────────────────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2. Deployment Objectives
1. Detailed survey and assessment of server hardware, network, and base OS packages.
2. Foundation hardening (Swap buffer, Docker runtime, Host Nginx, log rotation).
3. 9-container Frappe backend cluster orchestration (Frappe v16, ERPNext, MariaDB 11.8, Redis, Celery workers).
4. `lotus_fin` application synchronization and enterprise accounting demonstration fixture seeding.
5. Host Nginx reverse proxy configuration serving React frontend SPA and proxying backend APIs.
6. Execution of the 6-scenario verification test matrix (Unit tests, What-If simulation, AI Copilot APIs).
7. Automated continuous deployment (CI/CD) pipeline integration via GitHub Actions.

---

## 2. PHASE 1: CLOUD SERVER SURVEY & AUDIT

Prior to software installation, perform an automated pre-flight audit via SSH:

### 2.1. All-in-One Diagnostic Script
Execute the system survey script on the server:

```bash
cat << 'EOF' > /tmp/server_survey.sh
#!/usr/bin/env bash
echo "=========================================================="
echo "          LOTUS FIN - SYSTEM SURVEY REPORT                "
echo "=========================================================="

echo -e "\n[1] OS & KERNEL INFORMATION"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"

echo -e "\n[2] HARDWARE RESOURCES (CPU / RAM / DISK)"
echo "CPU Cores: $(nproc)"
echo "RAM:"
free -h
echo "Disk:"
df -h /

echo -e "\n[3] BASE UTILITIES"
echo "Git: $(git --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Docker: $(docker -v 2>/dev/null || echo 'NOT INSTALLED')"
echo "Docker Compose: $(docker compose version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Nginx: $(nginx -v 2>&1 || echo 'NOT INSTALLED')"

echo -e "\n[4] LISTENING NETWORK PORTS (80, 443, 8080, 3306, 6379)"
ss -tulpn | grep -E ':80|:443|:8080|:3306|:6379' || echo "-> Key ports are currently free."

echo -e "\n[5] HOST FIREWALL STATUS (UFW)"
ufw status

echo -e "\n[6] OUTBOUND CONNECTIVITY (GITHUB / DOCKER HUB)"
echo -n "GitHub ping: "
curl -Is --connect-timeout 5 https://github.com | head -n 1
echo -n "Docker Hub ping: "
curl -Is --connect-timeout 5 https://registry-1.docker.io/v2/ | head -n 1

echo "=========================================================="
EOF
chmod +x /tmp/server_survey.sh
/tmp/server_survey.sh
```

### 2.2. Baseline Audit Checklist

| Audit Criterion | Verification Command | Lotus Fin Standard | Actionable Recommendation |
| :--- | :--- | :--- | :--- |
| **CPU Cores** | `nproc` | Minimum 2 vCPUs | Ensure $\ge 2$ Cores for multi-threaded concurrency |
| **Physical RAM** | `free -m` | Minimum 4 GB, 8 GB recommended | 9-container cluster footprint is ~1.2 GB RAM |
| **SSD Storage** | `df -h /` | Minimum 20 GB, 40 GB recommended | Ensure free disk space $\ge 15\text{ GB}$ |
| **Swap Space** | `swapon --show` | Mandatory $\ge 2\text{ GB}$ | Allocate 2GB Swap file in Phase 2 if absent |
| **Operating System** | `lsb_release -a` | Ubuntu 22.04 LTS x86_64 / Debian 12 | Official distribution compatible with Docker CE |
| **Port 80 (HTTP)** | `ss -tulpn \| grep :80` | Free for Host Nginx | Designated for reverse proxy in Phase 4 |
| **Port 8080 (Frappe)**| `ss -tulpn \| grep :8080`| Free for loopback proxy container | Avoid port conflicts |
| **Port 3306 (DB)** | `ss -tulpn \| grep :3306`| Isolated inside Docker | Must never bind to public interfaces |
| **Docker Engine** | `docker -v` | Release 24.x or newer | Install official upstream release in Phase 2 |
| **Docker Compose** | `docker compose version`| Compose Plugin v2 | Install Compose plugin in Phase 2 |
| **Git CLI** | `git --version` | Git 2.25+ | Required to clone and synchronize code |
| **UFW Firewall** | `ufw status` | Ports 22, 80, 443 open | Verify Cloud Provider Security Group rules |
| **GitHub Access** | `curl -Is https://github.com` | `HTTP/2 200` | Verify outbound network connectivity |
| **Docker Hub** | `curl -Is https://registry-1.docker.io/v2/` | `HTTP/2 401` *(standard unauth)* | Confirms registry image pulling ability |

---

## 3. PHASE 2: OS HARDENING & DOCKER SETUP

### 3.1. Allocate 2GB Virtual Swap Memory
Even on an 8GB RAM host, provisioning 2GB Swap with conservative swappiness (`swappiness=10`) is essential to eliminate the risk of the Linux Out-Of-Memory (OOM) Killer terminating MariaDB or Gunicorn processes during database migration spikes:

```bash
# Allocate 2GB swap file
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Persist swap mount across system reboots
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Tune swappiness (trigger swap only when free RAM drops below 10%)
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf
```

### 3.2. Install Docker Engine & Docker Compose Plugin
```bash
apt update
apt install -y ca-certificates curl gnupg lsb-release

# Add Docker official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker CE and Compose plugin
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker daemon
systemctl enable docker
systemctl start docker
```

### 3.3. Enforce Container Log Rotation Limits
By default, Docker stores container JSON logs with unbounded growth. Enforce a strict 10MB per-file ceiling:

```bash
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl restart docker
```

### 3.4. Prepare Web Root & Application Directories
```bash
mkdir -p /var/www/lotus-fin-fe
mkdir -p ~/lotus-fin
```

---

## 4. PHASE 3: FRAPPE BACKEND CLUSTER DEPLOYMENT (DOCKER COMPOSE)

### 4.1. Clone Codebase & Setup Runners
```bash
cd ~
git clone https://github.com/trungkienit25/lotus-fin.git ~/lotus-fin
cd ~/lotus-fin

# Ensure executable permissions on management runner
chmod +x run.sh
```

### 4.2. Initialize 9 Container Services
Launch the container cluster:
```bash
./run.sh up
```
*Note:* During the initial startup, Docker downloads base images (`frappe/erpnext:v16.36.1`, `mariadb:11.8`, `redis:6.2-alpine`) and initializes the `frontend` site database. This typically takes 2 to 3 minutes.

Verify container status:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
*Verify that all 9 containers report healthy or `Up`:*
1. `frappe_docker-frontend-1` (:8080)
2. `frappe_docker-backend-1`
3. `frappe_docker-db-1` (healthy)
4. `frappe_docker-redis-cache-1`
5. `frappe_docker-redis-queue-1`
6. `frappe_docker-queue-short-1`
7. `frappe_docker-queue-long-1`
8. `frappe_docker-scheduler-1`
9. `frappe_docker-websocket-1`

### 4.3. Synchronize Lotus Fin App & Migrate Database
```bash
./run.sh sync
```
This command performs:
* Synchronizes `lotus_fin` app source into the container bench directory.
* Installs `lotus_fin` on the `frontend` site.
* Runs database migrations (`bench --site frontend migrate`).
* Clears all application caches (`clear-cache`).
* Validates demo configuration fixtures.

### 4.4. Seed Demonstration Accounting Dataset
```bash
./run.sh demo
```
Initializes sample enterprise accounts (`Lotus-fin (Demo)`), fiscal years, general ledger records, and transactions across modules AI001 – AI006.

---

## 5. PHASE 4: HOST NGINX REVERSE PROXY & SSL CONFIGURATION

### 5.1. Configure Nginx Virtual Host
Create `/etc/nginx/sites-available/lotusfin`:

```bash
cat > /etc/nginx/sites-available/lotusfin << 'EOF'
server {
    listen 80;
    server_name _; # Replace with production domain (e.g., demo.lotusfin.vn)

    client_max_body_size 50m;

    # 1. Serve React Frontend SPA Static Assets
    location / {
        root /var/www/lotus-fin-fe;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 2. Reverse Proxy APIs, SocketIO & Desk to Frappe Docker Proxy (:8080)
    location ~ ^/(api|assets|files|socket.io|app|desk)/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        # WebSocket support for real-time Copilot streaming and desk notifications
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Extended timeouts for deep financial analytics and stress-test calculations
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;

        # Disable buffering to preserve LLM response streaming
        proxy_buffering off;
    }
}
EOF
```

### 5.2. Activate Site & Reload Nginx
```bash
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 5.3. (Optional) Provision Automated TLS Certificate via Certbot
If pointing an active domain name:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d demo.lotusfin.vn
```

---

## 6. PHASE 5: REACT FRONTEND PACKAGING & DEPLOYMENT

Because compilation of the React frontend takes only **1.47 seconds** and yields an optimized `dist` payload **< 1 MB**, the optimal deployment approach is building locally (or inside CI runners) and copying artifacts to the server:

### 6.1. Build on Local Development Workstation
From `d:\Coding\lotus-fin\frontend`:
```bash
npm run build
tar -czf dist.tar.gz -C dist .
```

### 6.2. Transfer and Extract onto Cloud Server
From local machine:
```powershell
scp -P 22 .\dist.tar.gz root@<YOUR_SERVER_IP>:/tmp/
```

On the Cloud Server:
```bash
rm -rf /var/www/lotus-fin-fe/*
tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/
rm -f /tmp/dist.tar.gz
```

---

## 7. PHASE 6: TESTING & VERIFICATION MATRIX

Following installation, execute the full 6-scenario verification sequence:

```text
[Scenario 1: Network & Ping]  ──>  [Scenario 2: Desk Login]  ──>  [Scenario 3: AI Copilot API]
                                                                          │
[Scenario 6: Resource Audit]  <──  [Scenario 5: Stress Test] <──  [Scenario 4: Suite Test]
```

### Scenario 1: Verify HTTP/HTTPS Endpoints
* **Commands:**
  ```bash
  curl -I http://127.0.0.1/
  curl -I http://127.0.0.1/api/method/ping
  ```
* **Expected Result:** Returns `HTTP/1.1 200 OK` (pong).

### Scenario 2: Frappe Desk Authentication
* **URL:** `http://<YOUR_SERVER_IP>/desk/financial-health`
* **Credentials:** `Administrator` / `admin`
* **Expected Result:** Login succeeds; the Financial Health dashboard displays revenue, margins, and cash balance KPI charts.

### Scenario 3: AI Copilot API Endpoint Verification
* **Test Command:**
  ```bash
  curl -s -X POST "http://127.0.0.1:8080/api/method/lotus_fin.api.copilot_api.chat_copilot" \
       -H "Content-Type: application/json" \
       -d '{"query": "financial health summary", "company": "Lotus-fin (Demo)"}'
  ```
* **Expected Result:** Structured JSON response containing diagnostic metrics, advice, and UI widget data (HTTP 200).

### Scenario 4: Automated Financial Integration Tests
* **Command:**
  ```bash
  cd ~/lotus-fin
  ./run.sh test lotus_fin.tests.test_financial_health
  ```
* **Expected Result:** `Ran 15 tests ... OK` in $< 0.5$ seconds.

### Scenario 5: What-If Stress-Testing Simulation (AI004)
* **Command:**
  ```bash
  ./run.sh simulate
  ```
* **Expected Result:** Standard output outputs all 9 modeled KPI layers (`revenue`, `gross_margin`, `ar_outstanding`, `dso`, `net_cash_flow`, `ending_cash`, `ccc`, `cash_shortfall`).

### Scenario 6: Hardware Resource Audit
* **Command:**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
  ```
* **Expected Result:**
  * 9 containers consume $\le 1.5\text{ GB}$ total RAM.
  * Host free RAM $\ge 5.5\text{ GB}$.
  * CPU idle $\ge 95\%$.

---

## 8. PHASE 7: GITHUB ACTIONS CI/CD AUTOMATION

Configure `.github/workflows/deploy.yml` to automatically build the frontend and update the backend upon merge to `main` or `develop`:

### 8.1. Secrets Required in GitHub Repository
Under **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
* `VM_HOST`: `<YOUR_SERVER_IP>`
* `VM_USERNAME`: `root`
* `VM_SSH_KEY`: SSH Private Key authorized on the cloud server.
* `VM_PORT`: `22`

### 8.2. CI/CD Pipeline Configuration
```yaml
name: Deploy Lotus Fin to Cloud Server

on:
  push:
    branches: [main, develop]
  workflow_dispatch:

concurrency:
  group: deploy-cloud-server
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Build React Frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build
          tar -czf dist.tar.gz -C dist .

      - name: Transfer Artifacts to Cloud Server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          source: "frontend/dist.tar.gz"
          target: "/tmp/"

      - name: Deploy Code & Reload Services
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VM_HOST }}
          username: ${{ secrets.VM_USERNAME }}
          key: ${{ secrets.VM_SSH_KEY }}
          port: ${{ secrets.VM_PORT || 22 }}
          script: |
            set -e

            # 1. Update Frontend
            rm -rf /var/www/lotus-fin-fe/*
            tar -xzf /tmp/frontend/dist.tar.gz -C /var/www/lotus-fin-fe/
            rm -f /tmp/frontend/dist.tar.gz

            # 2. Update Backend Code
            cd ~/lotus-fin
            git fetch origin main
            git reset --hard origin/main
            chmod +x run.sh

            # 3. Synchronize containers and run migrations
            ./run.sh sync

            # 4. Clean Docker cache to preserve disk space
            docker system prune -f

            echo ">>> DEPLOYMENT COMPLETED SUCCESSFULLY ON CLOUD SERVER! <<<"
```

---

## 9. MAINTENANCE & TROUBLESHOOTING RUNBOOK

| Operational Scenario | Diagnostic Symptom | Immediate Remediation |
| :--- | :--- | :--- |
| **Disk Exhaustion** | `No space left on device` | `docker system prune -af --volumes`<br>`journalctl --vacuum-time=3d` |
| **RAM Exhaustion / OOM** | Container restarts repeatedly | Check swap: `free -h`<br>Restart worker: `docker restart frappe_docker-backend-1` |
| **502 Bad Gateway** | Nginx cannot connect to Backend | Check internal proxy container: `docker ps`<br>`docker logs frappe_docker-frontend-1 --tail 50` |
| **Missing Demo Ledgers** | Missing DocType or chart of accounts | Re-run: `./run.sh sync && ./run.sh demo` |
| **Realtime Backend Logs** | Debugging Copilot API or tool calls | `docker logs -f frappe_docker-backend-1 --tail 100` |

---

*Authored by Lotus Fin Engineering Team — Internal Engineering Specification.*
