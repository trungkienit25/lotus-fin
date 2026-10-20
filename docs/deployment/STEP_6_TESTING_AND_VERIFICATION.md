# STEP 6: TESTING AND VERIFICATION SUITE

> **Stage:** Step 6 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Execute an end-to-end 6-scenario test matrix: network connectivity, Frappe Desk authentication, AI Copilot API endpoints, automated unit test suites, What-If stress testing simulation, and runtime hardware resource audits.  
> **Prerequisites:** Completed [Step 5: React Frontend Deployment](./STEP_5_FRONTEND_DEPLOYMENT.md).  

---

## 1. 6-SCENARIO VERIFICATION MATRIX

| Scenario | Scope & Method | Expected Acceptance Verdict |
| :--- | :--- | :--- |
| **1. Network & Ping** | Test Host Nginx, port bounds, and loopback forwarding to Docker :8080 | HTTP 200 OK, latency < 50ms |
| **2. Frappe Desk** | Authenticate into ERP accounting desk, load Financial Health page | Successful login, charts and tables rendered |
| **3. AI Copilot API** | POST `/api/method/chat_copilot` with natural language financial inquiry | Valid JSON analysis returned with grounded metrics; zero permission errors |
| **4. Unit Tests** | Automated test suite execution across financial modules | Test suites PASS; hermetic test runtime < 2s |
| **5. Stress What-If** | Run multi-factor simulation scenario (sales shock -20%, payment delay +15d) | Complete 9-KPI matrix returned; zero `NaN`/`Null` values |
| **6. Resource Audit** | Profile memory and CPU utilization across all 9 containers | Docker footprint <= 1.4 GB; free RAM >= 6.0 GB (on 8GB VM) |

---

## 2. DETAILED TEST EXECUTION SCRIPTS

Connect via SSH: `ssh root@<YOUR_SERVER_IP>` and execute:

### 2.1. Scenario 1: Network & Ping Test
```bash
# Verify Host Nginx responds
curl -Is http://localhost/ | head -n 1
# Expected: HTTP/1.1 200 OK

# Verify API reverse proxy path to Docker
curl -s http://localhost/api/method/ping
# Expected: {"message":"pong"}
```

---

### 2.2. Scenario 2: Frappe Desk Authentication Test
```bash
# Test login API with administrator credentials
curl -s -X POST http://localhost/api/method/login \
  -H "Content-Type: application/json" \
  -d '{"usr": "Administrator", "pwd": "admin"}' \
  -c /tmp/cookie.txt

# Expected: {"message":"Logged In","home_page":"/app"}
```

---

### 2.3. Scenario 3: AI Copilot API Execution Test
```bash
# Query Financial Health Copilot through authenticated session cookie
curl -s -X POST http://localhost/api/method/lotus_fin.api.ai_insights.chat_copilot \
  -H "Content-Type: application/json" \
  -b /tmp/cookie.txt \
  -d '{
    "message": "Analyze corporate financial health for Lotus-fin (Demo) as of 2026-10-01",
    "company": "Lotus-fin (Demo)"
  }' | jq .
```
Verify the payload returns `status: "SUCCESS"`, structured metrics (Revenue, COGS, Gross Margin, DSCR), and an interactive UI widget payload.

---

### 2.4. Scenario 4: Automated Unit Test Suite Execution
```bash
cd ~/lotus-fin

# Run hermetic unit test suites
./run.sh test lotus_fin.tests.test_financial_health
```
Ensure all tests exit with zero failures.

---

### 2.5. Scenario 5: What-If Multi-Factor Stress Simulation
```bash
# Execute simulation engine
./run.sh simulate
```
Verify stdout returns all 9 modeled KPIs:
- Revenue variance, Gross Margin delta, Operating Cashflow, Closing Cash, Cash Runway, Net Working Capital, DSCR, Overdue Receivables, Payables Cluster.

---

### 2.6. Scenario 6: Hardware Resource Audit
```bash
# Snapshot CPU and Memory across all containers
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Verify host memory and swap state
free -h
```

Proceed to **[Step 7: GitHub Actions CI/CD Automation](./STEP_7_CICD_AUTOMATION.md)**.
