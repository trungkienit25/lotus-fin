/**
 * Lotus Fin - Centralized Policy Gate & Executive Constants (English Core Standard)
 * Defines verified audit policies and executive messaging specifications.
 */

export interface PolicyDefinition {
  id: string;
  name: string;
  category: string;
  riskText: string;
  riskLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  gateLevel: string;
  description: string;
  erpImpact: string;
  approvalFlow: string;
  needsInvoice: boolean;
}

export const POLICY_CATALOG: PolicyDefinition[] = [
  {
    id: "submit_sales_invoice",
    name: "Submit Sales Invoice to General Ledger",
    category: "Revenue & Receivables Recognition",
    riskText: "Risk: High",
    riskLevel: "HIGH",
    gateLevel: "Finance Officer Gate",
    description: "Transitions Sales Invoice from Draft to Submitted, generating General Ledger entries that debit Accounts Receivable and credit Revenue.",
    erpImpact: "Generates permanent GL Journal entries; invoice can no longer be deleted, only formally cancelled.",
    approvalFlow: "Accounts User verifies invoice -> Finance Officer confirms submission.",
    needsInvoice: true,
  },
  {
    id: "cancel_sales_invoice",
    name: "Cancel Submitted Sales Invoice",
    category: "Document Adjustment & Invalidation",
    riskText: "Risk: Critical",
    riskLevel: "CRITICAL",
    gateLevel: "Dual-Control (M-of-N Approval)",
    description: "Cancels an issued sales invoice, posting reverse GL entries to eliminate recorded revenue and receivables balance.",
    erpImpact: "Permanently impacts Trial Balance and Financial Statements; requires audited justification.",
    approvalFlow: "Requires dual independent approval from Finance Controller and Executive Board with digital signature.",
    needsInvoice: true,
  },
  {
    id: "send_statement_email",
    name: "Send Customer Statement of Accounts Email",
    category: "External Communication & Audit",
    riskText: "Risk: Medium",
    riskLevel: "MEDIUM",
    gateLevel: "Single User Confirm",
    description: "Dispatches automated AR statement summaries and reconciliation details to the customer's verified accounting mailbox.",
    erpImpact: "Records communication log and issues legally binding payment reconciliation notice.",
    approvalFlow: "Permitted only to verified domain mailboxes registered in customer master profiles.",
    needsInvoice: false,
  },
  {
    id: "request_disbursement",
    name: "Initiate Supplier Payment Request",
    category: "Treasury & Cash Outflow Planning",
    riskText: "Risk: High",
    riskLevel: "HIGH",
    gateLevel: "Finance Officer Gate",
    description: "Creates an accounts payable disbursement proposal based on verified supplier invoices due within the forecast horizon.",
    erpImpact: "Reserves cash allocation from liquidity pool without releasing funds from banking rail.",
    approvalFlow: "Procurement Officer initiates -> Finance Manager validates liquidity and approves disbursement cap.",
    needsInvoice: false,
  },
  {
    id: "execute_wire_transfer",
    name: "Automated Banking Wire Transfer",
    category: "Direct Treasury Rail Execution",
    riskText: "Risk: Critical (Prohibited)",
    riskLevel: "CRITICAL",
    gateLevel: "Strictly Blocked by Safety Policy",
    description: "Direct outbound disbursement of corporate funds through external commercial banking rails.",
    erpImpact: "Immediate deduction of corporate liquidity. Highest fiduciary risk if triggered autonomously.",
    approvalFlow: "Autonomous execution is strictly prohibited. Must be executed manually via corporate banking portal with hardware 2FA.",
    needsInvoice: false,
  },
  {
    id: "autonomous_reconciliation",
    name: "Autonomous Ledger Discrepancy Adjustment",
    category: "Audit Integrity & Internal Control",
    riskText: "Risk: Critical (Prohibited)",
    riskLevel: "CRITICAL",
    gateLevel: "Strictly Blocked by Safety Policy",
    description: "Autonomous reconciliation and clearance of GL vs. bank statement variances in the background without human inspection.",
    erpImpact: "Violates segregation of duties and standard international financial auditing rules.",
    approvalFlow: "Strictly prohibited on production systems. Human accounting review is mandatory.",
    needsInvoice: false,
  },
];
