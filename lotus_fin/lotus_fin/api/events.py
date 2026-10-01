"""
Lotus Fin AI - Background Event Hooks & Scheduled Jobs.
"""

import frappe


def on_sales_invoice_submit(doc, method=None):
    """Triggered on Sales Invoice submit for debtor risk assessment."""
    try:
        customer = doc.customer
        outstanding = doc.outstanding_amount or doc.grand_total
        frappe.logger("lotus_fin_ai").info(
            f"[AI Insights] Sales Invoice {doc.name} submitted for customer {customer}, amount: {outstanding}"
        )
    except Exception as e:
        frappe.log_error(f"Lotus Fin AI on_sales_invoice_submit error: {str(e)}")


def on_payment_entry_submit(doc, method=None):
    """Triggered on Payment Entry submit for real-time cashflow update."""
    try:
        party = doc.party
        amount = doc.paid_amount
        payment_type = doc.payment_type
        frappe.logger("lotus_fin_ai").info(
            f"[AI Insights] Payment Entry {doc.name} ({payment_type}) submitted for party {party}, amount: {amount}"
        )
    except Exception as e:
        frappe.log_error(f"Lotus Fin AI on_payment_entry_submit error: {str(e)}")


def generate_daily_cashflow_digest():
    """Daily job to summarize 30-day projected cash flow."""
    frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running daily cash flow digest job.")


def evaluate_sme_financial_health():
    """Weekly job to inspect SME financial health."""
    frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running weekly SME financial health evaluation.")
