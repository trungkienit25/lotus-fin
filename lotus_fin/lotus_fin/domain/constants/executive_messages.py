"""
Lotus Fin - Executive Dictionary & Policy Constants (English Core Standard).
Centralized repository of executive messages, business glossaries,
and policy safety verdicts across Backend and AI Copilot services.
Configured with an English-first standard for international enterprise readiness.
"""

from typing import Any, Dict

# Business glossary: maps raw technical symbols/keys to human-friendly executive English terms
TECHNICAL_KEY_GLOSSARY: Dict[str, str] = {
    "STRICT_BASELINE_V1": "Standardized figures based on verified commercial invoices issued",
    "has_constituent_deficit: false": "Cash balance is secure; no constituent bank accounts show a deficit",
    "has_constituent_deficit: true": "Constituent bank account deficit identified",
    "has_constituent_deficit": "Constituent account deficit condition",
    "shortfall_events: []": "No projected cash shortfall risks detected within the next 30 days",
    "shortfall_events": "Cash shortfall risk alerts",
    "NO_CONFIRMED_SETTLEMENT_EVENTS": "No confirmed settlement schedule recorded in this period",
    "FORECAST_UNAVAILABLE": "Cash flow data does not meet forecasting qualification criteria",
    "TRADE_ONLY": "Independent commercial accounting scope",
    "VALIDATION_ERROR": "Ledger reconciliation variance",
    "INCONSISTENT_DATA": "Ledger figures not fully synchronized",
    "UNAVAILABLE": "Temporarily unavailable",
    "AWAITING_DATA": "Awaiting ledger data synchronization",
    "reason_code": "Classification Code",
    "source_label": "Audit Data Source",
    "action_name": "Business Action",
    "risk_level": "Risk Level",
    "required_approval_level": "Mandatory Approval Gate",
    "consequence_description": "Ledger Impact Description",
}

# Policy evaluation definitions & verdicts for Safety Gate (Dual-Control) in English
POLICY_GATE_VERDICTS: Dict[str, Dict[str, Any]] = {
    "submit_sales_invoice": {
        "already_submitted": {
            "status": "warning",
            "verdict_title": "Invoice Already Submitted",
            "verdict_detail": "Sales Invoice {invoice} is already in Submitted status. Duplicate submission is rejected.",
            "risk_badge": "Risk: High",
            "action_allowed": False,
            "approval_required": "Unavailable due to document status conflict.",
        },
        "eligible": {
            "status": "success",
            "verdict_title": "Eligible for Submission & Ledger Posting",
            "verdict_detail": "Integrity validation passed for invoice {invoice}. Submission will post Debit to Accounts Receivable and Credit to Revenue in the General Ledger.",
            "risk_badge": "Risk: High",
            "action_allowed": True,
            "approval_required": "Requires single-level approval from an Accounts User or Accounts Manager.",
        },
    },
    "cancel_sales_invoice": {
        "is_draft": {
            "status": "info",
            "verdict_title": "Document Not Yet Posted to Ledger",
            "verdict_detail": "Sales Invoice {invoice} is in Draft status and can be discarded directly without reverse GL journal entries.",
            "risk_badge": "Risk: Low",
            "action_allowed": True,
            "approval_required": "Direct deletion permitted for draft records.",
        },
        "dual_control_required": {
            "status": "restricted",
            "verdict_title": "Dual-Control Policy Gate Triggered",
            "verdict_detail": "Cancelling invoice {invoice} permanently reverses revenue and receivables entries in {company}'s General Ledger, directly altering financial statements.",
            "risk_badge": "Risk: Critical",
            "action_allowed": False,
            "approval_required": "Requires dual independent sign-offs (Finance Controller & Board Member) with written audit justification.",
        },
    },
    "send_statement_email": {
        "default": {
            "status": "success",
            "verdict_title": "Approved for Dispatch Post-Confirmation",
            "verdict_detail": "Customer statement summaries may only be dispatched to verified recipient domains registered in partner profiles.",
            "risk_badge": "Risk: Medium",
            "action_allowed": True,
            "approval_required": "Sender verification required (Single User Confirm).",
        }
    },
    "request_disbursement": {
        "default": {
            "status": "success",
            "verdict_title": "Eligible for Payment Proposal",
            "verdict_detail": "Payment proposal verified against legitimate purchase invoices to support 30-day liquidity and cash planning.",
            "risk_badge": "Risk: High",
            "action_allowed": True,
            "approval_required": "Accounts Payable Officer initiates proposal -> Finance Manager approves budget cap.",
        }
    },
    "execute_wire_transfer": {
        "blocked": {
            "status": "blocked",
            "verdict_title": "Autonomous Wire Transfers Strictly Blocked",
            "verdict_detail": "To preserve company treasury assets, autonomous AI and background jobs are prohibited from executing outbound bank transfers.",
            "risk_badge": "Risk: Critical (Prohibited)",
            "action_allowed": False,
            "approval_required": "Strictly blocked. Disbursement must be executed manually via corporate banking with hardware token / 2FA.",
        }
    },
    "autonomous_reconciliation": {
        "blocked": {
            "status": "blocked",
            "verdict_title": "Autonomous Ledger Adjustments Prohibited",
            "verdict_detail": "Discrepancies between general ledger balances and bank statements require human review and documentation.",
            "risk_badge": "Risk: Critical (Prohibited)",
            "action_allowed": False,
            "approval_required": "Strictly blocked on production environments per statutory audit standards.",
        }
    },
}

# Standard template for Debt Reminder letters in English
DEBT_REMINDER_TEMPLATE = (
    "Dear Finance & Accounting Team - {customer_name},\n\n"
    "We hope this message finds your business thriving.\n\n"
    "We are writing to provide a statement reconciliation and request payment for the following invoice:\n"
    "• Invoice ID: {invoice_id}\n"
    "• Payment Due Date: {due_date}\n"
    "• Outstanding Balance: {amount}\n"
    "{overdue_notice}\n\n"
    "We kindly ask that you review these details and arrange settlement within 3 to 5 business days to keep our mutual financial planning aligned.\n\n"
    "If payment has already been initiated, please disregard this notice and reply with the payment confirmation receipt so we can update our ledger.\n\n"
    "Thank you for your continued partnership!\n"
    "Corporate Accounting & Treasury Department"
)
