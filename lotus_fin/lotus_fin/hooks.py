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
app_include_js = []  # Legacy ERP Desk customizations are not loaded by core.


# Document Events (Hooks for AI analysis & automation)
# ---------------
doc_events = {}
before_request = ["lotus_fin.runtime.boundary.enforce_request_boundary"]
after_request = ["lotus_fin.runtime.boundary.sanitize_error_response"]
page_renderer = ["lotus_fin.runtime.spa.LotusSpaPage"]

# Scheduled Tasks (Cron for AI Cash Flow Forecast & Health Check)
# ---------------
scheduler_events = {}

# Installation & Migration Hooks
# ------------------------------
after_migrate = ["lotus_fin.patches.v1_0.set_default_currency_usd.execute"]

app_home = "/app"

add_to_apps_screen = [
	{
		"name": "lotus_fin",
		"logo": "/assets/lotus_fin/logo.svg",
		"title": "Lotus Fin AI",
		"route": "/app",
	}
]

fixtures = []


# Desk Workspaces Configuration (Filtering allowed modules for Lotus Fin)
# ------------------
# Allowed core modules: Accounting, Buying, Selling, Assets, Subcontracting, Settings
ALLOWED_WORKSPACES = [
	"Settings",
	"Lotus Fin AI"
]

# Persistent Cache Keys (Preserved across clear_cache)
persistent_cache_keys = []
