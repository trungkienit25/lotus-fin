# 🔀 Git Workflow & Branch Governance — Lotus Fin

This policy outlines repository branch structures, protection rules, and Conventional Commit requirements for the Lotus Fin project.

---

## 1. Branch Topology

```
  main (Production — Certified stable releases)
    │
    ├──────────────────── staging (Pre-production / Final UAT)
    │                       ▲
    │                       │ Merge upon test pass
    │                       │
    └──────────────────── develop (Integration Testing)
                            ▲
                            │ Merge for integration check
                            │
                    ┌───────┴───────┐
                    │               │
                 feat/            fix/
               cashflow-engine   rate-shock-calc
```

The code promotion lifecycle moves in a single forward direction:
```
feature/fix branch -> develop (integration test) -> staging (UAT) -> main (Production)
```

---

## 2. Branch Roles & Protection Rules

| Branch | Lifecycle / Purpose | Base | Target Merge | Deployment Target |
| :--- | :--- | :--- | :--- | :--- |
| **`main`** | Certified production-ready code | — | `staging` only | Production Server (Port 80) |
| **`staging`** | Pre-production & UAT verification | `main` | Verified `feature/*` / `fix/*` | Staging Cluster |
| **`develop`** | Active integration test branch | `main` | Feature branches | Local / CI Test Server |
| **`feat/*`** | Feature development | `develop` | `develop` -> `staging` | Local Dev |
| **`fix/*`** | Bug remediation | `develop` | `develop` -> `staging` | Local Dev |
| **`hotfix/*`** | Production critical emergency fixes | `main` | Directly to `staging` & `main` | Hotfix Deployment |

### Protection Enforcements:
1. **Direct pushes are strictly prohibited** to `main`, `staging`, and `develop`.
2. All pull requests require a clean test pass (`npm run build` & Python test suites) before merging.

---

## 3. Commit Message Standard (Conventional Commits)

Format:
```
<type>(<scope>): <concise description in lowercase>
```

Types:
- `feat`: A new user-facing feature or domain capability.
- `fix`: A bug fix in existing modules.
- `docs`: Documentation updates only.
- `refactor`: Code changes that neither fix a bug nor add a feature.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Build process, package updates, or tool configurations.
