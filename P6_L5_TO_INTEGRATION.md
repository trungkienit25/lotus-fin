# LOTUS FIN P6-2: L5 TO INTEGRATION GUIDE

## 1. Integration Boundary & Readiness

L5 components are implemented in modular isolation:
- Backend: [`lotus_fin.domain.l5`](file:///e:/lotus-fin/lotus_fin/lotus_fin/domain/l5)
- Frontend: [`frontend/src/pages/copilot/l5`](file:///e:/lotus-fin/frontend/src/pages/copilot/l5)

### Prerequisites for Connecting to Shared Copilot Mount (Post P6-0)

1. **Shared Mount Isolation**:
   No modifications were made to existing Copilot mount files ([`LotusCopilotPage.tsx`](file:///e:/lotus-fin/frontend/src/pages/copilot/LotusCopilotPage.tsx), [`InvoiceActionsTabView.tsx`](file:///e:/lotus-fin/frontend/src/pages/copilot/components/InvoiceActionsTabView.tsx)) while P6-0 is in progress.

2. **Frontend Wiring**:
   Import [`L5ActionPreviewPanel`](file:///e:/lotus-fin/frontend/src/pages/copilot/l5/L5ActionPreviewPanel.tsx) into the Copilot Action drawer or tabs when an L5 proposal envelope is received.

3. **Backend Route Registration**:
   Expose Frappe-whitelisted endpoints:
   - `POST /api/method/lotus_fin.l5.prepare_action`
   - `POST /api/method/lotus_fin.l5.approve_action`
   - `POST /api/method/lotus_fin.l5.execute_action`
   - `POST /api/method/lotus_fin.l5.reconcile_action`

4. **Production Side Effect Qualification**:
   Production adapters for live document mutation, external email dispatch, bank transfer, and background schedulers must remain **BLOCKED** until individual qualification audits and cryptographic signer gates are approved.
