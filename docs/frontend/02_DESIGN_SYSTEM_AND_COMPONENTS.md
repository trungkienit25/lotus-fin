# 02 — Design System & UI Components

Lotus Fin is styled with a customized **TailAdmin** design system powered by **Tailwind CSS**, delivering clean typography, harmonious color tokens, and full **Dark Mode** support.

---

## 🎨 Color Tokens & Theme Configuration

Configured in [`frontend/tailwind.config.js`](file:///d:/Coding/lotus-fin/frontend/tailwind.config.js):

- **Brand Colors**:
  - `brand-500`: `#465fff` (Primary Actions, Active States, Highlight Buttons)
  - `brand-600`: `#3b4bd8` (Hover States)
  - `brand-50`: `#f2f4ff` (Subtle selection highlights)
- **Neutral / Surface**:
  - Light mode: White (`#ffffff`), Gray-50 (`#f9fafb`), Gray-100 (`#f3f4f6`), Gray-200 (`#e5e7eb`)
  - Dark mode: Gray-Dark (`#121926`), Gray-800 (`#1f2937`), Gray-900 (`#111827`)
- **Semantic Badges**:
  - `success`: `#10b981` (Emerald)
  - `warning`: `#f59e0b` (Amber)
  - `error`: `#f43f5e` (Rose)
  - `info`: `#3b82f6` (Blue)

---

## 🧭 Navigation Hierarchy

### 1. Top Navigation Bar (`TailAdminHeader.tsx`)
Located at `frontend/src/components/tailadmin/Header.tsx`, always visible across all views:
- **Logo / Home Action**: Isometric cube icon linking directly to the Module Desk (`/home`).
- **Global Search (`Ctrl+K`)**:
  - Automatically captures `Ctrl + K` or `Cmd + K` key combinations.
  - Searches through DocTypes, Workspaces, Reports, and Pages with instant live results.
- **Notification Center**: Bell icon with indicator dot and dropdown drawer.
- **User Profile**: User avatar badge, identity display, and quick Logout action.

### 2. Contextual Sidebar (`TailAdminSidebar.tsx`)
Located at `frontend/src/components/tailadmin/Sidebar.tsx`:
- Dynamically loads menu trees and categorizes them into Sections based on the currently active Workspace (Invoicing, Buying, Selling, Stock, etc.).
- Highlights active routes (`isLinkActive`) accurately across nested DocType lists and edit forms.
- Automatically collapses on mobile screens.

### 3. Module Selector Desk (`ModuleSelectorHome.tsx`)
Located at `frontend/src/pages/home/ModuleSelectorHome.tsx`:
- Replaces standard menus with a sleek app grid inspired by the official ERPNext Desk.
- Features high-contrast, colorful app icon badges with smooth hover animations.

---

## 🛠️ Reusable UI Component Library

All primitives are located in `frontend/src/components/ui/`:

| Component | Path | Description |
| :--- | :--- | :--- |
| `Button` | `components/ui/button/Button.tsx` | Standard buttons with `primary`, `outline`, `sm`, `md` variants and icon slots. |
| `Badge` | `components/ui/badge/Badge.tsx` | Status badges (`success`, `warning`, `error`, `info`, `light`). |
| `Modal` | `components/ui/modal/index.tsx` | Accessible modal dialogs with backdrop blur and smooth fade transitions. |
| `Table` | `components/ui/table/index.tsx` | Composable `TableHeader`, `TableRow`, `TableCell`, `TableBody` for high-density ERP data. |
| `EmptyState` | `components/tailadmin/EmptyState.tsx` | TailAdmin placeholder illustration for empty tables and searches. |
| `FilterBar` | `components/tailadmin/FilterBar.tsx` | Modular search, sort dropdown, and condition chips. |
| `ListToolbar` | `components/tailadmin/ListToolbar.tsx` | Bulk selection actions, export buttons, and refresh controls. |

