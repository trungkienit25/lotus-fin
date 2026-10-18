"""
Lotus Fin Migration Patch v1.0: Convert legacy VND amounts to USD at standard exchange rate (25,000 VND/USD).
Idempotent: Only divides records with amount >= 1,000,000 to prevent double conversion.
"""

import frappe
from decimal import Decimal


EXCHANGE_RATE = 25000.0


def execute() -> None:
    frappe.logger("lotus_fin").info("[Patch migrate_vnd_amounts_to_usd] Starting VND to USD amount conversion...")

    # 1. Sales Invoice
    frappe.db.sql(f"""
        UPDATE `tabSales Invoice`
        SET grand_total = grand_total / {EXCHANGE_RATE},
            outstanding_amount = outstanding_amount / {EXCHANGE_RATE},
            base_grand_total = base_grand_total / {EXCHANGE_RATE},
            total = total / {EXCHANGE_RATE},
            net_total = net_total / {EXCHANGE_RATE},
            base_net_total = base_net_total / {EXCHANGE_RATE},
            base_total = base_total / {EXCHANGE_RATE},
            currency = 'USD',
            party_account_currency = 'USD',
            conversion_rate = 1.0
        WHERE grand_total >= 1000000
    """)

    # 1.1 Sales Invoice Item
    frappe.db.sql(f"""
        UPDATE `tabSales Invoice Item`
        SET rate = rate / {EXCHANGE_RATE},
            amount = amount / {EXCHANGE_RATE},
            base_rate = base_rate / {EXCHANGE_RATE},
            base_amount = base_amount / {EXCHANGE_RATE},
            net_rate = net_rate / {EXCHANGE_RATE},
            net_amount = net_amount / {EXCHANGE_RATE},
            base_net_rate = base_net_rate / {EXCHANGE_RATE},
            base_net_amount = base_net_amount / {EXCHANGE_RATE}
        WHERE amount >= 1000000
    """)

    # 2. Purchase Invoice
    frappe.db.sql(f"""
        UPDATE `tabPurchase Invoice`
        SET grand_total = grand_total / {EXCHANGE_RATE},
            outstanding_amount = outstanding_amount / {EXCHANGE_RATE},
            base_grand_total = base_grand_total / {EXCHANGE_RATE},
            total = total / {EXCHANGE_RATE},
            net_total = net_total / {EXCHANGE_RATE},
            base_net_total = base_net_total / {EXCHANGE_RATE},
            base_total = base_total / {EXCHANGE_RATE},
            currency = 'USD',
            party_account_currency = 'USD',
            conversion_rate = 1.0
        WHERE grand_total >= 1000000
    """)

    # 2.1 Purchase Invoice Item
    frappe.db.sql(f"""
        UPDATE `tabPurchase Invoice Item`
        SET rate = rate / {EXCHANGE_RATE},
            amount = amount / {EXCHANGE_RATE},
            base_rate = base_rate / {EXCHANGE_RATE},
            base_amount = base_amount / {EXCHANGE_RATE},
            net_rate = net_rate / {EXCHANGE_RATE},
            net_amount = net_amount / {EXCHANGE_RATE},
            base_net_rate = base_net_rate / {EXCHANGE_RATE},
            base_net_amount = base_net_amount / {EXCHANGE_RATE}
        WHERE amount >= 1000000
    """)

    # 3. Payment Entry
    frappe.db.sql(f"""
        UPDATE `tabPayment Entry`
        SET paid_amount = paid_amount / {EXCHANGE_RATE},
            received_amount = received_amount / {EXCHANGE_RATE},
            base_paid_amount = base_paid_amount / {EXCHANGE_RATE},
            base_received_amount = base_received_amount / {EXCHANGE_RATE},
            paid_to_account_currency = 'USD',
            paid_from_account_currency = 'USD'
        WHERE paid_amount >= 1000000
    """)

    # 3.1 Payment Entry Reference
    frappe.db.sql(f"""
        UPDATE `tabPayment Entry Reference`
        SET allocated_amount = allocated_amount / {EXCHANGE_RATE},
            outstanding_amount = outstanding_amount / {EXCHANGE_RATE},
            total_amount = total_amount / {EXCHANGE_RATE}
        WHERE allocated_amount >= 1000000
    """)

    # 4. GL Entry
    frappe.db.sql(f"""
        UPDATE `tabGL Entry`
        SET debit = debit / {EXCHANGE_RATE},
            credit = credit / {EXCHANGE_RATE},
            debit_in_account_currency = debit_in_account_currency / {EXCHANGE_RATE},
            credit_in_account_currency = credit_in_account_currency / {EXCHANGE_RATE},
            debit_in_transaction_currency = debit_in_transaction_currency / {EXCHANGE_RATE},
            credit_in_transaction_currency = credit_in_transaction_currency / {EXCHANGE_RATE},
            account_currency = 'USD',
            transaction_currency = 'USD'
        WHERE debit >= 1000000 OR credit >= 1000000
    """)

    # 5. Accounts
    frappe.db.sql("""
        UPDATE `tabAccount`
        SET account_currency = 'USD'
        WHERE account_currency = 'VND' OR account_currency IS NULL
    """)

    # 6. Global defaults & companies
    frappe.db.set_single_value("Global Defaults", "default_currency", "USD")
    frappe.db.sql("UPDATE `tabCompany` SET default_currency = 'USD'")

    frappe.db.commit()
    frappe.clear_cache()
    frappe.logger("lotus_fin").info("[Patch migrate_vnd_amounts_to_usd] Completed successfully.")
