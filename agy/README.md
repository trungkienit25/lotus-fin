# 🧠 Lotus Fin Operations & Deployment Knowledge Base (KB)

Comprehensive operational guide, real-world deployment lessons, and architectural reference for deploying **Lotus Fin** on Linux Cloud Servers (VPS), multi-container orchestration with Docker, and serving the system via HTTP Port 80 and HTTPS custom domains.

---

## 📚 Knowledge Base Index

| Document | Overview |
| :--- | :--- |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | End-to-end 1-click production deployment manual, swap configuration, docker-compose orchestration, database hydration, and custom domain setup. |
| [TROUBLESHOOTING_LESSONS_LEARNED.md](TROUBLESHOOTING_LESSONS_LEARNED.md) | In-depth retrospective on challenges encountered and battle-tested solutions (Headless Frappe vs React SPA routing, `/copilot/session` proxying, edge SSL proxy headers, automated database restores). |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Complete architectural topology, multi-container networking, Nginx reverse proxy gateway rules, and security boundaries. |

---

## 🎯 Architectural Highlights

1. **Headless ERP + React 19 SPA Paradigm**:
   - Frappe/ERPNext functions exclusively as a headless backend REST/JSON API.
   - The native Frappe Desk interface (`/desk`) is completely blocked, ensuring 100% of the user experience is powered by the custom Lotus Fin React Single Page Application.
2. **Unified Single Port Entrypoint (Port 80 / 443)**:
   - An optimized Nginx Gateway container (`lotus-fin/gateway:latest`) governs all ingress traffic. Internal service ports (`:8080`, `:8000`, `:9000`, `:3306`, `:6379`) remain completely isolated within the private bridge network.
3. **Seamless Cloud Edge Proxy / CDN Integration (Tenten VCloud DNS, Cloudflare)**:
   - Dynamic `X-Forwarded-Proto` header mapping preserves external SSL/HTTPS contexts terminating at edge proxies, preventing insecure cookie drops or protocol mismatch redirects.
4. **Automated Hydration & Scientific Runtime Assembly**:
   - Automatically provisions and mounts the `lotus_fin` application package and installs essential mathematical computing dependencies (`numpy`, `pandas`, `pydantic`) across all worker containers (`queue-long`, `queue-short`, `scheduler`).
