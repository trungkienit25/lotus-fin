# LOTUS FIN CLOUD DEPLOYMENT GUIDE (END-TO-END LINUX SERVER)



> **System:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  

> **Target Environment:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / Debian 12)  

> **Minimum Hardware:** 2 vCPU — 4 GB RAM (8 GB Recommended) — 40 GB SSD  

> **Architecture:** Single VM (Host Nginx Reverse Proxy + React SPA + 9 Docker Containers Frappe/ERPNext)  



---



## DEPLOYMENT ROADMAP & CHAPTER INDEX



This guide is structured into **7 modular, step-by-step verification procedures**:



| Step | Detailed Specification | Focus & Technical Scope | Status |

| :---: | :--- | :--- | :---: |

| **Step 1** | [**STEP_1_SERVER_SURVEY.md**](./STEP_1_SERVER_SURVEY.md) | Initial server audit: CPU, RAM, disk, active ports, firewall, and network outbound connectivity. | Completed |

| **Step 2** | [**STEP_2_OS_HARDENING_AND_DOCKER.md**](./STEP_2_OS_HARDENING_AND_DOCKER.md) | Host OS hardening, 2GB Swap configuration, Docker CE & Compose v2, and log rotation caps. | Ready |

| **Step 3** | [**STEP_3_BACKEND_DEPLOYMENT.md**](./STEP_3_BACKEND_DEPLOYMENT.md) | Provision 9 Frappe/ERPNext containers, mount lotus_fin, run database migrations, and load fixtures. | Ready |

| **Step 4** | [**STEP_4_NGINX_AND_SSL_CONFIG.md**](./STEP_4_NGINX_AND_SSL_CONFIG.md) | Host Nginx reverse proxy, WebSocket support, 180s proxy timeouts, rate limiting, and Let's Encrypt TLS. | Ready |

| **Step 5** | [**STEP_5_FRONTEND_DEPLOYMENT.md**](./STEP_5_FRONTEND_DEPLOYMENT.md) | React frontend build (Vite SPA), deployment to /var/www/lotus-fin-fe, and static asset caching. | Ready |

| **Step 6** | [**STEP_6_TESTING_AND_VERIFICATION.md**](./STEP_6_TESTING_AND_VERIFICATION.md) | 6 verification test scenarios: Ping, Frappe Desk, AI Copilot API, Suite tests, What-If simulation, resource audit. | Ready |

| **Step 7** | [**STEP_7_CICD_AUTOMATION.md**](./STEP_7_CICD_AUTOMATION.md) | Automated GitHub Actions CI/CD deployment pipeline triggering on branch pushes. | Ready |



---



## SYSTEM ARCHITECTURE OVERVIEW



```text
[ Public Internet / Clients & Administrators ]

                       |

                       v

+----------------------------------------------------------------------------------------+

| CLOUD PROVIDER VPC (Virtual Private Cloud - 10.0.0.0/16)                               |

|                                                                                        |

|   +--------------------------------------------------------------------------------+   |

|   | VPC INTERNET GATEWAY (IGW)                                                     |   |

|   | - Public IPv4 Allocation / Elastic IP (e.g., 203.0.113.10)                     |   |

|   | - 1:1 NAT Routing & Internet Ingress/Egress Gateway                            |   |

|   +--------------------------------------+-----------------------------------------+   |

|                                          | Route: 0.0.0.0/0 via IGW                    |

|                                          v                                             |

|   +--------------------------------------------------------------------------------+   |

|   | PUBLIC DMZ SUBNET (10.0.1.0/24)                                                |   |

|   |                                                                                |   |

|   |   +------------------------------------------------------------------------+   |   |

|   |   | CLOUD SECURITY GROUP (Stateful Packet Filter)                          |   |   |

|   |   | ---------------------------------------------------------------------- |   |   |

|   |   | [INBOUND RULES]                                                        |   |   |

|   |   | * TCP 22  (SSH)   --> Whitelisted Admin CIDR (Remote Management)       |   |   |

|   |   | * TCP 80  (HTTP)  --> 0.0.0.0/0 (SSL Certbot & HTTPS Redirect)         |   |   |

|   |   | * TCP 443 (HTTPS) --> 0.0.0.0/0 (Encrypted Web Traffic & API)          |   |   |

|   |   | * ALL OTHER INBOUND PORTS (3306, 6379, 8000, 8080) --> DROP / DENY ALL |   |   |

|   |   | ---------------------------------------------------------------------- |   |   |

|   |   | [OUTBOUND RULES]                                                       |   |   |

|   |   | * ALL TRAFFIC (0.0.0.0/0) --> ALLOW ALL (OS Updates, GitHub, LLM API)  |   |   |

|   |   +-----------------------------------+------------------------------------+   |   |

|   |                                       |                                        |   |

|   |                                       v                                        |   |

|   |   +------------------------------------------------------------------------+   |   |

|   |   | COMPUTE VIRTUAL MACHINE (Ubuntu 22.04 LTS / Private IP: 10.0.1.5)      |   |   |

|   |   |                                                                        |   |   |

|   |   |   +----------------------------------------------------------------+   |   |   |

|   |   |   | HOST OS LOCAL FIREWALL (UFW - Second Inbound Perimeter)        |   |   |   |

|   |   |   | - Default Inbound: DENY ALL | Default Outbound: ALLOW ALL      |   |   |   |

|   |   |   | - Explicit Allow: TCP 22, TCP 80, TCP 443                      |   |   |   |

|   |   |   +-------------------------------+--------------------------------+   |   |   |

|   |   |                                   |                                    |   |   |

|   |   |                                   v                                    |   |   |

|   |   |   +----------------------------------------------------------------+   |   |   |

|   |   |   | NGINX HOST REVERSE PROXY GATEWAY (L7 Application Gateway)      |   |   |   |

|   |   |   | - SSL Termination (TLS 1.2 / 1.3 Strict Ciphers)               |   |   |   |

|   |   |   | - DDoS Rate Limiting: 10 req/s per IP, burst=20 nodelay        |   |   |   |

|   |   |   | - Volumetric Payload Bounding: Max 50MB (Files) / 16KB (JSON)  |   |   |   |

|   |   |   | - Security Headers: HSTS, CSP strict, nosniff, SAMEORIGIN      |   |   |   |

|   |   |   +-------+----------------------------------------+---------------+   |   |   |

|   |   |           | proxy_pass http://127.0.0.1:8080       | Static Web Files  |   |   |

|   |   |           v                                        v                   |   |   |

|   |   |   +----------------------------------+   +-------------------------+   |   |   |

|   |   |   | DOCKER BRIDGE NETWORK            |   | /var/www/lotus-fin-fe   |   |   |   |

|   |   |   | (Internal Subnet 172.x.0.0/16)   |   | (React Vite Dist Bundle)|   |   |   |

|   |   |   |                                  |   +-------------------------+   |   |   |

|   |   |   |  [frappe-frontend-1] (:8080)     |                                 |   |   |

|   |   |   |        | Gunicorn WSGI (:8000)   |                                 |   |   |

|   |   |   |        v                         |                                 |   |   |

|   |   |   |  [frappe-backend-1] (App Core)   |                                 |   |   |

|   |   |   |        |                         |                                 |   |   |

|   |   |   |        +---------------+---------+                                 |   |   |

|   |   |   |        v               v         v                                 |   |   |

|   |   |   |  [mariadb:11.8]  [redis-queue] [redis-cache]                       |   |   |

|   |   |   |  (Port :3306)    (Port :6379)  (Port :6379)                        |   |   |

|   |   |   |  [NO HOST BIND]  [NO HOST BIND][NO HOST BIND]                      |   |   |

|   |   |   +----------------------------------+                                 |   |   |

|   |   +------------------------------------------------------------------------+   |   |

|   +--------------------------------------------------------------------------------+   |

+----------------------------------------------------------------------------------------+

```






---



## FREQUENT OPERATIONAL COMMANDS CHEATSHEET



From ~/lotus-fin on the server:



`ash

# Start container cluster

./run.sh up



# Sync latest codebase into backend containers and run DB migrations

./run.sh sync



# Seed demo accounting dataset

./run.sh demo



# Run What-If financial simulation scenario across 9 KPIs

./run.sh simulate



# Execute automated test suites

./run.sh test lotus_fin.tests.test_financial_health



# Inspect real-time container resource utilization

docker stats --no-stream



# Clean up build caches and dangling images

docker system prune -f

`

