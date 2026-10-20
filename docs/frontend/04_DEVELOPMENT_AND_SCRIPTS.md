# 04 — Development, Scripts & Deployment Guide

This guide covers setting up, running, testing, building, and deploying the Lotus Fin Frontend.

---

## 🛠️ Prerequisites

- **Node.js**: v18.0.0 or higher (`node -v`)
- **npm**: v9.0.0 or higher (`npm -v`)
- **Backend**: Frappe/ERPNext backend running on `http://localhost:8080` (or configured via Vite proxy).

---

## 🚀 Quick Execution Scripts

Lotus Fin provides dedicated management scripts at the root repository directory for both Unix (Linux / macOS / WSL) and Windows (PowerShell):

### Linux / macOS / Git Bash (`run-fe.sh`)

```bash
# Start development server on http://localhost:5173
./run-fe.sh

# Or explicitly:
./run-fe.sh dev

# Run TypeScript type check and production build
./run-fe.sh build

# Install/update dependencies
./run-fe.sh install

# Run TypeScript compiler check (tsc --noEmit)
./run-fe.sh check

# Preview production build
./run-fe.sh preview

# Clean build artifacts and Vite cache
./run-fe.sh clean
```

### Windows PowerShell (`run-fe.ps1`)

```powershell
# Start development server on http://localhost:5173
.\run-fe.ps1

# Build for production
.\run-fe.ps1 build

# Type check
.\run-fe.ps1 check

# Preview production build
.\run-fe.ps1 preview

# Clean cache
.\run-fe.ps1 clean
```

---

## 💻 Manual NPM Commands

Inside the `frontend/` directory:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Run full TypeScript check and Vite build
npm run build

# Preview build
npm run preview
```

---

## 🌐 Vite Proxy Configuration

Configured in [`frontend/vite.config.ts`](file:///d:/Coding/lotus-fin/frontend/vite.config.ts):

```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
      },
      "/assets": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```

All API requests starting with `/api` or `/assets` are automatically proxied to the Frappe backend at `http://localhost:8080`.

---

## 📦 Production Build & Deployment

When running `npm run build` or `./run-fe.sh build`:
1. `tsc -b`: Validates all TypeScript types across the codebase.
2. `vite build`: Compiles, minifies, and bundles JS and CSS assets into `frontend/dist/`.
3. The resulting `dist/` directory can be served via Nginx, Caddy, or integrated directly into Frappe desk assets.

