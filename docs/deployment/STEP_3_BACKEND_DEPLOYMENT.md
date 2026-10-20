# STEP 3: FRAPPE & ERPNEXT BACKEND DOCKER CLUSTER DEPLOYMENT

> **Stage:** Step 3 of 7 in the Lotus Fin Deployment Process  
> **Goal:** Clone repository, spin up the 9 core containers of Frappe v16 & ERPNext, install the `lotus_fin` application, run database migrations on MariaDB 11.8, and seed enterprise accounting demo data.  
> **Prerequisites:** Completed [Step 2: OS Hardening & Docker Environment Setup](./STEP_2_OS_HARDENING_AND_DOCKER.md).  

---

## 1. 9-CONTAINER CLUSTER ARCHITECTURE

The backend infrastructure follows the standard production pattern for Frappe Framework v16 packaged via Docker Compose (`frappe_docker/pwd.yml`):

```text
                                  [ Port 8080 ]
                                        |
                                        v
                         +-----------------------------+
                         |  frappe_docker-frontend-1   |
                         | (Frappe Internal Nginx Proxy)|
                         +--------------+--------------+
                                        |
                 +----------------------+----------------------+
                 |                      |                      |
                 v                      v                      v
        +-----------------+    +-----------------+    +-----------------+
        |     backend     |    |    websocket    |    |       db        |
        | (Gunicorn App)  |    |  (SocketIO Real)|    | (MariaDB 11.8)  |
        +--------+--------+    +-----------------+    +-----------------+
                 |
                 +------------------------------+
                 |                              |
                 v                              v
        +-----------------+            +-----------------+
        |   queue-short   |            |   queue-long    |
        | (Short Workers) |            | (Long Workers)  |
        +--------+--------+            +--------+--------+
                 |                              |
                 v                              v
        +-----------------+            +-----------------+
        |   redis-queue   |            |   redis-cache   |
        |  (Celery / RQ)  |            |  (System Cache) |
        +-----------------+            +-----------------+
                 ^
                 |
        +-----------------+
        |    scheduler    |
        |  (Frappe Cron)  |
        +-----------------+
```

---

## 2. STEP-BY-STEP DEPLOYMENT PROCEDURE

Connect to your cloud server via SSH: `ssh root@<YOUR_SERVER_IP>`.

### 2.1. Clone Lotus Fin Repository
```bash
cd ~
git clone https://github.com/trungkienit25/lotus-fin.git ~/lotus-fin
cd ~/lotus-fin

# Grant execution permissions to the management control script
chmod +x run.sh
```

---

### 2.2. Initialize and Launch the 9 Containers
Execute the cluster startup command:
```bash
./run.sh up
```

*Underlying automated workflow:*
1. Checks and clones the `frappe_docker` configuration repository.
2. Pulls official container images:
   * `frappe/erpnext:v16.36.1` (~2.89 GB)
   * `mariadb:11.8` (~329 MB)
   * `redis:6.2-alpine` (~28 MB)
3. Spawns the transient `create-site` container to initialize the site named `frontend` with default credentials (`Administrator / admin`).
4. Launches all 9 long-running container services.

> [!NOTE]
> Initial execution requires approximately **2 to 3 minutes** depending on network bandwidth for image downloads.

---

### 2.3. Verify Container Health and Status
Inspect the status of running containers:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Cluster Health Verification Matrix (9/9 Containers):**

| Container Name | Expected Status | Ports / Network | Functional Role |
| :--- | :---: | :---: | :--- |
| `frappe_docker-frontend-1` | `Up ...` | `0.0.0.0:8080->8080/tcp` | Frappe ingress reverse proxy |
| `frappe_docker-backend-1` | `Up ...` | Internal | Python Gunicorn application server |
| `frappe_docker-db-1` | `Up ... (healthy)` | `3306/tcp` | MariaDB relational database |
| `frappe_docker-websocket-1`| `Up ...` | Internal | Real-time Socket.io event engine |
| `frappe_docker-queue-short-1`| `Up ...` | Internal | Short background worker queue (Email, Events) |
| `frappe_docker-queue-long-1` | `Up ...` | Internal | Heavy background worker queue (Reports, Snapshots) |
| `frappe_docker-scheduler-1` | `Up ...` | Internal | Scheduled Frappe cron jobs |
| `frappe_docker-redis-queue-1`| `Up ...` | `6379/tcp` | Celery / RQ message broker |
| `frappe_docker-redis-cache-1`| `Up ...` | `6379/tcp` | In-memory key-value cache |

---

### 2.4. Synchronize Lotus Fin App & Migrate Database
Once all 9 containers report healthy statuses, run the sync command:
```bash
./run.sh sync
```

*Sequential operations executed:*
1. Copies current `lotus_fin` application code into `/home/frappe/frappe-bench/apps/lotus_fin` inside the container.
2. Installs `lotus_fin` into the containerized Python virtualenv (`pip install -e`).
3. Executes database migrations (`bench --site frontend migrate`) to apply DocTypes, Custom Fields, and Fixtures.
4. Flushes the Redis cache and gracefully reloads `frappe_docker-backend-1`.

> [!TIP]
> Expected completion log: `[OK] Synced source code, built assets, migrated DB, and reloaded successfully!`.

---

### 2.5. Seed Enterprise Demo Dataset
To supply data for the AI intelligence modules (AI001 through AI007) with invoices, debts, and cashflows:
```bash
./run.sh demo
```

*Seeded entities:*
* Demonstration company: `Lotus-fin (Demo)`.
* Standard chart of accounts and baseline balance sheet.
* Complete transactional batch: `Sales Invoice`, `Payment Entry`, and `AR Overdue` receivables.
* Preconfigured Copilot endpoint: `http://localhost:8080/desk/financial-health`.

---

## 3. VERIFICATION CHECKLIST

- [ ] Command `docker ps` outputs all 9 containers prefixed with `frappe_docker-`.
- [ ] Container `frappe_docker-db-1` displays `(healthy)`.
- [ ] HTTP probe `curl -I http://127.0.0.1:8080/api/method/ping` returns `HTTP/1.1 200 OK` (pong).
- [ ] Command `docker stats --no-stream` confirms aggregate cluster RAM consumption between **750 MB and 1.1 GB**.

---

👉 **Proceed to:** [STEP 4: NGINX REVERSE PROXY & SSL HTTPS CONFIGURATION](./STEP_4_NGINX_AND_SSL_CONFIG.md)
