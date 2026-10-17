"""
Lotus Fin Migration Patch v1.0: Set Standard Operating Currency to USD.

Execution guarantees:
1. Idempotent: Can be run multiple times safely.
2. Updates Global Defaults default_currency to USD.
3. Updates Company entities (Lotus-fin, Lotus-fin (Demo)) default_currency to USD.
4. Resets Frappe cache so UI and API queries immediately reflect the new standard currency.
"""

import frappe
from typing import List


def execute() -> None:
    frappe.logger("lotus_fin").info("[Patch v1_0_set_default_currency_usd] Executing standard currency migration to USD...")

    # 1. Update Global Defaults
    frappe.db.set_single_value("Global Defaults", "default_currency", "USD")

    # 2. Update all associated company entities
    target_companies: List[str] = ["Lotus-fin", "Lotus-fin (Demo)", "Name", "Name (Demo)"]
    for company_name in target_companies:
        if frappe.db.exists("Company", company_name):
            frappe.db.set_value("Company", company_name, "default_currency", "USD", update_modified=False)
            frappe.logger("lotus_fin").info(f"Updated currency to USD for company: {company_name}")

    # 3. Update existing open invoices currency tag if needed (safe idempotent update)
    frappe.db.sql("""
        UPDATE `tabSales Invoice`
        SET currency = 'USD', party_account_currency = 'USD'
        WHERE company IN ('Lotus-fin', 'Lotus-fin (Demo)') AND (currency = 'VND' OR party_account_currency = 'VND')
    """)

    frappe.db.sql("""
        UPDATE `tabPurchase Invoice`
        SET currency = 'USD', party_account_currency = 'USD'
        WHERE company IN ('Lotus-fin', 'Lotus-fin (Demo)') AND (currency = 'VND' OR party_account_currency = 'VND')
    """)

    frappe.db.sql("""
        UPDATE `tabPayment Entry`
        SET paid_to_account_currency = 'USD', paid_from_account_currency = 'USD'
        WHERE company IN ('Lotus-fin', 'Lotus-fin (Demo)') AND (paid_to_account_currency = 'VND' OR paid_from_account_currency = 'VND')
    """)

    frappe.db.sql("""
        UPDATE `tabAccount`
        SET account_currency = 'USD'
        WHERE company IN ('Lotus-fin', 'Lotus-fin (Demo)') AND (account_currency = 'VND' OR account_currency IS NULL)
    """)

    frappe.db.sql("""
        UPDATE `tabGL Entry`
        SET account_currency = 'USD', transaction_currency = 'USD'
        WHERE company IN ('Lotus-fin', 'Lotus-fin (Demo)') AND (account_currency = 'VND' OR transaction_currency = 'VND')
    """)

    frappe.db.sql("""
        UPDATE `tabCustomer`
        SET default_currency = 'USD'
        WHERE default_currency = 'VND'
    """)

    frappe.db.sql("""
        UPDATE `tabSupplier`
        SET default_currency = 'USD'
        WHERE default_currency = 'VND'
    """)

    # 4. Commit transaction and clear system cache
    frappe.db.commit()
    frappe.clear_cache()
    frappe.logger("lotus_fin").info("[Patch v1_0_set_default_currency_usd] Completed successfully.")

