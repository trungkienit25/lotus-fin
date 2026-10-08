// Lotus Fin Cash Forecast Copilot Page Controller & UI (Google Material 3 DNA)
frappe.provide("lotus_fin.cash_forecast");

frappe.pages["cash-forecast"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Cash Flow Forecast & Runway (AI002)"),
		single_column: true
	});

	wrapper.cash_forecast = new lotus_fin.cash_forecast.Controller(wrapper);
};

frappe.pages["cash-forecast"].refresh = function (wrapper) {
	if (wrapper.cash_forecast) {
		wrapper.cash_forecast.refresh();
	}
};

// Safe pure currency formatter (no HTML tags)
function format_money(val, currency = "VND") {
	if (val === null || val === undefined || isNaN(val)) return "0 " + currency;
	return Math.round(Number(val)).toLocaleString("vi-VN") + " " + currency;
}

lotus_fin.cash_forecast.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.financial_as_of = "2026-09-26";
		this.request_generation = 0;
		this.data = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.load_default_company_and_fetch();
	}

	setup_breadcrumbs() {
		frappe.breadcrumbs.add("Accounts");
	}

	setup_filters() {
		const me = this;

		// 1. Company selector
		this.company_field = this.page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"),
			change() {
				const val = me.company_field.get_value();
				if (val !== me.current_company) {
					me.current_company = val;
					me.on_company_change();
				}
			}
		});

		// 2. Financial As-Of Date
		this.as_of_field = this.page.add_field({
			fieldname: "financial_as_of",
			label: __("As of Date"),
			fieldtype: "Date",
			default: "2026-09-26",
			change() {
				me.financial_as_of = me.as_of_field.get_value();
				me.fetch_forecast();
			}
		});

		// Navigation buttons
		this.page.add_inner_button(__("🤖 Lotus Copilot"), function () {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("⚠️ Risk Signals (AI003)"), function () {
			frappe.set_route("risk-signal");
		});

		this.page.add_inner_button(__("🔮 What-If Studio (AI004)"), function () {
			frappe.set_route("what-if-studio");
		});

		this.page.set_primary_action(__("Run Cash Forecast"), function () {
			me.fetch_forecast(true);
		}, "octicon octicon-sync");
	}

	setup_dom() {
		this.page.main.empty();
		this.container = $(`
			<div class="lotus-financial-health-container" style="max-width: 1280px; margin: 0 auto;">
				<!-- Header Banner (Material 3 Style) -->
				<div class="lotus-fh-header-card">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<div class="d-flex align-items-center gap-2 mb-2">
								<span class="lotus-brand-badge">Lotus Fin • Cash Forecast & Runway (AI002)</span>
								<span class="lotus-badge lotus-badge-primary">Horizon: 30 Days</span>
							</div>
							<h1 class="lotus-fh-title">💧 ${__("Cash Flow Forecast & Liquidity Runway")}</h1>
							<p class="lotus-fh-subtitle">${__("Deterministic 30-day cash trajectory, independent ledger balancing, and shortfall alert engine")}</p>
						</div>
						<div id="cf-verification-badge">
							<span class="lotus-badge lotus-badge-neutral">Waiting for data...</span>
						</div>
					</div>
				</div>

				<!-- Alert Containers (Account Imbalance / Shortfall / Forbidden) -->
				<div id="cf-alert-area"></div>

				<!-- Server-resolved account scope banner (Fix C) -->
				<div id="cf-scope-status" class="mb-4"></div>

				<!-- Main 3-Tier Dashboard Grid -->
				<div class="row">
					<!-- Left 8 Cols: Finance Viewport -->
					<div class="col-lg-8 col-md-12">
						<!-- Tier 1: Ledger Truth & Opening Cash -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>🏦</span>
										<span>${__("Tier 1: Opening Cash & Bank Balances")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("Independent verification between General Ledger (GL) and Trial Balance")}</p>
								</div>
								<span id="cf-reconciliation-status" class="lotus-badge lotus-badge-neutral">Verifying ledger...</span>
							</div>

							<div class="p-4 rounded-2xl mb-3" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid var(--lotus-border);">
								<div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${__("Consolidated Aggregate Cash Balance")}</div>
								<div id="cf-opening-amount" style="font-size: 32px; font-weight: 800; color: var(--lotus-text-primary); margin-top: 4px; letter-spacing: -0.5px;">-- VND</div>
							</div>

							<div class="text-muted mb-2" style="font-size: 12px; font-weight: 600;">${__("Breakdown by constituent cash/bank account:")}</div>
							<div id="cf-account-breakdown" class="d-flex flex-wrap gap-2"></div>
						</div>

						<!-- 30-Day Forecast Table / Trajectory -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>📈</span>
										<span>${__("30-Day Cash Trajectory (Daily EOD Balances)")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("End-of-day balances projected from verified settled accounting events")}</p>
								</div>
								<span id="cf-points-count" class="lotus-badge lotus-badge-primary">30 Daily Points</span>
							</div>

							<div class="lotus-table-container" style="max-height: 320px; overflow-y: auto;">
								<table class="lotus-table">
									<thead>
										<tr>
											<th style="width: 25%;">${__("Date")}</th>
											<th style="width: 35%;">${__("Projected Balance (EOD Cash)")}</th>
											<th style="width: 25%;">${__("Settlement Events")}</th>
											<th style="width: 15%; text-align: center;">${__("Status")}</th>
										</tr>
									</thead>
									<tbody id="cf-points-tbody">
										<tr><td colspan="4" class="text-center text-muted py-4">${__("No forecast data generated yet.")}</td></tr>
									</tbody>
								</table>
							</div>
						</div>

						<!-- Tier 2: Obligations (Contractual Due Dates) -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>📑</span>
										<span>${__("Tier 2: Contractual Obligations (AR / AP Due Dates)")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("Contractual due dates from Sales Invoices (AR) & Purchase Invoices (AP)")}</p>
								</div>
							</div>

							<div class="lotus-table-container" style="max-height: 260px; overflow-y: auto;">
								<table class="lotus-table">
									<thead>
										<tr>
											<th style="width: 12%; text-align: center;">${__("Type")}</th>
											<th style="width: 22%;">${__("Party (Hash)")}</th>
											<th style="width: 20%;">${__("Due Date")}</th>
											<th style="width: 26%;">${__("Remaining Amount")}</th>
											<th style="width: 20%;">${__("Source Voucher")}</th>
										</tr>
									</thead>
									<tbody id="cf-obligations-tbody">
										<tr><td colspan="5" class="text-center text-muted py-4">${__("No outstanding contractual obligations.")}</td></tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>

					<!-- Right 4 Cols: Decoupled Copilot & Explanations -->
					<div class="col-lg-4 col-md-12">
						<!-- Bounded AI Copilot Explanation Card -->
						<div class="lotus-card mb-4" style="border: 1px solid rgba(99, 102, 241, 0.25); box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);">
							<div class="lotus-card-header mb-2">
								<h3 class="lotus-card-title" style="color: var(--lotus-ai-magic);">
									<span>🤖</span>
									<span>${__("AI Financial Copilot")}</span>
								</h3>
								<span id="cf-explanation-badge" class="lotus-badge lotus-badge-ai">Bounded AI</span>
							</div>
							<div id="cf-copilot-content" style="font-size: 13px; line-height: 1.6; color: var(--lotus-text-secondary);">
								<p class="text-muted">${__("Click <b>Run Cash Forecast</b> to synthesize ledger evidence and generate management guidance.")}</p>
							</div>
						</div>

						<!-- Next Checks & Deep Links -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-2">
								<h3 class="lotus-card-title" style="font-size: 14px;">
									<span>🎯</span>
									<span>${__("Recommended Next Checks")}</span>
								</h3>
							</div>
							<ul id="cf-next-checks-list" class="list-unstyled mb-0 d-flex flex-column gap-2" style="font-size: 13px;">
								<li>
									<a href="/app/bank-reconciliation-tool" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>🏦 Bank Reconciliation Tool</span>
										<span>&rarr;</span>
									</a>
								</li>
								<li>
									<a href="/app/query-report/Accounts%20Receivable?status=Overdue" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>⚠️ Overdue AR Collection Report</span>
										<span>&rarr;</span>
									</a>
								</li>
								<li>
									<a href="/app/purchase-invoice" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>📦 Pending AP Payment Vouchers</span>
										<span>&rarr;</span>
									</a>
								</li>
							</ul>
						</div>

						<!-- Limitations & Disclosures -->
						<div class="lotus-card" style="background: var(--lotus-surface-app); border: 1px dashed var(--lotus-border);">
							<div class="text-muted" style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
								🛡️ ${__("Contract Scope Limitations")}
							</div>
							<div id="cf-limitations-list" style="font-size: 12px; color: var(--lotus-text-muted); line-height: 1.6;">
								<div>• Model strictly covers Trade AR/AP and Opening GL Cash Balances.</div>
								<div>• Does not speculate on unvouchered payroll, taxes, or unbooked accruals.</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);
		this.page.main.append(this.container);
	}

	load_default_company_and_fetch() {
		const comp = this.company_field.get_value();
		if (comp) {
			this.current_company = comp;
			this.fetch_forecast();
		}
	}

	refresh() {
		this.fetch_forecast();
	}

	on_company_change() {
		this.request_generation += 1;
		this.data = null;
		$("#cf-alert-area").empty();
		$("#cf-scope-status").empty();
		$("#cf-opening-amount").text("-- VND");
		$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
		$("#cf-account-breakdown").empty();
		$("#cf-verification-badge").empty();
		$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Loading forecast for selected company...</td></tr>');
		$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Loading contractual obligations...</td></tr>');
		$("#cf-copilot-content").html('<p class="text-muted">Connecting to AI Copilot...</p>');
		this.fetch_forecast();
	}

	fetch_forecast(want_explanation = true) {
		const me = this;
		const company = this.company_field.get_value();
		const as_of = this.as_of_field.get_value() || "2026-09-26";

		if (!company) {
			return;
		}

		const request_token = ++this.request_generation;

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_ai002_cash_account_scope",
			args: { company: company }
		}).then(function (r) {
			if (request_token !== me.request_generation) {
				return;
			}
			if (r.exc) {
				me.render_error("Unable to resolve verified cash account scope.");
				return;
			}
			const scope = r.message;
			if (!scope || scope.status !== "RESOLVED" || !Array.isArray(scope.scope) || scope.scope.length === 0) {
				me.render_scope_needs_review(scope || {});
				return;
			}
			me.render_scope_banner(scope);

			return frappe.call({
				method: "lotus_fin.api.ai_insights.get_ai002_cash_forecast",
				args: {
					company: company,
					financial_as_of: as_of,
					currency: "VND",
					include_explanation: want_explanation
				}
			}).then(function (r2) {
				if (request_token !== me.request_generation) {
					return;
				}
				if (r2.exc) {
					me.render_error("Server error during cash forecast calculation.");
					return;
				}
				const resp = r2.message;
				if (resp && resp.verified_company && resp.verified_company !== me.company_field.get_value()) {
					return;
				}
				me.data = resp;
				me.render_dashboard(resp);
			});
		}).catch(function () {
			if (request_token === me.request_generation) {
				me.render_error("Failed to fetch cash forecast data.");
			}
		});
	}

	render_scope_banner(scope) {
		const el = $("#cf-scope-status").empty();
		const count = (scope.count !== undefined && scope.count !== null)
			? scope.count
			: (scope.scope ? scope.scope.length : 0);
		const approval = scope.approval || "APPROVED";
		let html = `<div class="d-flex align-items-center gap-2">
			<span class="lotus-badge lotus-badge-success">Account Scope: ${count} verified accounts — ${approval}</span>`;
		if (scope.unapproved_excluded && scope.unapproved_excluded.length > 0) {
			html += `<span class="lotus-badge lotus-badge-warning">${scope.unapproved_excluded.length} unapproved accounts excluded</span>`;
		}
		html += `</div>`;
		el.html(html);
	}

	render_scope_needs_review(scope) {
		const approval = scope.approval || "MISSING_CONFIG";
		const reasons = {
			MISSING_CONFIG: "No approved cash/bank accounts configured for this company.",
			INVALID_CONFIG: "Cash account configuration is empty or invalid.",
			STALE_CONFIG: "Configured accounts do not exist or are disabled."
		};
		const reason = reasons[approval] || "Unable to confirm approved cash account scope.";
		$("#cf-scope-status").html(`
			<div class="lotus-banner lotus-banner-warning">
				<b>Account Scope Review Required (${approval}):</b><br/>
				${reason} Forecast engine remains locked until an accounting manager approves account scope in Company settings.
			</div>
		`);
		$("#cf-opening-amount").text("-- VND");
		$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
		$("#cf-account-breakdown").empty();
		$("#cf-verification-badge").html('<span class="lotus-badge lotus-badge-warning">Pending Scope Approval</span>');
		$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Forecast temporarily locked: Account Scope Review Required.</td></tr>');
		$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Forecast temporarily locked: Account Scope Review Required.</td></tr>');
		$("#cf-copilot-content").html('<p class="text-muted">Please configure approved cash accounts to activate forecast.</p>');
	}

	render_dashboard(resp) {
		const alertArea = $("#cf-alert-area").empty();

		if (resp.status === "FORBIDDEN" || (resp.reason_code && resp.reason_code === "UNAUTHORIZED_ACCESS")) {
			alertArea.html(`
				<div class="lotus-banner lotus-banner-danger mb-4">
					<h5 style="margin-top: 0; color: #b91c1c;">Access Denied (FORBIDDEN)</h5>
					<p class="mb-2">You do not have permission to view financial forecast data for this company.</p>
					<button class="lotus-btn lotus-btn-primary lotus-btn-sm" onclick="frappe.set_route('Form', 'Company')">Change Company</button>
				</div>
			`);
			$("#cf-opening-amount").text("-- VND");
			$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
			$("#cf-account-breakdown").empty();
			$("#cf-verification-badge").empty();
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Access Denied.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Access Denied.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Access Denied.</p>');
			return;
		}

		if (resp.status === "SOURCE_ERROR" || resp.status === "TIMEOUT") {
			alertArea.html(`
				<div class="lotus-banner lotus-banner-danger mb-4">
					<h5 style="margin-top: 0; color: #b91c1c;">Financial Data Source Error</h5>
					<p class="mb-1">A mandatory data source (AR / AP / Trial Balance) could not be retrieved. Forecast halted for fail-closed data integrity.</p>
					<p class="text-muted mb-0" style="font-size: 12px;">${(resp.limitations && resp.limitations[0]) || "Data source temporarily unavailable."}</p>
				</div>
			`);
			$("#cf-opening-amount").text("-- VND");
			$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
			$("#cf-account-breakdown").empty();
			$("#cf-verification-badge").html('<span class="lotus-badge lotus-badge-danger">Source Error</span>');
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Forecast halted due to source error.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Forecast halted due to source error.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Please resolve underlying data source error and retry.</p>');
			return;
		}

		if (resp.status === "INSUFFICIENT_DATA" || resp.status === "INCONSISTENT_DATA") {
			const isInconsistent = resp.status === "INCONSISTENT_DATA";
			alertArea.html(`
				<div class="lotus-banner ${isInconsistent ? 'lotus-banner-danger' : 'lotus-banner-warning'} mb-4">
					<h5 style="margin-top: 0; color: ${isInconsistent ? '#b91c1c' : '#c2410c'};">${isInconsistent ? "Inconsistent Ledger Data" : "Unverified Opening Cash Balance"}</h5>
					<p class="mb-1">${isInconsistent
						? "General Ledger (GL) does not equal Trial Balance for designated accounts. Forecast halted."
						: "Missing verifiable reconciliation baseline; cannot compute cash trajectory."}</p>
					<p class="text-muted mb-0" style="font-size: 12px;">${(resp.limitations && resp.limitations[0]) || ""}</p>
				</div>
			`);
			if (resp.opening_cash) {
				$("#cf-opening-amount").text(format_money(resp.opening_cash.aggregate_amount, resp.currency || "VND"));
				$("#cf-reconciliation-status").text(resp.opening_cash.reconciliation).attr("class", "lotus-badge lotus-badge-warning");
			}
			$("#cf-verification-badge").html(isInconsistent
				? '<span class="lotus-badge lotus-badge-danger">Ledger Mismatch</span>'
				: '<span class="lotus-badge lotus-badge-warning">Unreconciled</span>');
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Forecast halted: Opening balance is unverified.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Forecast halted: Opening balance is unverified.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Please reconcile ledger accounts and rerun forecast.</p>');
			return;
		}

		const recon = resp.opening_cash ? resp.opening_cash.reconciliation : null;
		const isLedgerVerified = recon === "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED"
			|| recon === "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED";
		$("#cf-verification-badge").html(isLedgerVerified
			? '<span class="lotus-badge lotus-badge-success">🛡️ Ledger Reconciled & Verified</span>'
			: '<span class="lotus-badge lotus-badge-warning">⚠️ Unreconciled Ledger</span>');

		// Check Shortfall Alerts
		if (resp.shortfall_events && resp.shortfall_events.length > 0) {
			const sf = resp.shortfall_events[0];
			const isInherited = sf.breach_kind === "INHERITED_FROM_OPENING";
			const title = isInherited ? "Inherited Opening Cash Deficit Alert" : "CRITICAL LIQUIDITY SHORTFALL ALERT";
			alertArea.append(`
				<div class="lotus-banner ${isInherited ? 'lotus-banner-warning' : 'lotus-banner-danger'} mb-4">
					<b>${title}:</b> Projected cash drops below zero on <b>${sf.first_date}</b>, reaching peak deficit of <b>${format_money(sf.minimum_modeled_cash, "VND")}</b> on <b>${sf.minimum_date}</b>.
				</div>
			`);
		}

		// Check Constituent Account Deficit
		if (resp.opening_cash && resp.opening_cash.has_constituent_deficit) {
			alertArea.append(`
				<div class="lotus-banner lotus-banner-warning mb-4">
					<b>Internal Account Imbalance Alert:</b> One or more constituent bank accounts have negative balances despite positive consolidated cash. Internal liquidity transfer recommended.
				</div>
			`);
		}

		// Render Opening Cash
		if (resp.opening_cash) {
			$("#cf-opening-amount").text(format_money(resp.opening_cash.aggregate_amount, resp.currency || "VND"));
			$("#cf-reconciliation-status")
				.text(resp.opening_cash.reconciliation)
				.attr("class", isLedgerVerified ? "lotus-badge lotus-badge-success" : "lotus-badge lotus-badge-warning");
			
			let accHtml = "";
			if (resp.opening_cash.accounts) {
				accHtml = resp.opening_cash.accounts.map(a => `
					<div class="lotus-evidence-item mb-0" style="padding: 6px 12px; border-radius: var(--lotus-radius-pill); font-size: 12px;">
						<span style="font-weight: 500;">${frappe.utils.escape_html(a.account)}:</span>
						<b style="color: ${a.deficit ? '#dc2626' : 'var(--lotus-text-primary)'}; margin-left: 4px;">
							${format_money(a.amount, a.currency || "VND")}
						</b>
					</div>
				`).join("");
			}
			$("#cf-account-breakdown").html(accHtml);
		}

		// Render Forecast Points
		const tbody = $("#cf-points-tbody").empty();
		if (!resp.forecast_points || resp.forecast_points.length === 0) {
			tbody.html(`
				<tr><td colspan="4" class="text-center text-muted py-4">
					<b>No confirmed future payment events found.</b><br/>
					Model halted under deterministic fail-closed safety policy.
				</td></tr>
			`);
		} else {
			resp.forecast_points.forEach(p => {
				const val = parseFloat(p.modeled_cash);
				const isNeg = val < 0;
				const eventsCount = p.included_event_ids ? p.included_event_ids.length : 0;
				tbody.append(`
					<tr style="${isNeg ? 'background-color: #fef2f2;' : ''}">
						<td><span class="font-weight-bold" style="color: var(--lotus-text-primary);">${p.date}</span></td>
						<td style="${isNeg ? 'color: #dc2626; font-weight: 700;' : 'color: var(--lotus-primary); font-weight: 600;'}">
							${format_money(p.modeled_cash, resp.currency || "VND")}
						</td>
						<td>${eventsCount > 0 ? `<span class="lotus-badge lotus-badge-primary">${eventsCount} events</span>` : '<span class="text-muted">—</span>'}</td>
						<td style="text-align: center;"><span class="lotus-badge lotus-badge-neutral">${p.status}</span></td>
					</tr>
				`);
			});
		}

		// Render Obligations
		const obTbody = $("#cf-obligations-tbody").empty();
		if (!resp.obligations || resp.obligations.length === 0) {
			obTbody.html('<tr><td colspan="5" class="text-center text-muted py-4">No outstanding contractual obligations.</td></tr>');
		} else {
			resp.obligations.forEach(o => {
				const isAR = o.type === "AR";
				obTbody.append(`
					<tr>
						<td style="text-align: center;"><span class="lotus-badge ${isAR ? 'lotus-badge-success' : 'lotus-badge-warning'}">${o.type}</span></td>
						<td><span class="lotus-code-badge">${o.party_hash || '-'}</span></td>
						<td style="color: var(--lotus-text-secondary);">${o.due_date || 'N/A'}</td>
						<td style="font-weight: 600; color: var(--lotus-text-primary);">${format_money(o.remaining_amount, o.currency || "VND")}</td>
						<td><span class="text-muted" style="font-size: 11px;">${frappe.utils.escape_html(o.source_ref)}</span></td>
					</tr>
				`);
			});
		}

		// Render Copilot Explanation
		const copilotDiv = $("#cf-copilot-content").empty();
		if (resp.explanation) {
			let factsHtml = "<div class='mb-2'><b>Verified Ledger Evidence Facts:</b></div><ul class='pl-3 mb-3' style='line-height: 1.6;'>";
			(resp.explanation.facts || []).forEach(f => {
				factsHtml += `<li>${frappe.utils.escape_html(f.statement)}</li>`;
			});
			factsHtml += "</ul>";

			let driversHtml = "";
			if (resp.explanation.drivers && resp.explanation.drivers.length > 0) {
				driversHtml = "<div class='mb-2'><b>AI Synthesis & Operational Insights:</b></div><div class='p-3 rounded-xl' style='background: var(--lotus-surface-subtle); border-left: 3px solid var(--lotus-ai-magic); line-height: 1.6;'>" +
					resp.explanation.drivers.map(d => frappe.utils.escape_html(d.statement)).join("<br/>") +
					"</div>";
			}

			copilotDiv.html(factsHtml + driversHtml);
		} else {
			copilotDiv.html(`
				<p class="text-muted">Deterministic forecast calculated. Click <b>Run Cash Forecast</b> to generate AI synthesis & analysis.</p>
			`);
		}
	}

	render_error(msg) {
		frappe.msgprint({
			title: __("Cash Forecast Notification"),
			indicator: "orange",
			message: msg
		});
	}
};
