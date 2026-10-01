app_name = "lotus_fin"
app_title = "Lotus Fin"
app_publisher = "Lotus Fin Team"
app_description = "SME Financial Management Core with AI Key Report Pipeline on Frappe Framework"
app_email = "dev@lotusfin.vn"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/lotus_fin/css/lotus_fin.css"
app_include_js = "/assets/lotus_fin/js/lotus_fin.js"

# Document Events (Hooks for AI analysis & automation)
# ---------------
doc_events = {
	"Sales Invoice": {
		"on_submit": "lotus_fin.api.ai_insights.on_sales_invoice_submit"
	},
	"Payment Entry": {
		"on_submit": "lotus_fin.api.ai_insights.on_payment_entry_submit"
	}
}

# Scheduled Tasks (Cron for AI Cash Flow Forecast & Health Check)
# ---------------
scheduler_events = {
	"daily": [
		"lotus_fin.api.ai_insights.generate_daily_cashflow_digest"
	],
	"weekly": [
		"lotus_fin.api.ai_insights.evaluate_sme_financial_health"
	]
}

# Fixtures to sync configuration across environments
# ---------------
fixtures = [
	{
		"doctype": "Custom HTML Block",
		"filters": [["name", "in", ["Lotus Fin AI Widget"]]]
	}
]

# Desk Workspaces Configuration (Filtering allowed modules for Lotus Fin)
# ------------------
# Allowed core modules: Accounting, Buying, Selling, Assets, Subcontracting, Settings
ALLOWED_WORKSPACES = [
	"Accounting",
	"Buying",
	"Selling",
	"Assets",
	"Subcontracting",
	"Settings",
	"Lotus Fin AI"
]
