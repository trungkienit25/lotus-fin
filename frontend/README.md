# Lotus Fin — Modern ERP Frontend

Lotus Fin is a React 18, TypeScript, and Tailwind CSS (TailAdmin) frontend for ERPNext and Frappe Framework. It features a metadata-driven dynamic runtime engine that auto-renders 100% of ERPNext DocTypes, Workspaces, Reports, and Pages with zero hardcoded form views.

---

## 📚 Comprehensive Documentation

Full architecture, design system, API integration, and development guides are located in [`docs/frontend/`](../docs/frontend/README.md):

- [**01. Dynamic Metadata Engine & Architecture**](../docs/frontend/01_ARCHITECTURE_AND_ENGINE.md)
- [**02. TailAdmin Design System & Components**](../docs/frontend/02_DESIGN_SYSTEM_AND_COMPONENTS.md)
- [**03. API Integration & State Management (SWR)**](../docs/frontend/03_API_INTEGRATION_AND_CACHING.md)
- [**04. Development, Scripts & Deployment**](../docs/frontend/04_DEVELOPMENT_AND_SCRIPTS.md)

---

## ⚡ Quick Start

From the repository root:

```bash
# Start frontend dev server (Linux / macOS / Git Bash)
./run-fe.sh

# Or on Windows PowerShell:
.\run-fe.ps1
```

Or from inside `frontend/`:

```bash
npm install
npm run dev
```

Server will run on **`http://localhost:5173`** and proxy API calls to **`http://localhost:8080`**.
