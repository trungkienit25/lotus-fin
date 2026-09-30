// Lotus Fin Financial Health Page Controller & UI
frappe.provide("lotus_fin.financial_health");

frappe.pages["financial-health"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Financial Health"),
		single_column: true
	});

	wrapper.financial_health = new lotus_fin.financial_health.Controller(wrapper);
};

frappe.pages["financial-health"].refresh = function (wrapper) {
	if (wrapper.financial_health) {
		wrapper.financial_health.refresh();
	}
};

lotus_fin.financial_health.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.period_start = null;
		this.period_end = null;
		this.data = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.setup_events();
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
				if (val && val !== me.current_company) {
					me.current_company = val;
					me.fetch_financial_health();
				}
			}
		});

		const curYear = frappe.datetime.get_today().slice(0, 4);
		this.period_field = this.page.add_field({
			fieldname: "fiscal_year_preset",
			label: __("Period"),
			fieldtype: "Select",
			options: [
				{ label: "Current Year (" + curYear + ")", value: "CURRENT_YEAR" },
				{ label: "FY2020 (2020-01-01 to 2020-12-31)", value: "FY2020" },
				{ label: "FY2025 (2025-01-01 to 2025-12-31)", value: "FY2025" }
			],
			default: "CURRENT_YEAR",
			change() {
				me.apply_period_preset(me.period_field.get_value());
				me.fetch_financial_health();
			}
		});

		// 3. Comparison Mode
		this.comparison_field = this.page.add_field({
			fieldname: "comparison_mode",
			label: __("Comparison"),
			fieldtype: "Select",
			options: [
				{ label: "Previous Period", value: "PREVIOUS_PERIOD" },
				{ label: "None", value: "NONE" }
			],
			default: "PREVIOUS_PERIOD",
			change() {
				me.fetch_financial_health();
			}
		});

		// 4. Primary Refresh / Run AI Analysis Button
		this.page.set_primary_action(__("Analyze Financial Health"), function () {
			me.fetch_financial_health(true);
		}, "octicon octicon-sync");

		this.apply_period_preset("CURRENT_YEAR");
		if (this.period_field) {
			this.period_field.set_value("CURRENT_YEAR");
		}
	}

	apply_period_preset(preset) {
		if (preset === "FY2020") {
			this.period_start = "2020-01-01";
			this.period_end = "2020-12-31";
		} else if (preset === "FY2025") {
			this.period_start = "2025-01-01";
			this.period_end = "2025-12-31";
		} else {
			const curYear = frappe.datetime.get_today().slice(0, 4);
			this.period_start = `${curYear}-01-01`;
			this.period_end = `${curYear}-12-31`;
		}
	}

	setup_dom() {
		this.main = $(`<div class="lotus-financial-health-container">
			<div class="lotus-fh-header-card">
				<div class="d-flex justify-content-between align-items-start">
					<div>
						<span class="lotus-brand-badge">Lotus Fin &bull; AI-F001</span>
						<h1 class="lotus-fh-title">${__("Financial Health Analyst")}</h1>
						<p class="lotus-fh-subtitle">${__("SME Financial Intelligence & Continuous Health Inspection")}</p>
					</div>
					<div class="text-right" id="lotus-meta-bar">
						<span class="lotus-meta-tag status-ok">${__("Data Mode: Actual")}</span>
						<span class="lotus-meta-tag status-warn ml-2" id="lotus-retrieval-time">${__("Waiting for analysis...")}</span>
					</div>
				</div>
			</div>

			<!-- Limitation / Error Banner Container -->
			<div id="lotus-banner-container"></div>

			<!-- Section 1: KPI Cards -->
			<div class="lotus-section-card">
				<div class="lotus-section-title">
					<span>${__("Key Financial Metrics")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;">${__("Formula v2026.1 &bull; Deterministic Accounting Verification")}</span>
				</div>
				<div class="lotus-kpi-grid" id="lotus-kpi-cards">
					<!-- KPI Cards rendered here -->
				</div>
			</div>

			<!-- Section 2: Period Comparison -->
			<div class="lotus-section-card" id="lotus-comparison-section">
				<div class="lotus-section-title">
					<span>${__("Period Comparison")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;" id="lotus-comparison-subtitle">${__("Equal-length historical span")}</span>
				</div>
				<div id="lotus-comparison-content">
					<!-- Comparison Table rendered here -->
				</div>
			</div>

			<!-- Section 3: AI Financial Analysis -->
			<div class="lotus-section-card" id="lotus-ai-section">
				<div class="lotus-section-title">
					<span>🤖 ${__("AI Financial Analysis & Narrative")}</span>
					<span class="lotus-ai-badge" id="lotus-ai-status-badge">${__("Grounded Explanation")}</span>
				</div>
				<div id="lotus-ai-content">
					<!-- AI Decomposition: Facts, Interpretations, Limitations, Next Checks -->
				</div>
			</div>

			<!-- Section 4: Recommended Next Checks / Actionability -->
			<div class="lotus-section-card" id="lotus-action-section">
				<div class="lotus-section-title">
					<span>🔍 ${__("Recommended Next Review Actions")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;">${__("Bounded Drill-down & Ledger Inspection (Read-Only)")}</span>
				</div>
				<div id="lotus-action-content">
					<!-- Action buttons rendered here -->
				</div>
			</div>

			<!-- Section 5: Evidence & Data Quality -->
			<div class="lotus-section-card" id="lotus-evidence-section">
				<div class="lotus-section-title">
					<span>📋 ${__("Evidence & Audit Provenance")}</span>
					<button class="btn btn-xs btn-default" id="lotus-toggle-evidence-btn">${__("Toggle Details")}</button>
				</div>
				<div id="lotus-evidence-content" style="display: block;">
					<!-- Evidence list rendered here -->
				</div>
			</div>
		</div>`).appendTo(this.page.main);
	}

	setup_events() {
		const me = this;
		this.main.on("click", "#lotus-toggle-evidence-btn", function () {
			const container = me.main.find("#lotus-evidence-content");
			container.slideToggle(150);
		});

		this.main.on("click", "[data-open-report]", function (e) {
			e.preventDefault();
			const reportName = $(this).attr("data-open-report");
			me.open_approved_report(reportName);
		});
	}

	load_default_company_and_fetch() {
		const me = this;
		if (this.company_field && this.company_field.get_value()) {
			this.current_company = this.company_field.get_value();
			this.fetch_financial_health();
		} else {
			// Query authorized companies for user
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Company",
					fields: ["name"],
					limit: 1
				},
				callback(r) {
					if (r.message && r.message.length > 0) {
						const comp = r.message[0].name;
						me.company_field.set_value(comp);
						me.current_company = comp;
						me.fetch_financial_health();
					} else {
						me.render_error("FORBIDDEN", __("No authorized companies found for current user."));
					}
				}
			});
		}
	}

	refresh() {
		// Called on desk route activate
		if (this.current_company) {
			this.fetch_financial_health();
		}
	}

	show_loading() {
		const kpiContainer = this.main.find("#lotus-kpi-cards");
		kpiContainer.html(`
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
			<div class="lotus-kpi-card lotus-skeleton" style="height: 90px;"></div>
		`);

		this.main.find("#lotus-banner-container").empty();
		this.main.find("#lotus-retrieval-time").text(__("Fetching financial snapshot..."));
	}

	fetch_financial_health(force_include_explanation = true) {
		const me = this;
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		if (!company) {
			this.render_error("VALIDATION_ERROR", __("Please select a company."));
			return;
		}

		if (this.period_field && this.period_field.get_value()) {
			this.apply_period_preset(this.period_field.get_value());
		}

		this.show_loading();
		const compMode = this.comparison_field ? this.comparison_field.get_value() : "PREVIOUS_PERIOD";

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_financial_snapshot",
			args: {
				company: company,
				period_start: this.period_start,
				period_end: this.period_end,
				currency: "VND",
				comparison: compMode === "NONE" ? null : "PREVIOUS_PERIOD",
				include_explanation: force_include_explanation ? 1 : 0
			},
			freeze: false,
			callback(r) {
				if (r.exc) {
					me.render_error("SOURCE_ERROR", __("An error occurred while gathering financial snapshot."));
					return;
				}
				if (r.message) {
					me.data = r.message;
					me.render();
				}
			},
			error(err) {
				const errMsg = (err && err.message) ? err.message : __("Failed to contact Lotus Fin engine.");
				me.render_error("FORBIDDEN", errMsg);
			}
		});
	}

	render() {
		if (!this.data) return;

		// 1. Check top-level status
		const status = this.data.status;
		this.render_meta_bar();

		if (status === "FORBIDDEN") {
			this.render_error("FORBIDDEN", __("Access denied. You do not have permission to view financial records for this company."));
			return;
		}

		// Handle empty company activity
		const metrics = this.data.metrics || [];
		const isAllZeroOrUnavailable = metrics.every(m => m.status === "UNAVAILABLE" || (m.status === "AVAILABLE" && (m.value === 0 || m.value === 0.0)));
		
		this.render_banners();
		this.render_kpis();
		this.render_comparison();
		this.render_ai_analysis();
		this.render_actions();
		this.render_evidence();
	}

	render_meta_bar() {
		const metaBar = this.main.find("#lotus-meta-bar");
		const status = this.data.status || "UNKNOWN";
		const timeStr = this.data.as_of ? frappe.datetime.comment_when(this.data.as_of) : __("Just now");
		
		let statusClass = "status-ok";
		if (status === "PARTIAL" || status === "INSUFFICIENT_DATA") statusClass = "status-warn";
		if (status === "SOURCE_ERROR" || status === "FORBIDDEN") statusClass = "status-error";

		metaBar.html(`
			<span class="lotus-meta-tag ${statusClass}">${__("Status: ")}${frappe.utils.escape_html(status)}</span>
			<span class="lotus-meta-tag status-ok ml-1">${__("Actual Data &bull; ")}${frappe.utils.escape_html(this.data.currency || "VND")}</span>
			<span class="lotus-meta-tag ml-1 text-muted">${__("Updated: ")}${timeStr}</span>
		`);
	}

	render_banners() {
		const container = this.main.find("#lotus-banner-container").empty();
		const limitations = this.data.limitations || [];

		if (this.data.status === "INSUFFICIENT_DATA") {
			$(`<div class="lotus-banner lotus-banner-warning">
				<div>
					<b>${__("No Financial Activity:")}</b> ${__("No recorded transactions or financial statements exist for the selected period. Displaying verified state.")}
				</div>
			</div>`).appendTo(container);
		} else if (this.data.status === "PARTIAL") {
			$(`<div class="lotus-banner lotus-banner-warning">
				<div>
					<b>${__("Notice on Data Availability:")}</b> ${__("Certain report sources returned partial or unconfigured values. Metrics with verified ledger data remain authoritative.")}
				</div>
			</div>`).appendTo(container);
		}

		// Display explicit limitations
		if (limitations.length > 0) {
			const limItems = limitations.map(l => `<li>${frappe.utils.escape_html(l)}</li>`).join("");
			$(`<div class="lotus-banner lotus-banner-info">
				<div>
					<b>${__("Active System Boundaries & Limitations:")}</b>
					<ul class="mb-0 mt-1 pl-3">${limItems}</ul>
				</div>
			</div>`).appendTo(container);
		}
	}

	render_kpis() {
		const container = this.main.find("#lotus-kpi-cards").empty();
		const metrics = this.data.metrics || [];
		const metricMap = {};
		metrics.forEach(m => { metricMap[m.metric_id] = m; });

		// Standard AI001 Approved 6 core metrics
		const approvedMetrics = [
			{ id: "revenue", label: __("Revenue"), is_currency: true },
			{ id: "cogs", label: __("COGS"), is_currency: true },
			{ id: "gross_margin", label: __("Gross Margin"), is_ratio: true },
			{ id: "cash_balance", label: __("Cash Balance"), is_currency: true },
			{ id: "ar_outstanding", label: __("AR Outstanding"), is_currency: true },
			{ id: "overdue_ar_ratio", label: __("Overdue AR Ratio"), is_ratio: true },
			{ id: "ap_outstanding", label: __("AP Outstanding"), is_currency: true },
			{ id: "near_term_ap", label: __("Near-Term AP"), is_currency: true }
		];

		approvedMetrics.forEach(meta => {
			const m = metricMap[meta.id];
			let valHtml = `<span class="text-muted font-weight-normal">${__("Unavailable")}</span>`;
			let stateBadge = `<span class="lotus-kpi-state-badge lotus-kpi-state-unavailable">${__("Unavailable")}</span>`;
			let subtext = "";
			let isCashNegative = false;

			if (m && m.status === "AVAILABLE" && m.value !== null) {
				stateBadge = `<span class="lotus-kpi-state-badge lotus-kpi-state-available">${__("Verified")}</span>`;
				if (meta.is_ratio) {
					// Ratio display: 0.3009 -> 30.09%
					const pct = (m.value * 100).toFixed(2);
					valHtml = `${pct}<span class="lotus-kpi-unit">%</span>`;
				} else {
					// Currency formatting: VND
					const formatted = frappe.format(m.value, { fieldtype: "Currency", currency: m.currency_or_unit || "VND" });
					if (meta.id === "cash_balance" && m.value < 0) {
						isCashNegative = true;
					}
					valHtml = `${formatted}`;
				}
			} else if (meta.id === "near_term_ap") {
				subtext = `<span class="text-muted" style="font-size: 10px;">${__("Horizon not frozen")}</span>`;
			}

			if (m && m.limitations && m.limitations.length > 0 && !subtext) {
				subtext = `<span class="text-muted" style="font-size: 10px;">${frappe.utils.escape_html(m.limitations[0])}</span>`;
			}

			const card = $(`<div class="lotus-kpi-card" data-metric-id="${meta.id}">
				<div class="d-flex justify-content-between align-items-center mb-1">
					<div class="lotus-kpi-label">${meta.label}</div>
					${stateBadge}
				</div>
				<div class="lotus-kpi-value ${isCashNegative ? 'cash-negative' : ''}">
					${valHtml}
				</div>
				<div class="lotus-kpi-subtext">${subtext}</div>
			</div>`);

			container.append(card);
		});
	}

	render_comparison() {
		const compSection = this.main.find("#lotus-comparison-section");
		const container = this.main.find("#lotus-comparison-content").empty();
		const comp = this.data.comparison;

		if (!comp || comp.status === "UNAVAILABLE") {
			const reason = (comp && comp.limitations && comp.limitations[0]) 
				? comp.limitations[0] 
				: __("Previous-period data unavailable");
			container.html(`
				<div class="text-muted p-3 bg-light rounded text-center">
					<i class="octicon octicon-info mr-1"></i> ${frappe.utils.escape_html(reason)}
				</div>
			`);
			return;
		}

		const pPeriod = comp.previous_period || {};
		this.main.find("#lotus-comparison-subtitle").text(
			__("Compared against previous period: ") + `${pPeriod.start || ""} to ${pPeriod.end || ""}`
		);

		const compMetrics = comp.metrics || {};
		const rows = [
			{ id: "revenue", label: __("Revenue"), is_currency: true },
			{ id: "cogs", label: __("COGS"), is_currency: true },
			{ id: "gross_margin", label: __("Gross Margin"), is_ratio: true },
			{ id: "cash_balance", label: __("Cash Balance"), is_currency: true },
			{ id: "ar_outstanding", label: __("AR Outstanding"), is_currency: true },
			{ id: "overdue_ar_ratio", label: __("Overdue AR Ratio"), is_ratio: true },
			{ id: "ap_outstanding", label: __("AP Outstanding"), is_currency: true }
		];

		let tableRowsHtml = "";
		rows.forEach(r => {
			const item = compMetrics[r.id];
			if (!item) return;

			let curStr = item.current !== null ? this.format_metric_val(item.current, r) : __("N/A");
			let prevStr = item.previous !== null ? this.format_metric_val(item.previous, r) : __("Unavailable");
			let absChangeStr = __("N/A");
			let relChangeStr = __("N/A");

			if (item.status === "AVAILABLE") {
				if (item.absolute_change !== null) {
					absChangeStr = this.format_metric_val(item.absolute_change, r);
				}
				if (item.relative_change !== null) {
					const pct = (item.relative_change * 100).toFixed(2);
					relChangeStr = `${item.relative_change > 0 ? '+' : ''}${pct}%`;
				}
			}

			tableRowsHtml += `<tr>
				<td class="font-weight-bold">${r.label}</td>
				<td>${curStr}</td>
				<td>${prevStr}</td>
				<td>${absChangeStr}</td>
				<td>${relChangeStr}</td>
				<td><span class="badge ${item.status === 'AVAILABLE' ? 'badge-success' : 'badge-light'}">${item.status}</span></td>
			</tr>`;
		});

		container.html(`
			<table class="lotus-table">
				<thead>
					<tr>
						<th>${__("Metric")}</th>
						<th>${__("Current Period")}</th>
						<th>${__("Previous Period")}</th>
						<th>${__("Absolute Change")}</th>
						<th>${__("Relative Change")}</th>
						<th>${__("Availability")}</th>
					</tr>
				</thead>
				<tbody>
					${tableRowsHtml}
				</tbody>
			</table>
		`);
	}

	format_metric_val(val, meta) {
		if (val === null || val === undefined) return __("N/A");
		if (meta.is_ratio) {
			return `${(val * 100).toFixed(2)}%`;
		}
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}

	render_ai_analysis() {
		const container = this.main.find("#lotus-ai-content").empty();
		const badge = this.main.find("#lotus-ai-status-badge");
		const exp = this.data.explanation;

		if (!exp || exp.status === "UNAVAILABLE" || exp.status !== "AVAILABLE") {
			badge.removeClass("lotus-ai-badge").addClass("badge badge-secondary").text(__("Degraded / Unavailable"));
			container.html(`
				<div class="lotus-banner lotus-banner-warning">
					<div>
						<b>${__("AI Explanation Unavailable:")}</b> ${__("AI narrative generation is currently unavailable. Deterministic financial metrics, period comparison, and evidence refs remain authoritative and fully preserved.")}
					</div>
				</div>
			`);
			return;
		}

		badge.removeClass("badge-secondary").addClass("lotus-ai-badge").text(__("Grounded Analysis"));

		// 1. Facts
		const factsHtml = (exp.facts || []).map(f => `<li>${frappe.utils.escape_html(f)}</li>`).join("");
		
		// 2. Interpretations
		const interpHtml = (exp.interpretations || []).map(i => `<li>${frappe.utils.escape_html(i)}</li>`).join("");

		// 3. Limitations
		const limHtml = (exp.limitations || []).map(l => `<li>${frappe.utils.escape_html(l)}</li>`).join("");

		container.html(`
			<div class="row">
				<div class="col-md-6">
					<div class="lotus-ai-box facts">
						<div class="lotus-ai-box-title">📊 ${__("What Happened (Verified Facts)")}</div>
						<ul class="lotus-ai-list">${factsHtml || `<li>${__("No factual statements generated.")}</li>`}</ul>
					</div>
				</div>
				<div class="col-md-6">
					<div class="lotus-ai-box interpretations">
						<div class="lotus-ai-box-title">💡 ${__("Financial Interpretation")}</div>
						<ul class="lotus-ai-list">${interpHtml || `<li>${__("No interpretations available.")}</li>`}</ul>
					</div>
				</div>
			</div>
			${limHtml ? `
			<div class="lotus-ai-box limitations">
				<div class="lotus-ai-box-title">⚠️ ${__("Analysis Boundaries & Limitations")}</div>
				<ul class="lotus-ai-list">${limHtml}</ul>
			</div>` : ''}
		`);
	}

	render_actions() {
		const container = this.main.find("#lotus-action-content").empty();
		const exp = this.data.explanation || {};
		const nextChecks = exp.next_checks || [
			__("Review overdue receivables in Accounts Receivable"),
			__("Inspect detailed revenue and expense lines in Profit and Loss Statement"),
			__("Review General Ledger cash entries and bank reconciliations"),
			__("Inspect upcoming payment obligations in Accounts Payable")
		];

		const checkItemsHtml = nextChecks.map(c => `<li>${frappe.utils.escape_html(c)}</li>`).join("");

		container.html(`
			<ul class="lotus-ai-list mb-3">
				${checkItemsHtml}
			</ul>
			<div class="lotus-action-btn-group">
				<button class="lotus-action-btn" data-open-report="Accounts Receivable">
					📑 ${__("Open Accounts Receivable")}
				</button>
				<button class="lotus-action-btn" data-open-report="Profit and Loss Statement">
					📊 ${__("Open Profit and Loss")}
				</button>
				<button class="lotus-action-btn" data-open-report="General Ledger">
					🏦 ${__("Inspect Cash in General Ledger")}
				</button>
				<button class="lotus-action-btn" data-open-report="Accounts Payable">
					💳 ${__("Open Accounts Payable")}
				</button>
				<button class="lotus-action-btn" data-open-report="Trial Balance">
					⚖️ ${__("Open Trial Balance")}
				</button>
			</div>
		`);
	}

	render_evidence() {
		const container = this.main.find("#lotus-evidence-content").empty();
		const evidenceRefs = this.data.evidence_refs || [];

		if (evidenceRefs.length === 0) {
			container.html(`<div class="text-muted p-2">${__("No source reports retrieved for current snapshot.")}</div>`);
			return;
		}

		let itemsHtml = "";
		evidenceRefs.forEach(ev => {
			const checksum = ev.checksum_or_version || __("N/A");
			const filterSnippet = frappe.utils.escape_html(JSON.stringify(ev.filters || {}));
			itemsHtml += `
				<div class="lotus-evidence-item">
					<div class="d-flex justify-content-between align-items-center mb-1">
						<b>${frappe.utils.escape_html(ev.source_name)}</b>
						<span class="lotus-code-badge">${checksum}</span>
					</div>
					<div class="text-muted" style="font-size: 11px;">
						<span>${__("Company: ")}<b>${frappe.utils.escape_html(ev.company)}</b></span> &bull; 
						<span>${__("As of: ")}${frappe.utils.escape_html(ev.as_of || "")}</span> &bull; 
						<span>${__("Retrieved: ")}${frappe.utils.escape_html(ev.retrieved_at || "")}</span>
					</div>
					<div class="text-muted mt-1" style="font-size: 11px; word-break: break-all;">
						<code>${filterSnippet}</code>
					</div>
				</div>
			`;
		});

		container.html(itemsHtml);
	}

	render_error(type, message) {
		const banner = $(`<div class="lotus-banner lotus-banner-danger mt-3">
			<div>
				<b>[${type}]</b> ${frappe.utils.escape_html(message)}
			</div>
		</div>`);
		this.main.find("#lotus-banner-container").empty().append(banner);
		this.main.find("#lotus-kpi-cards").empty();
		this.main.find("#lotus-comparison-content").empty();
		this.main.find("#lotus-ai-content").empty();
		this.main.find("#lotus-action-content").empty();
		this.main.find("#lotus-evidence-content").empty();
	}

	open_approved_report(reportName) {
		const approvedList = [
			"Profit and Loss Statement",
			"Accounts Receivable",
			"Accounts Payable",
			"General Ledger",
			"Trial Balance",
			"Cash Flow"
		];

		if (!approvedList.includes(reportName)) {
			frappe.msgprint({
				title: __("Access Restricted"),
				indicator: "orange",
				message: __("Navigation to this report is not permitted under AI001.")
			});
			return;
		}

		frappe.set_route("query-report", reportName, {
			company: this.current_company
		});
	}
};
