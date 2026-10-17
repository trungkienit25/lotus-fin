# 📐 RESTful API 接口设计规范 — Lotus Fin

本文档定义了 Lotus Fin 各服务、控制器以及后台作业中实现 RESTful API 接口的统一定义规范与标准。

---

## 1. URL 结构与资源命名规范

### 1.1. 版本化与路由层级
所有对外 API 均遵循版本化前缀规范：
```
/api/v{version}/{resource-collection}[/{resource-id}][/{sub-resource}]
```
示例：
- `/api/v1/copilot/query`
- `/api/v1/invoices`
- `/api/v1/cashflow/forecast`
- `/api/v1/debts/reminders`

### 1.2. 命名规则
- **使用复数名词：** 集合资源一律使用复数名词：`/invoices`, `/users`, `/reports`。
- **Kebab-Case 短横线命名：** 多单词资源必须使用小写短横线连接：`/cash-forecasts`, `/risk-signals`, `/debt-reminders`。
- **禁止在 URI 中出现动词：**
  - ❌ 错误：`POST /api/v1/getInvoices`, `POST /api/v1/calculateCash`
  - ✅ 正确：`GET /api/v1/invoices`, `POST /api/v1/cash-forecasts/simulations`

---

## 2. HTTP 请求动词映射

| 请求方法 | 幂等性 | 适用场景 | 标准状态码 |
| :--- | :---: | :--- | :--- |
| `GET` | 是 | 获取资源实体或列表展示 | `200 OK` |
| `POST` | 否 | 创建新实体或触发事务性业务操作 | `201 Created` / `200 OK` |
| `PUT` | 是 | 全量覆盖替换目标资源 | `200 OK` |
| `PATCH`| 是 | 部分更新目标资源的指定属性 | `200 OK` |
| `DELETE`| 是 | 移除目标资源 | `200 OK` / `204 No Content` |

---

## 3. 标准 JSON 响应封装规范

所有 API 均以统一的 JSON 结构进行响应封包：

### 3.1. 成功响应 (Success Response)
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

### 3.2. 异常与错误响应 (Error Response)
```json
{
  "success": false,
  "error": {
    "code": "POLICY_GATE_RESTRICTED",
    "message": "作废销售发票需经财务总监与董事会双重授权。",
    "riskLevel": "CRITICAL",
    "details": {}
  },
  "timestamp": "2026-10-17T17:00:00Z"
}
```
