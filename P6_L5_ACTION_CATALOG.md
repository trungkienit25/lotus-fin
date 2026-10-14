# LOTUS FIN P6-2: L5 ACTION CATALOG

The following actions constitute the server-side allowlisted catalog under `lotus_fin/domain/l5/policy/engine.py`.

### 1. `l5.doc.submit_sales_invoice.v1`
- **Family**: `DOCUMENT_SUBMIT`
- **Description**: Submit an approved draft Sales Invoice into submitted status.
- **Risk Level**: `HIGH`
- **Required Approval Level**: `FINANCE_OFFICER_GATE`
- **Required Roles**: `Accounts User`, `Accounts Manager`
- **Allowed Target DocTypes**: `Sales Invoice`
- **Allowed Transitions**: Docstatus `0 -> 1`
- **Reversibility**: Irreversible (requires separate cancel action)
- **Status**: Simulated In Test / Production Blocked

---

### 2. `l5.doc.cancel_sales_invoice.v1`
- **Family**: `DOCUMENT_CANCEL`
- **Description**: Cancel a submitted Sales Invoice.
- **Risk Level**: `CRITICAL`
- **Required Approval Level**: `DUAL_CONTROL_M_OF_N` (requires independent second approver)
- **Required Roles**: `Accounts Manager`
- **Allowed Target DocTypes**: `Sales Invoice`
- **Allowed Transitions**: Docstatus `1 -> 2`
- **Reversibility**: Irreversible
- **Status**: Simulated In Test / Production Blocked

---

### 3. `l5.comm.send_statement_email.v1`
- **Family**: `EXTERNAL_EMAIL_SEND`
- **Description**: Send customer account statement email to allowlisted domain.
- **Risk Level**: `MEDIUM`
- **Required Approval Level**: `SINGLE_USER_CONFIRM`
- **Required Roles**: `Accounts User`, `Accounts Manager`
- **Allowed Target DocTypes**: `Customer`, `Sales Invoice`
- **Recipient Allowlist**: `lotusfin.internal`, `clientcorp.com`, `verified-domain.com`
- **Status**: Simulated In Test / Production Blocked

---

### 4. `l5.pay.request_disbursement.v1`
- **Family**: `PAYMENT_REQUEST`
- **Description**: Generate a typed Payment Request proposal record (explicitly NOT fund disbursement).
- **Risk Level**: `HIGH`
- **Required Approval Level**: `FINANCE_OFFICER_GATE`
- **Required Roles**: `Accounts Manager`, `Treasurer`
- **Allowed Target DocTypes**: `Payment Request`, `Sales Invoice`
- **Amount Cap**: 100,000,000.0 VND
- **Allowed Currencies**: `VND`, `USD`
- **Status**: Simulated In Test / Production Blocked

---

### 5. `l5.pay.execute_wire_transfer.v1`
- **Family**: `PAYMENT_EXECUTION`
- **Description**: Actual wire transfer disbursement to banking rail.
- **Risk Level**: `CRITICAL`
- **Required Approval Level**: `BLOCKED_DISALLOWED`
- **Status**: **PERMANENTLY BLOCKED IN CANDIDATE**

---

### 6. `l5.sched.autonomous_reconciliation.v1`
- **Family**: `SCHEDULED_AUTONOMOUS_ACTION`
- **Description**: Autonomous background job for scheduled reconciliation.
- **Risk Level**: `CRITICAL`
- **Required Approval Level**: `BLOCKED_DISALLOWED`
- **Status**: **PERMANENTLY BLOCKED IN CANDIDATE**
