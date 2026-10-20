# 03 — API Integration & State Management

Lotus Fin communicates directly with the Frappe Framework REST endpoints while employing client-side **Stale-While-Revalidate (SWR)** in-memory caching to achieve instant page transitions.

---

## 📡 Backend Endpoint Integration

| Category | Endpoint | Method | Purpose |
| :--- | :--- | :--- | :--- |
| **Authentication** | `/api/method/login` | `POST` | User login session creation. |
| **Identity** | `/api/method/frappe.auth.get_logged_user` | `GET` | Current user identity and role retrieval. |
| **DocType Meta** | `/api/method/frappe.desk.form.load.getdoctype` | `GET` | Retrieve fields, permissions, and layout for any DocType. |
| **DocType CRUD** | `/api/resource/:doctype` | `GET/POST` | Query records list or create new document. |
| **Single Record** | `/api/resource/:doctype/:id` | `GET/PUT/DELETE` | Read, update, or delete an existing record. |
| **Single DocType** | `/api/resource/:doctype/:doctype` | `GET/PUT` | Load and save single settings documents (e.g. `Buying Settings`). |
| **Reports** | `/api/method/frappe.desk.query_report.run` | `POST` | Execute script/query report with dynamic filter parameters. |
| **Workspaces** | `/api/resource/Workspace/:name` | `GET` | Fetch cards, shortcuts, and link groups for workspace dashboard. |
| **Sidebar** | `/api/resource/Workspace Sidebar/:name` | `GET` | Fetch hierarchy and categorized navigation links for sidebar. |

---

## ⚡ SWR In-Memory Caching Strategy

To eliminate page flickers and unnecessary round trips when navigating across ERP modules, Lotus Fin implements three global caches:

```mermaid
flowchart LR
    A[User Action / Route Change] --> B{In-Memory Cache Hit?}
    B -->|Yes| C[Render Immediately from Cache]
    C --> D[Background Fetch / Revalidate]
    D --> E[Update State & Cache]
    B -->|No| F[Show Minimal Loader]
    F --> G[Fetch from Backend API]
    G --> E
```

### 1. `schemaCache` (`Map<string, DocTypeMeta>`)
- Stores metadata field definitions for DocTypes once loaded.
- Prevents re-fetching the 50KB+ metadata schema every time a user switches between list and form views.

### 2. `recordsCache` (`Map<string, { records: any[], totalCount: number }>`)
- Caches query results keyed by `${doctype}::${page}::${pageSize}::${filters}`.
- Allows instant back-navigation without re-triggering network spinners.

### 3. `sidebarCache` (`Map<string, SidebarItem[]>`)
- Caches the sidebar navigation structure for each workspace.
- Guarantees zero delay when switching between tabs within the same module.

---

## 🤖 Lotus AI Copilot Integration

- **Drawer Component**: `frontend/src/components/copilot/LotusCopilotDrawer.tsx`
- **Capabilities**:
  - Floating trigger button on all pages.
  - Multi-intent chat interface supporting Financial Health Analysis, Cash Flow Projections, and Scenario Analysis.
  - Quick action prompt chips for instant ERP insights.

