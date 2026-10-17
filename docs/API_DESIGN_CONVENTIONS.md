# 📐 RESTful API Design Specification — Lotus Fin

This specification defines conventions and standards for implementing RESTful API endpoints across Lotus Fin services, controllers, and background workers.

---

## 1. URL Structure & Resource Naming Conventions

### 1.1. Versioning & Route Hierarchy
All API endpoints follow a standard versioned prefix:
```
/api/v{version}/{resource-collection}[/{resource-id}][/{sub-resource}]
```
Examples:
- `/api/v1/copilot/query`
- `/api/v1/invoices`
- `/api/v1/cashflow/forecast`
- `/api/v1/debts/reminders`

### 1.2. Naming Rules
- **Plural Nouns:** Always use plural nouns for collections: `/invoices`, `/users`, `/reports`.
- **Kebab-Case:** Multi-word resources must use lowercase hyphen-separated naming: `/cash-forecasts`, `/risk-signals`, `/debt-reminders`.
- **No Verbs in URIs:** 
  - ❌ Incorrect: `POST /api/v1/getInvoices`, `POST /api/v1/calculateCash`
  - ✅ Correct: `GET /api/v1/invoices`, `POST /api/v1/cash-forecasts/simulations`

---

## 2. HTTP Method Mapping

| Method | Idempotent | Usage | Standard Status |
| :--- | :---: | :--- | :--- |
| `GET` | Yes | Retrieve resource or collection representation | `200 OK` |
| `POST` | No | Create a new entity or trigger a transactional operation | `201 Created` / `200 OK` |
| `PUT` | Yes | Full replacement of target resource | `200 OK` |
| `PATCH`| Yes | Partial update of resource attributes | `200 OK` |
| `DELETE`| Yes | Remove target entity | `200 OK` / `204 No Content` |

---

## 3. Standard JSON Response Envelope

All API endpoints encapsulate responses in a predictable JSON structure:

### 3.1. Success Response
```json
{
  "success": true,
  "data": {
    "invoiceId": "ACC-SINV-2026-00005",
    "customerName": "Grant Plastics Ltd.",
    "outstandingAmount": 20000.0,
    "currency": "VND",
    "status": "OVERDUE"
  },
  "timestamp": "2026-10-17T17:00:00Z"
}
```

### 3.2. Error Response
```json
{
  "success": false,
  "error": {
    "code": "POLICY_GATE_RESTRICTED",
    "message": "Cancelling invoice requires dual-control independent sign-offs.",
    "riskLevel": "CRITICAL",
    "details": {}
  },
  "timestamp": "2026-10-17T17:00:00Z"
}
```
