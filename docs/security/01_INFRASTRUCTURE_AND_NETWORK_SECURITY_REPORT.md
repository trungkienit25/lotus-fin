# INFRASTRUCTURE & NETWORK SECURITY SPECIFICATION REPORT
## Enterprise Infrastructure, Network Boundary & Container Hardening Specification

> **Project Name:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Competition:** The 2026 Shenzhen International FinTech Competition — WeBank FinTech University Challenge (Topic E)  
> **Version:** 3.0 (Technical Deep-Dive, Quantitative Metrics & Implementation Aligned)  
> **Methodology:** `Problem` $\to$ `Solution` $\to$ `Implementation Blueprint` $\to$ `Verification Evidence`  
> **Reference Standards:** CIS Ubuntu Linux 22.04 Benchmark, CIS Docker Community Edition Benchmark, NIST SP 800-53 Rev. 5, OWASP Top 10 API Security (2023)  

---

## 1. INFRASTRUCTURE ARCHITECTURE & ATTACK SURFACE OVERVIEW

Lotus Fin is deployed on a dedicated Linux Cloud Compute instance (Ubuntu 22.04 LTS / 2 vCPU / 8GB RAM / 40GB NVMe SSD), hosting a 9-container Dockerized stack for Frappe Framework v16 & ERPNext, a MariaDB 11.8 database, Redis cache/queue brokers, and an independent Host-level Nginx Reverse Proxy Gateway:

```
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
│   │   │ • TCP 22  (SSH)   ──► Whitelisted Admin CIDR (Remote Management)       │   │   │
│   │   │ • TCP 80  (HTTP)  ──► 0.0.0.0/0 (SSL Certbot & HTTPS Redirect)         │   │   │
│   │   │ • TCP 443 (HTTPS) ──► 0.0.0.0/0 (Encrypted Web Traffic & API)          │   │   │
│   │   │ • ALL OTHER INBOUND PORTS (3306, 6379, 8000, 8080) ──► DROP / DENY ALL │   │   │
│   │   │ ────────────────────────────────────────────────────────────────────── │   │   │
│   │   │ [OUTBOUND RULES]                                                       │   │   │
│   │   │ • ALL TRAFFIC (0.0.0.0/0) ──► ALLOW ALL (OS Updates, GitHub, LLM API)  │   │   │
│   │   └───────────────────────────────────┬────────────────────────────────────┘   │   │
│   │                                       │                                        │   │
│   │                                       ▼                                        │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ COMPUTE VIRTUAL MACHINE (Ubuntu 22.04 LTS / Private IP: 10.0.1.5)      │   │   │
│   │   │                                                                        │   │   │
│   │   │   ┌────────────────────────────────────────────────────────────────┐   │   │   │
│   │   │   │ HOST OS LOCAL FIREWALL (UFW - Second Inbound Perimeter)        │   │   │   │
│   │   │   │ - Default Inbound: DENY ALL | Default Outbound: ALLOW ALL      │   │   │   │
│   │   │   │ - Explicit Allow: TCP 22, TCP 80, TCP 443                      │   │   │   │
│   │   │   └───────────────────────────────┬────────────────────────────────┘   │   │   │
│   │   │                                   │                                    │   │   │
│   │   │                                   ▼                                    │   │   │
│   │   │   ┌────────────────────────────────────────────────────────────────┐   │   │   │
│   │   │   │ NGINX HOST REVERSE PROXY GATEWAY (L7 Application Gateway)      │   │   │   │
│   │   │   │ - SSL Termination (TLS 1.2 / 1.3 Strict Ciphers)               │   │   │   │
│   │   │   │ - DDoS Rate Limiting: 10 req/s per IP, burst=20 nodelay        │   │   │   │
│   │   │   │ - Volumetric Payload Bounding: Max 50MB (Files) / 16KB (JSON)  │   │   │   │
│   │   │   │ - Security Headers: HSTS, CSP strict, nosniff, SAMEORIGIN      │   │   │   │
│   │   │   └───────┬────────────────────────────────────────┬───────────────┘   │   │   │
│   │   │           │ proxy_pass http://127.0.0.1:8080       │ Static Web Files  │   │   │
│   │   │           ▼                                        ▼                   │   │   │
│   │   │   ┌──────────────────────────────────┐   ┌─────────────────────────┐   │   │   │
│   │   │   │ DOCKER BRIDGE NETWORK            │   │ /var/www/lotus-fin-fe   │   │   │   │
│   │   │   │ (Internal Subnet 172.x.0.0/16)   │   │ (React Vite Dist Bundle)│   │   │   │
│   │   │   │                                  │   └─────────────────────────┘   │   │   │
│   │   │   │  [frappe-frontend-1] (:8080)     │                                 │   │   │
│   │   │   │        │ Gunicorn WSGI (:8000)   │                                 │   │   │
│   │   │   │        ▼                         │                                 │   │   │
│   │   │   │  [frappe-backend-1] (App Core)   │                                 │   │   │
│   │   │   │        │                         │                                 │   │   │
│   │   │   │        ├───────────────┬─────────┤                                 │   │   │
│   │   │   │        ▼               ▼         ▼                                 │   │   │
│   │   │   │  [mariadb:11.8]  [redis-queue] [redis-cache]                       │   │   │
│   │   │   │  (Port :3306)    (Port :6379)  (Port :6379)                        │   │   │
│   │   │   │  [NO HOST BIND]  [NO HOST BIND][NO HOST BIND]                      │   │   │
│   │   │   └──────────────────────────────────┘                                 │   │   │
│   │   └────────────────────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DEFENSE-IN-DEPTH SECURITY ANALYSIS: CLOUD PERIMETER TO APPLICATION RUNTIME

The network topology implements a rigorous **Four-Tier Defense-in-Depth** model spanning Layer 3 (Network Routing), Layer 4 (Transport / Stateful Filtering), and Layer 7 (Application Proxy & TLS Termination).

### 2.1. Cloud Perimeter Security: VPC, Internet Gateway & Security Group

#### 1. VPC Isolation & Internet Gateway (IGW) Decoupling
* **Architectural Blueprint:** The Virtual Machine is deployed inside a private, software-defined Virtual Private Cloud (VPC) with an isolated Class-A/B IP space (`10.0.0.0/16`). The VM interface itself holds only a private internal IP (`10.0.1.5`).
* **Security Effect:** The VM interface is completely detached from physical public routing fabrics. External communication is mediated exclusively via the VPC Internet Gateway (IGW) using 1:1 Elastic IP Network Address Translation (NAT). Direct Layer 2 ARP spoofing, broadcast storming, or adjacent tenant snooping on the cloud hypervisor is physically prohibited.

#### 2. Cloud Security Group (Stateful L4 Firewall)
* **Inbound Lockdown (Zero-Trust Ingress):**
  * `TCP Port 22 (SSH):` Dedicated exclusively to administrative maintenance. In production, this rule is constrained to static corporate/bastion IP CIDR blocks, completely shielding the host from automated internet-wide SSH brute-force bots.
  * `TCP Port 80 (HTTP):` Permitted solely to satisfy Let's Encrypt automated ACME HTTP-01 domain ownership challenges and issue immediate `HTTP 301 Moved Permanently` redirects to HTTPS.
  * `TCP Port 443 (HTTPS):` The primary encrypted channel accepting web traffic and API invocations.
  * **Default-Deny for All Other Inbound Traffic:** All other TCP/UDP ports (including MariaDB `3306`, Redis `6379`, Gunicorn `8000`, and Docker `8080`) are **strictly dropped at the cloud hypervisor boundary** before any packet can consume CPU cycles or bandwidth on the VM.
* **Outbound Allow-All (Permissive Egress for System Operations):**
  * `All Traffic (0.0.0.0/0) ALLOW:` Outbound traffic is unrestricted to enable essential operational functions: fetching OS security patches (`apt update`), pulling verified Docker Hub container images, and dispatching encrypted outbound HTTPS API requests to external LLM providers (e.g., Google Gemini / OpenAI).
  * **Stateful Filtering Guarantee:** Because Cloud Security Groups are **stateful**, when an inbound client establishes an HTTPS handshake on port 443, return traffic is automatically tracked and allowed back to the client regardless of outbound rules. Conversely, allowing all outbound traffic does *not* open any corresponding inbound ports.

---

### 2.2. Host OS Local Firewall (UFW — Second Inbound Perimeter)

#### Problem
If a cloud administrative misconfiguration occurs on the Cloud Console (e.g., an operator accidentally opens all ports on the Cloud Security Group `0.0.0.0/0`), the VM could immediately become vulnerable to internet-wide port scans.

#### Solution & Security Effect
Lotus Fin enforces a redundant, host-level software firewall (`UFW` on Ubuntu Linux):
* **Independent Enforcement:** UFW acts as an autonomous second gate directly inside the Linux Kernel (`netfilter/iptables`).
* **Redundant Whitelisting:** UFW enforces an identical default-deny inbound posture, allowing only ports 22, 80, and 443. Even if the outer cloud security group fails open, the host firewall intercepts and drops packets targeting internal services.

---

### 2.3. L7 Reverse Proxy Gateway: Nginx vs. Network Layer Responsibilities

#### Boundary Clarification
It is critical to distinguish between **Layer 4 Network Filtering** (performed by Cloud Security Groups & UFW) and **Layer 7 Application Gateway Controls** (performed by Nginx):

| Architectural Layer | Component | Security Domain & Responsibility |
| :--- | :--- | :--- |
| **L3 / L4 (Network & Transport)** | **Cloud Security Group & UFW** | • Drops unauthorized IP packets before socket creation.<br>• Filters TCP ports (22, 80, 443 only).<br>• Protects against SYN floods, UDP floods, and port scanning.<br>• Operates at kernel/hypervisor level with zero CPU overhead for application runtimes. |
| **L7 (Application & Transport Security)**| **Nginx Host Reverse Proxy** | • **SSL/TLS Termination:** Offloads cryptographic overhead, enforces TLS 1.3 and forward-secret ciphers.<br>• **Layer 7 DDoS Protection:** Tracks HTTP requests per IP via `limit_req_zone` (10 req/s, burst 20).<br>• **Volumetric Payload Bounding:** Inspects `Content-Length` headers, dropping HTTP bodies $> 50\text{ MB}$ before hitting backend services.<br>• **Security Header Injection:** Injects HSTS, strict Content-Security-Policy (CSP), nosniff, and anti-clickjacking headers.<br>• **Single Origin Mediation:** Serves the pre-compiled React SPA locally ($<10\text{ms}$ response) and proxies authenticated API calls to internal Docker sockets. |

---

### 2.4. Intra-Host Container Segmentation (Docker Bridge Isolation)

#### Problem
Exposing stateful storage engines (MariaDB port 3306, Redis queue/cache port 6379) or internal application WSGI servers (Gunicorn port 8000) to public interfaces creates severe attack vectors. Adversaries can bypass application-level authorization via database brute-force attacks, remote memory corruption exploits, or direct ledger manipulation.

#### Solution
1. **Local Loopback Gateway Binding:** The internal container entrypoint (`frappe_docker-frontend-1`) binds strictly to loopback interface `127.0.0.1:8080`, rejecting non-local socket allocations.
2. **Internal Docker Network Isolation:** The relational database (`db`) and Redis workers (`redis-queue`, `redis-cache`) omit host port mappings entirely. Communication is confined to a private, non-routable Docker bridge network.
3. **Container Non-Root Execution:** Application runtimes run under dedicated unprivileged system service accounts: `frappe` (UID 1000, GID 1000) for application logic, `mysql` (UID 999) for database processes, and `redis` (UID 999) for caching.
4. **Log & Storage Governance:** Container log rotation enforces a maximum of 10 MB per file, retaining at most 3 archives ($\le 30 \text{ MB}$ total per container) and preserving dedicated 2.0 GiB virtual swap space (`swappiness = 10`) to protect against OOM database crashes.

#### Implementation Blueprint
* **Firewall Policy Configuration:**
  * Configure the operating system packet filter to drop all unsolicited inbound traffic across all interfaces.
  * Explicitly whitelist TCP ports 22, 80, and 443 with strict connection state tracking.
* **Container Bridge Specification:**
  * In the service orchestration definition, assign the database and cache services to an isolated internal bridge network (`frappe_network`).
  * Remove all host port publication directives (`ports:`) from internal services, leaving only intra-network DNS resolution.
  * Restrict container proxy port mapping exclusively to `127.0.0.1:8080:8080`.

#### Verification Evidence
Auditing the active listening sockets on the host OS via low-level socket inspection (`ss -tulpn`) confirms:
* Public listeners (`0.0.0.0`): Only Nginx reverse proxy (ports 80 and 443) and SSH daemon (port 22).
* Local loopback listener (`127.0.0.1`): Only Docker proxy at port 8080.
* Zero external listeners for ports 3306 (MariaDB) and 6379 (Redis).

---

### 2.2. Web Reverse Proxy Hardening, DDoS Mitigation & Security Headers

#### Problem
Automated vulnerability scanners, HTTP request flooding (DDoS), volumetric payload injections, and browser-targeted framing attacks (Clickjacking, MIME confusion, XSS) can degrade availability or compromise client session confidentiality.

#### Solution
1. **Client Rate Limiting:** Enforce a token bucket algorithm keyed on client IP address (`10 requests/second` with a temporary burst tolerance of 20 requests).
2. **Payload Size Bounding:** Enforce a strict 50 MB ceiling for document invoice uploads and a 16 KB restriction on structured mutation endpoints.
3. **Hardened HTTP Response Headers:** Enforce modern transport and framing policies including HTTP Strict Transport Security (HSTS), Content-Security-Policy (CSP), and nosniff protection.

#### Implementation Blueprint
* **Rate Limiting Engine:**
  * Allocate a 10 MB shared memory zone tracking binary client IP hashes to sustain rate monitoring for over 160,000 concurrent sessions.
  * Apply immediate request shedding (HTTP 429) once burst thresholds are exceeded.
* **Transport & Framing Policies:**
  * Enforce TLS 1.2 and TLS 1.3 ciphers with forward secrecy (ECDHE-ECDSA/RSA-AES-GCM).
  * Inject HSTS with a 2-year duration (`max-age=63072000`) and preload flag.
  * Restrict iframe embedding strictly to identical origins (`SAMEORIGIN`).
  * Prevent MIME-type sniffing via `nosniff`.
  * Establish a restrictive CSP permitting script and style assets exclusively from self-hosted endpoints.
* **Upstream Proxy Optimization:**
  * Disable upstream proxy buffering on streaming endpoints to facilitate real-time Server-Sent Events (SSE) from analytical engines.
  * Enforce upstream connect timeouts at 60 seconds and read timeouts at 180 seconds to accommodate complex mathematical batch computations.

---

## 3. CONTAINER RUNTIME & HOST OS HARDENING

### 3.1. Non-Root Container Execution (Principle of Least Privilege)

#### Problem
Executing application containers under the root user (UID 0) significantly amplifies container breakout vulnerabilities, allowing an attacker who exploits an unpatched library vulnerability to gain administrative control over the host kernel.

#### Solution
All application and supporting runtime containers run under dedicated, unprivileged system service accounts: `frappe` (UID 1000, GID 1000) for application logic, `mysql` (UID 999) for database processes, and `redis` (UID 999) for caching.

#### Implementation Blueprint
* **Service Account Assignment:**
  * Configure container process supervisors to execute application runtimes under UID 1000.
  * Restrict container root filesystem write permissions, ensuring persistent database and log directories retain minimal write leases exclusively for their respective service accounts.
  * Disable privilege escalation flags (`no-new-privileges:true`) in container runtime configurations.

#### Verification Evidence
Inspecting the execution context of the core application container (`docker exec -it frappe_docker-backend-1 id`) verifies an unprivileged execution context: `uid=1000(frappe) gid=1000(frappe)`.

---

### 3.2. Swap Memory Governance & Log Storage Caps

#### Problem
1. Financial data migrations and stress simulations induce transient RAM spikes. In the absence of virtual swap memory, the Linux Out-Of-Memory (OOM) Killer will abruptly terminate the database process, risking unrecoverable data corruption.
2. Uncapped container log generation can exhaust physical NVMe SSD capacity within days, triggering widespread service failures.

#### Solution
1. **Dedicated 2.0 GiB Virtual Swap:** Provision a 2 GB dedicated swap file with conservative swappiness tuning (`swappiness = 10`), preserving system stability during heavy analytical workloads.
2. **Container Log Rotation:** Enforce an immutable rotation ceiling across all container log streams: maximum 10 MB per file, retaining at most 3 historical archives ($\le 30 \text{ MB}$ total storage per container).

#### Implementation Blueprint
* **Swap Space Configuration:**
  * Allocate a continuous 2 GB contiguous block on the root storage partition with strict file permissions (`chmod 600`).
  * Format and activate swap space, committing mount entries into `/etc/fstab`.
  * Tune kernel virtual memory parameters via `/etc/sysctl.conf` to trigger swap utilization only when physical RAM falls below 10%.
* **Docker Log Rotation Directives:**
  * Configure Docker Compose logging drivers globally with `json-file` parameters: `max-size: "10m"` and `max-file: "3"`.

---

## 4. INFRASTRUCTURE SECURITY METRICS & VERIFICATION SUMMARY

| Measurement Dimension | Configured Target | Operational Threshold | Audit Status |
| :--- | :--- | :--- | :---: |
| **Public Listening Ports** | TCP 22, 80, 443 | Zero backend/database ports exposed |  **PASS (ss verified)** |
| **Frontend Bundle Footprint** | **820 KB** (Gzip: 217 KB) | $< 2.0 \text{ MB}$ total footprint |  **PASS (Vite production)** |
| **Container Log Ceiling** | $\le 30 \text{ MB}$ per container | Absolute cap preventing disk exhaustion |  **PASS (Docker daemon)** |
| **Static Delivery Latency** | $< 10 \text{ ms}$ (Host Nginx) | $< 50 \text{ ms}$ SLA |  **PASS (Curl benchmark)** |
| **API Rate Limiting Ceiling** | 10 req/s (Burst tolerance: 20) | Immediate throttling of DoS bursts |  **PASS (Nginx limit_req)** |
| **Virtual Memory Protection** | **2.0 GiB** (Swappiness: 10) | OOM crash protection for MariaDB |  **PASS (free -h verified)** |
