# Lotus Fin — Modern Frontend Documentation

Welcome to the **Lotus Fin** Frontend documentation. Lotus Fin is built as a next-generation Enterprise Resource Planning (ERP) desk interface, designed with a **Dynamic Runtime Engine** that auto-renders 100% of ERPNext/Frappe DocTypes, Workspaces, Reports, and Custom Pages while offering a modern, sleek **TailAdmin & Tailwind CSS** user experience.

---

## 📑 Documentation Structure

| Document | Topic | Description |
| :--- | :--- | :--- |
| [**01. Architecture & Engine**](./01_ARCHITECTURE_AND_ENGINE.md) | Core Runtime Engine | How Lotus Fin interprets Frappe DocType schemas dynamically and maps them to pure React controls. |
| [**02. Design System & Components**](./02_DESIGN_SYSTEM_AND_COMPONENTS.md) | TailAdmin UI & Controls | Layout system, ERPNext-style navigation bar (Ctrl+K), Sidebar, List Toolbar, Form views, and Dark Mode. |
| [**03. API & Data Layer**](./03_API_INTEGRATION_AND_CACHING.md) | REST APIs & In-Memory Cache | Interaction with Frappe Desk backend, SWR In-Memory Caching strategy, AuthProvider, and Lotus AI Copilot. |
| [**04. Development & Scripts**](./04_DEVELOPMENT_AND_SCRIPTS.md) | Developer Quickstart | Using `run-fe.sh` / `run-fe.ps1`, local development workflow, type checking, and production deployment. |

---

## 🚀 Key Architectural Highlights

1. **Zero Hardcoded Forms / Lists**: All standard and custom DocTypes (`Customer`, `Sales Invoice`, `Purchase Order`, `Buying Settings`, etc.) are rendered dynamically from Frappe metadata (`frappe.desk.form.load.getdoctype`).
2. **ERPNext-Grade Navigation**:
   - **Global Search (`Ctrl+K`)**: Instant lookup across all DocTypes, Workspaces, Reports, and Pages.
   - **Module Selector Desk**: Vibrant visual grid matching the Frappe/ERPNext Desk experience.
   - **Contextual Sidebar**: Dynamically loads menu trees and link cards for each active workspace.
3. **High Performance SWR Caching**: Eliminates redundant network requests and page flicker when navigating between modules, forms, and list views.
4. **Pure Tailwind CSS / TailAdmin**: Fully decoupled from legacy monolithic UI frameworks, supporting both Light and Dark themes natively.
5. **Integrated AI Copilot**: Native floating AI drawer communicating with Lotus Fin AI backends for real-time financial insights and workflow automation.

---

## ⚡ Quick Start

```bash
# Run with Bash (Linux / macOS / Git Bash)
./run-fe.sh

# Or run with PowerShell (Windows)
.\run-fe.ps1
```

The application will be available at **`http://localhost:5173`** and proxies backend API calls to **`http://localhost:8080`**.

