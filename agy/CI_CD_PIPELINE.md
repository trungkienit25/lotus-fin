# Lotus Fin — CI/CD Pipeline & Secure Secret Injection Guide

This operational manual documents the continuous delivery workflow and secret management architecture for Lotus Fin using a **Self-Hosted GitHub Actions Runner** on Linux VPS.

---

## 1. Architectural Strategy

The continuous deployment system uses a **Pull-Based Self-Hosted Runner** model:
- **Zero Inbound Ports Required**: The runner daemon on the VPS connects outbound to GitHub over HTTPS (Port 443).
- **SSH Port 22 Untouched**: The CI/CD pipeline does not interact with, depend on, or modify the server's SSH daemon or Port 22. Server administration access remains 100% uninterrupted and isolated.
- **Zero Secrets Committed**: All API keys (Gemini, OpenAI), database passwords, and SMTP credentials live exclusively inside GitHub Encrypted Secrets.

```
┌─────────────────────────────────┐
│     GitHub Platform             │
│  - Repository Secrets           │
│  - Workflow: deploy.yml         │
└────────────────┬────────────────┘
                 │ Outbound HTTPS (Port 443)
                 ▼
┌────────────────────────────────────────────────────────┐
│     Lotus Fin Linux VPS (113.192.7.68)                 │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  GitHub Actions Runner (/opt/actions-runner)      │  │
│  │  Service: actions.runner...service (active)      │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                              │
│                         ▼                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Pulls branch (release/beta-1.0)              │  │
│  │  2. Injects secrets to .env.production (chmod 600│  │
│  │  3. Rebuilds gateway image (if requested)        │  │
│  │  4. Runs: docker compose up -d                   │  │
│  │  5. Verifies health checks (Web & API ping)      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 2. GitHub Secrets Reference

Configure secrets in GitHub:
**Repository > Settings > Secrets and variables > Actions > New repository secret**

### Sensitive AI & Service Credentials
| Secret Name | Description | Example / Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Primary Google Gemini LLM API key | `AIzaSy...` |
| `OPENAI_API_KEY` | Secondary OpenAI API key (optional fallback) | `sk-proj-...` |
| `DB_PASSWORD` | MariaDB root password | `admin` (or custom strong password) |
| `ADMIN_PASSWORD` | Frappe Administrator password | `admin` (or custom strong password) |
| `LOTUS_SMTP_PASSWORD`| Gmail / SMTP application password | `btcyjmbjnykrrpol` |

### Optional Full-File Override
| Secret Name | Description |
| :--- | :--- |
| `ENV_PRODUCTION` | Optional. Paste the entire content of `.env.production`. When provided, the workflow uses this file directly. |

### Optional Configuration Secrets / Variables
| Name | Default Value | Notes |
| :--- | :--- | :--- |
| `SERVER_NAME` | `lotusfin.asia www.lotusfin.asia 113.192.7.68` | Virtual host domains |
| `PROD_PORT` | `80` | Production ingress port |
| `LOTUS_SITE` | `frontend` | Target Frappe site name |
| `LOTUS_AI_PROVIDER` | `gemini` | AI Provider (`gemini` or `openai`) |
| `LOTUS_LLM_MODEL` | `gemini-flash-latest` | Default model identifier |

---

## 3. Workflow Specification: `.github/workflows/deploy.yml`

The deployment workflow supports two execution triggers:
1. **Automatic Push Trigger**: Pushes to `release/beta-1.0` or `main` automatically deploy code and reload changed containers.
2. **Manual `workflow_dispatch` Trigger**:
   - Go to GitHub **Actions** tab > **Production CD (Self-Hosted VPS)** > Click **Run workflow**.
   - Option `rebuild_frontend`: Check to force a rebuild of the React SPA Nginx gateway container (`lotus-fin/gateway:latest`).

### Execution Steps
1. **Git Sync**: Fetches and checks out the target branch on the server (`/root/lotus-fin`).
2. **Secret Injection**: Inlines environment secrets into `/root/lotus-fin/docker/production/.env.production` using Python 3 (ensuring zero character escaping or delimiter corruption) and sets strict permissions (`chmod 600`).
3. **Packaging Gate**: Rebuilds the frontend gateway container if `rebuild_frontend` is set to `true`.
4. **Container Convergence**: Executes `docker compose --env-file .env.production -f compose.prod.yml up -d --remove-orphans`. Docker re-creates only containers whose environment or image has changed without dropping unchanged state.
5. **Automated Health Check**: Pings `http://127.0.0.1/` (Web Gateway) and `http://127.0.0.1/api/method/frappe.ping` (Frappe Backend).

---

## 4. Runner Management on VPS

The GitHub Actions runner daemon is installed as a systemd service:

```bash
# Check runner service status
systemctl status actions.runner.trungkienit25-lotus-fin.lotusfin-vps-runner.service

# View live runner logs
journalctl -u actions.runner.trungkienit25-lotus-fin.lotusfin-vps-runner.service -f

# Restart runner service
systemctl restart actions.runner.trungkienit25-lotus-fin.lotusfin-vps-runner.service
```

Runner installation path: `/opt/actions-runner`
All operations run under the `root` context, granting immediate access to Docker orchestration without socket permission errors.
