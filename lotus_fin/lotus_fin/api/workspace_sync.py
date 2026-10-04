"""
Lotus Fin AI - Workspace & Pages Synchronization Helper.
Forces full synchronization of all 7 domain pages and Workspace shortcuts/links.
"""

import json
import os
import frappe


def sync_lotus_workspace():
    """Forces standard Lotus Fin AI workspace sync from json definition."""
    json_path = frappe.get_app_path("lotus_fin", "lotus_fin_ai", "workspace", "lotus_fin_ai", "lotus_fin_ai.json")
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return {"status": "error", "message": "JSON file not found"}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Update or create Workspace
    if frappe.db.exists("Workspace", "Lotus Fin AI"):
        ws = frappe.get_doc("Workspace", "Lotus Fin AI")
        ws.shortcuts = []
        ws.links = []
    else:
        ws = frappe.new_doc("Workspace")
        ws.name = "Lotus Fin AI"

    ws.label = data.get("label", "Lotus Fin AI")
    ws.title = data.get("title", "Lotus Fin AI")
    ws.module = "Lotus Fin AI"
    ws.icon = data.get("icon", "calculator")
    ws.indicator_color = data.get("indicator_color", "green")
    ws.public = 1
    ws.is_hidden = 0
    ws.content = data.get("content", "[]")

    for s in data.get("shortcuts", []):
        ws.append("shortcuts", {
            "label": s.get("label"),
            "link_to": s.get("link_to"),
            "type": s.get("type", "Page"),
            "color": s.get("color", "Blue"),
            "doc_view": s.get("doc_view", ""),
            "format": s.get("format", "")
        })

    for l in data.get("links", []):
        ws.append("links", {
            "label": l.get("label"),
            "link_to": l.get("link_to"),
            "link_type": l.get("link_type", "Page"),
            "type": l.get("type", "Link"),
            "onboard": l.get("onboard", 0),
            "hidden": l.get("hidden", 0),
            "is_query_report": l.get("is_query_report", 0)
        })

    ws.flags.ignore_permissions = True
    ws.flags.ignore_mandatory = True
    ws.save()

    # 2. Ensure all 7 Pages are standard and have Accounts User, Accounts Manager, System Manager roles
    pages_to_sync = [
        ("lotus-copilot", "Lotus Fin AI Copilot"),
        ("financial-health", "Financial Health"),
        ("cash-forecast", "Cash Forecast"),
        ("risk-signal", "Risk Signal"),
        ("what-if-studio", "What-If Stress-Testing Studio"),
        ("financing-copilot", "Financing Copilot & Loan Decision"),
        ("repayment-schedule", "Debt & Repayment Simulation")
    ]

    for p_name, p_title in pages_to_sync:
        if frappe.db.exists("Page", p_name):
            p_doc = frappe.get_doc("Page", p_name)
        else:
            p_doc = frappe.new_doc("Page")
            p_doc.name = p_name
            p_doc.page_name = p_name

        p_doc.title = p_title
        p_doc.module = "Lotus Fin AI"
        p_doc.standard = "Yes"
        
        # Add roles if not present
        existing_roles = [r.role for r in p_doc.roles]
        for role in ["Accounts User", "Accounts Manager", "System Manager", "All"]:
            if role not in existing_roles:
                p_doc.append("roles", {"role": role})

        p_doc.flags.ignore_permissions = True
        p_doc.save()

    # 3. Clean up any custom/cached sidebar overrides
    frappe.db.delete("Workspace", {"name": ["like", "Lotus Fin AI-%"]})
    frappe.db.commit()
    frappe.clear_cache()

    print("Successfully synchronized Lotus Fin AI Workspace & all 7 Pages!")
    return {"status": "success", "shortcuts_count": len(ws.shortcuts), "links_count": len(ws.links)}
