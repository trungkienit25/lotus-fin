// Lotus Fin Cash Forecast Copilot Page Controller & UI
frappe.provide("lotus_fin.cash_forecast");

frappe.pages["cash-forecast"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Cash Forecast Copilot"),
		single_column: true
	});

	wrapper.cash_forecast = new lotus_fin.cash_forecast.Controller(wrapper);
};

frappe.pages["cash-forecast"].refresh = function (wrapper) {
	if (wrapper.cash_forecast) {
		wrapper.cash_forecast.refresh();
	}
};

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

		// 3. Primary Run Forecast Button
		this.page.set_primary_action(__("Compute Forecast"), function () {
			me.fetch_forecast(true);
		}, "octicon octicon-sync");
	}

	setup_dom() {
		this.page.main.empty();
		this.container = $(`
			<div class="cash-forecast-container" style="padding: 15px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
				<!-- Top Header / Scope Banner -->
				<div class="row mb-3">
					<div class="col-md-12 d-flex justify-content-between align-items-center">
						<div>
							<span class="badge badge-primary" style="font-size: 13px; padding: 6px 12px; background-color: #2b6cb0;">Scope: TRADE_ONLY</span>
							<span class="text-muted ml-2" style="font-size: 13px;">Timezone: Asia/Ho_Chi_Minh | Horizon: 30 Calendar Days</span>
						</div>
						<div id="cf-verification-badge">
							<span class="badge badge-success" style="background-color: #2f855a; color: white; padding: 6px 12px;">Ledger Truth Verified</span>
						</div>
					</div>
				</div>

				<!-- Alert Containers (Account Imbalance / Shortfall / Forbidden) -->
				<div id="cf-alert-area"></div>

				<!-- Main 3-Tier Dashboard Grid -->
				<div class="row">
					<!-- Left 8 Cols: Finance Viewport -->
					<div class="col-md-8">
						<!-- Tier 1: Ledger Truth & Opening Cash -->
						<div class="card p-3 mb-3" style="border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
							<h5 class="text-muted text-uppercase" style="font-size: 12px; letter-spacing: 0.5px; margin-bottom: 8px;">Tier 1: Opening Cash Balance</h5>
							<div class="d-flex align-items-baseline">
								<h2 id="cf-opening-amount" style="font-weight: 700; color: #1a202c; margin-right: 15px;">-- VND</h2>
								<span id="cf-reconciliation-status" class="badge badge-secondary" style="font-size: 11px;">Reconciled</span>
							</div>
							<div id="cf-account-breakdown" class="mt-2" style="font-size: 13px; color: #4a5568;"></div>
						</div>

						<!-- 30-Day Forecast Table / Trajectory -->
						<div class="card p-3 mb-3" style="border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
							<div class="d-flex justify-content-between align-items-center mb-2">
								<h5 class="text-muted text-uppercase" style="font-size: 12px; letter-spacing: 0.5px; margin: 0;">30-Day Daily EOD Cash Trajectory</h5>
								<span id="cf-points-count" class="badge badge-light">30 Daily Points</span>
							</div>
							<div id="cf-points-container" style="max-height: 280px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 6px;">
								<table class="table table-sm table-hover mb-0" style="font-size: 12px;">
									<thead class="thead-light">
										<tr>
											<th>Date</th>
											<th>Modeled Cash (EOD)</th>
											<th>Settlement Events</th>
											<th>Status</th>
										</tr>
									</thead>
									<tbody id="cf-points-tbody">
										<tr><td colspan="4" class="text-center text-muted py-3">No forecast points generated.</td></tr>
									</tbody>
								</table>
							</div>
						</div>

						<!-- Tier 2: Obligations (Contractual Due Dates) -->
						<div class="card p-3 mb-3" style="border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
							<h5 class="text-muted text-uppercase" style="font-size: 12px; letter-spacing: 0.5px; margin-bottom: 8px;">Tier 2: Trade Obligations (AR / AP Due Dates)</h5>
							<p class="text-muted" style="font-size: 12px;">Contractual due dates displayed below chart; never combined onto cash line without confirmed settlement.</p>
							<div id="cf-obligations-container" style="max-height: 220px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 6px;">
								<table class="table table-sm table-hover mb-0" style="font-size: 12px;">
									<thead class="thead-light">
										<tr>
											<th>Type</th>
											<th>Party Hash</th>
											<th>Due Date</th>
											<th>Remaining Amount</th>
											<th>Voucher Ref</th>
										</tr>
									</thead>
									<tbody id="cf-obligations-tbody">
										<tr><td colspan="5" class="text-center text-muted py-3">No trade obligations found.</td></tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>

					<!-- Right 4 Cols: Decoupled Copilot & Explanations -->
					<div class="col-md-4">
						<!-- Bounded AI Copilot Explanation Card -->
						<div class="card p-3 mb-3" style="border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-top: 3px solid #3182ce;">
							<div class="d-flex justify-content-between align-items-center mb-2">
								<h5 style="font-size: 14px; font-weight: 600; margin: 0;">AI Financial Copilot</h5>
								<span id="cf-explanation-badge" class="badge badge-info" style="font-size: 11px;">Bounded</span>
							</div>
							<div id="cf-copilot-content" style="font-size: 13px; line-height: 1.5; color: #2d3748;">
								<p class="text-muted">Click <b>Compute Forecast</b> to generate verified audit findings and grounded guidance.</p>
							</div>
						</div>

						<!-- Next Checks & Deep Links -->
						<div class="card p-3 mb-3" style="border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
							<h5 class="text-muted text-uppercase" style="font-size: 12px; letter-spacing: 0.5px; margin-bottom: 8px;">Deterministic Next Checks</h5>
							<ul id="cf-next-checks-list" class="list-unstyled mb-0" style="font-size: 12px;">
								<li class="py-1"><a href="/app/bank-reconciliation-tool" class="text-primary">Reconcile unposted bank transactions &rarr;</a></li>
								<li class="py-1"><a href="/app/query-report/Accounts%20Receivable?status=Overdue" class="text-primary">Follow up on overdue receivables &rarr;</a></li>
								<li class="py-1"><a href="/app/purchase-invoice" class="text-primary">Confirm vendor payment schedule dates &rarr;</a></li>
							</ul>
						</div>

						<!-- Limitations & Disclosures -->
						<div class="card p-3" style="border-radius: 8px; background-color: #f7fafc; border: 1px solid #e2e8f0;">
							<h6 class="text-muted text-uppercase" style="font-size: 11px; letter-spacing: 0.5px;">Contract Limitations</h6>
							<div id="cf-limitations-list" style="font-size: 11px; color: #718096;">
								<div>• Scope is limited to Trade AR/AP and Opening GL.</div>
								<div>• Excludes unmodeled tax, payroll, and debt service.</div>
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
		// Increment request generation to invalidate any in-flight requests
		this.request_generation += 1;
		// Clear prior-company data and DOM immediately
		this.data = null;
		$("#cf-alert-area").empty();
		$("#cf-opening-amount").text("-- VND");
		$("#cf-reconciliation-status").text("");
		$("#cf-account-breakdown").empty();
		$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-3">Loading forecast for selected company...</td></tr>');
		$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-3">Loading obligations...</td></tr>');
		$("#cf-copilot-content").html('<p class="text-muted">Loading financial copilot...</p>');
		this.fetch_forecast();
	}

	fetch_forecast(want_explanation = false) {
		const me = this;
		const company = this.company_field.get_value();
		const as_of = this.as_of_field.get_value() || "2026-09-26";

		if (!company) {
			return;
		}

		const request_token = ++this.request_generation;

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_ai002_cash_forecast",
			args: {
				company: company,
				financial_as_of: as_of,
				currency: "VND",
				include_explanation: want_explanation,
			},
			callback: function (r) {
				// Race condition & company switch check: Discard stale responses
				if (request_token !== me.request_generation) {
					return;
				}
				if (r.exc) {
					me.render_error("Server error executing cash forecast.");
					return;
				}
				const resp = r.message;
				if (resp && resp.verified_company && resp.verified_company !== me.company_field.get_value()) {
					return;
				}
				me.data = resp;
				me.render_dashboard(resp);
			}
		});
	}

	render_dashboard(resp) {
		const me = this;
		const alertArea = $("#cf-alert-area").empty();

		// Check FORBIDDEN (CG-SEC-01 / CG-SEC-04: generic denial, no company existence leakage)
		if (resp.status === "FORBIDDEN" || (resp.reason_code && resp.reason_code === "UNAUTHORIZED_ACCESS")) {
			alertArea.html(`
				<div class="alert alert-danger p-3" style="border-radius: 6px;">
					<h5 style="margin-top:0;">Access Denied (FORBIDDEN)</h5>
					<p>You do not have permission to access cash forecast data for the requested resource.</p>
					<button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form', 'Company')">Switch Company</button>
				</div>
			`);
			$("#cf-opening-amount").text("-- VND");
			$("#cf-reconciliation-status").text("");
			$("#cf-account-breakdown").empty();
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-3">Access forbidden.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-3">Access forbidden.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Access forbidden.</p>');
			return;
		}

		// Check Shortfall Alerts
		if (resp.shortfall_events && resp.shortfall_events.length > 0) {
			const sf = resp.shortfall_events[0];
			const isInherited = sf.breach_kind === "INHERITED_FROM_OPENING";
			const alertClass = isInherited ? "alert-warning" : "alert-danger";
			const title = isInherited ? "Technical Shortfall (Inherited from Opening)" : "Modeled Cash Shortfall (NEW_MODELED_DEFICIT)";
			alertArea.append(`
				<div class="alert ${alertClass} p-3 mb-3" style="border-radius: 6px;">
					<strong>${title}:</strong> Modeled cash drops below 0 on <b>${sf.first_date}</b>, reaching minimum of <b>${format_currency(sf.minimum_modeled_cash)} VND</b> on <b>${sf.minimum_date}</b>.
				</div>
			`);
		}

		// Check Constituent Account Deficit
		if (resp.opening_cash && resp.opening_cash.has_constituent_deficit) {
			alertArea.append(`
				<div class="alert alert-warning p-3 mb-3" style="border-radius: 6px;">
					<strong>Account Imbalance Alert:</strong> One or more constituent bank accounts have negative balances, despite positive net aggregate cash.
				</div>
			`);
		}

		// Render Opening Cash
		if (resp.opening_cash) {
			$("#cf-opening-amount").text(`${format_currency(resp.opening_cash.aggregate_amount)} ${resp.currency}`);
			$("#cf-reconciliation-status").text(resp.opening_cash.reconciliation);
			let accHtml = "";
			if (resp.opening_cash.accounts) {
				accHtml = resp.opening_cash.accounts.map(a => `
					<span class="mr-3 ${a.deficit ? 'text-danger font-weight-bold' : ''}">
						${a.account}: ${format_currency(a.amount)} ${a.currency}
					</span>
				`).join("");
			}
			$("#cf-account-breakdown").html(accHtml);
		}

		// Render Forecast Points
		const tbody = $("#cf-points-tbody").empty();
		if (!resp.forecast_points || resp.forecast_points.length === 0) {
			tbody.html(`
				<tr><td colspan="4" class="text-center text-muted py-4">
					<b>No confirmed future settlement events found.</b><br/>
					Forecast unavailable in accordance with strict deterministic policy.
				</td></tr>
			`);
		} else {
			resp.forecast_points.forEach(p => {
				const val = parseFloat(p.modeled_cash);
				const isNeg = val < 0;
				const eventsCount = p.included_event_ids ? p.included_event_ids.length : 0;
				tbody.append(`
					<tr style="${isNeg ? 'background-color: #fff5f5;' : ''}">
						<td><b>${p.date}</b></td>
						<td style="${isNeg ? 'color: #e53e3e; font-weight: bold;' : 'color: #2b6cb0;'}">
							${format_currency(p.modeled_cash)} ${resp.currency}
						</td>
						<td>${eventsCount > 0 ? `<span class="badge badge-info">${eventsCount} event(s)</span>` : '-'}</td>
						<td><span class="badge badge-light">${p.status}</span></td>
					</tr>
				`);
			});
		}

		// Render Obligations
		const obTbody = $("#cf-obligations-tbody").empty();
		if (!resp.obligations || resp.obligations.length === 0) {
			obTbody.html('<tr><td colspan="5" class="text-center text-muted py-3">No outstanding trade obligations.</td></tr>');
		} else {
			resp.obligations.forEach(o => {
				obTbody.append(`
					<tr>
						<td><span class="badge ${o.type === 'AR' ? 'badge-success' : 'badge-warning'}">${o.type}</span></td>
						<td><code>${o.party_hash || '-'}</code></td>
						<td>${o.due_date || 'N/A'}</td>
						<td>${format_currency(o.remaining_amount)} ${o.currency}</td>
						<td>${o.source_ref}</td>
					</tr>
				`);
			});
		}

		// Render Copilot Explanation
		const copilotDiv = $("#cf-copilot-content").empty();
		if (resp.explanation) {
			let factsHtml = "<b>Verified Ledger Facts:</b><ul class='pl-3 mb-2'>";
			resp.explanation.facts.forEach(f => {
				factsHtml += `<li>${frappe.utils.escape_html(f.statement)}</li>`;
			});
			factsHtml += "</ul>";

			let driversHtml = "";
			if (resp.explanation.drivers && resp.explanation.drivers.length > 0) {
				driversHtml = "<b>AI Interpretation:</b><div class='p-2 mb-2 bg-light rounded'>" +
					resp.explanation.drivers.map(d => frappe.utils.escape_html(d.statement)).join("<br/>") +
					"</div>";
			}

			copilotDiv.html(factsHtml + driversHtml);
		} else {
			copilotDiv.html(`
				<p class="text-muted">Deterministic forecast calculated. Click <b>Compute Forecast</b> to query the bounded AI Copilot.</p>
			`);
		}
	}

	render_error(msg) {
		frappe.msgprint({
			title: __("Forecast Notice"),
			indicator: "orange",
			message: msg
		});
	}
};
