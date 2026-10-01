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

			<!-- Section 4: AI004 / AI005 What-If Scenario Simulation -->
			<div class="lotus-section-card" id="lotus-simulator-section">
				<div class="lotus-section-title">
					<span>🔮 ${__("What-If Scenario Simulation & Cash Stress-Test")}</span>
					<span class="lotus-ai-badge">${__("9-KPI Engine • AI-F004")}</span>
				</div>
				<div class="lotus-sim-grid">
					<div class="lotus-sim-control">
						<div class="lotus-sim-label">
							<span>${__("Biến động Doanh thu (%)")}</span>
							<b id="val-sim-sales">-15%</b>
						</div>
						<input type="range" class="custom-range" id="input-sim-sales" min="-50" max="50" step="5" value="-15">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label">
							<span>${__("Khách hàng chậm trả (Ngày)")}</span>
							<b id="val-sim-delay">+15 ngày</b>
						</div>
						<input type="range" class="custom-range" id="input-sim-delay" min="0" max="60" step="5" value="15">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label">
							<span>${__("Dời hạn trả NCC (Ngày)")}</span>
							<b id="val-sim-supplier">0 ngày</b>
						</div>
						<input type="range" class="custom-range" id="input-sim-supplier" min="-30" max="60" step="5" value="0">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label">
							<span>${__("Tiếp nhận vốn vay (VND)")}</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-financing">
							<option value="0">${__("Không nhận vốn")}</option>
							<option value="300000000" selected>300.000.000 VND (12T - 9.5%)</option>
							<option value="500000000">500.000.000 VND (12T - 9.5%)</option>
							<option value="1000000000">1.000.000.000 VND (24T - 9.0%)</option>
						</select>
					</div>
				</div>
				<div class="mb-3 d-flex gap-2">
					<button class="lotus-sim-btn" id="btn-run-simulation">
						🚀 ${__("Chạy mô phỏng What-If (9 KPIs)")}
					</button>
				</div>
				<div id="lotus-simulation-result">
					<!-- Simulation table rendered here -->
				</div>
			</div>

			<!-- Section 5: AI005 Financing Copilot & Credit Matcher -->
			<div class="lotus-section-card" id="lotus-copilot-section">
				<div class="lotus-section-title">
					<span>💡 ${__("AI Financing Copilot & Credit Matcher")}</span>
					<span class="lotus-ai-badge">${__("Decision Support • AI-F005")}</span>
				</div>
				<div>
					<div class="mb-2">
						<span class="text-muted" style="font-size: 11px;">${__("Gợi ý câu hỏi nhanh:")}</span>
						<span class="lotus-quick-pill" data-query="Vay 500 triệu bổ sung vốn lưu động 12 tháng">${__("Vay 500tr lưu động 12T")}</span>
						<span class="lotus-quick-pill" data-query="Doanh nghiệp cần vay 1.5 tỷ mua máy móc thiết bị mở rộng quy mô">${__("Vay 1.5 tỷ mua máy móc")}</span>
						<span class="lotus-quick-pill" data-query="Chiết khấu hóa đơn công nợ 300 triệu trong 6 tháng">${__("Chiết khấu hóa đơn 300tr")}</span>
					</div>
					<div class="lotus-copilot-input-box">
						<input type="text" class="lotus-copilot-input" id="input-copilot-query" placeholder="${__("Nhập câu hỏi hoặc nhu cầu vốn (ví dụ: Doanh nghiệp cần vay 1 tỷ trong 12 tháng để mở rộng xưởng)...")}" />
						<button class="lotus-sim-btn" id="btn-ask-copilot">
							🤖 ${__("Tư vấn gói vay")}
						</button>
					</div>
				</div>
				<div id="lotus-copilot-result">
					<!-- Copilot result rendered here -->
				</div>
			</div>

			<!-- Section 6: Recommended Next Checks / Actionability -->
			<div class="lotus-section-card" id="lotus-action-section">
				<div class="lotus-section-title">
					<span>🔍 ${__("Recommended Next Review Actions")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;">${__("Bounded Drill-down & Ledger Inspection (Read-Only)")}</span>
				</div>
				<div id="lotus-action-content">
					<!-- Action buttons rendered here -->
				</div>
			</div>

			<!-- Section 7: Evidence & Data Quality -->
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

		// Simulator slider update events
		this.main.on("input", "#input-sim-sales", function () {
			me.main.find("#val-sim-sales").text($(this).val() + "%");
		});
		this.main.on("input", "#input-sim-delay", function () {
			me.main.find("#val-sim-delay").text("+" + $(this).val() + " ngày");
		});
		this.main.on("input", "#input-sim-supplier", function () {
			me.main.find("#val-sim-supplier").text($(this).val() + " ngày");
		});

		// Run Simulation click
		this.main.on("click", "#btn-run-simulation", function () {
			me.run_what_if_simulation();
		});

		// Quick pill query click
		this.main.on("click", ".lotus-quick-pill", function () {
			const q = $(this).attr("data-query");
			me.main.find("#input-copilot-query").val(q);
			me.ask_financing_copilot(q);
		});

		// Ask Copilot click
		this.main.on("click", "#btn-ask-copilot", function () {
			const q = me.main.find("#input-copilot-query").val();
			if (q && q.trim()) {
				me.ask_financing_copilot(q.trim());
			}
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

	run_what_if_simulation() {
		const me = this;
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const salesPct = (parseFloat(this.main.find("#input-sim-sales").val()) || 0) / 100.0;
		const delayDays = parseInt(this.main.find("#input-sim-delay").val()) || 0;
		const supplierDays = parseInt(this.main.find("#input-sim-supplier").val()) || 0;
		const finAmount = parseFloat(this.main.find("#input-sim-financing").val()) || 0;

		const container = this.main.find("#lotus-simulation-result");
		container.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("Đang tính toán mô phỏng 9 chỉ số...")}</div>`);

		frappe.call({
			method: "lotus_fin.AI005.service.simulate_what_if",
			args: {
				company: company,
				sales_change_pct: salesPct,
				collection_delay_days: delayDays,
				supplier_due_shift_days: supplierDays,
				financing_amount: finAmount,
				financing_term_months: finAmount > 0 ? 12 : 0,
				financing_rate_annual: finAmount > 0 ? 0.095 : 0.0
			},
			callback(r) {
				if (r.exc || !r.message) {
					container.html(`<div class="lotus-banner lotus-banner-danger">${__("Không thể chạy mô phỏng kịch bản.")}</div>`);
					return;
				}
				me.render_simulation_result(r.message);
			}
		});
	}

	render_simulation_result(res) {
		const container = this.main.find("#lotus-simulation-result").empty();
		const kpis = res.kpis_9_layer || {};
		const kpiList = [
			{ id: "revenue", label: __("1. Doanh thu (Revenue)"), is_currency: true },
			{ id: "gross_profit", label: __("2. Lợi nhuận gộp (Gross Profit)"), is_currency: true },
			{ id: "gross_margin", label: __("3. Biên LN gộp (Gross Margin)"), is_ratio: true },
			{ id: "ar_outstanding", label: __("4. Công nợ phải thu (AR)"), is_currency: true },
			{ id: "dso", label: __("5. Số ngày thu tiền (DSO)"), is_days: true },
			{ id: "net_cash_flow", label: __("6. Dòng tiền thuần (Net Cash Flow)"), is_currency: true },
			{ id: "ending_cash", label: __("7. Tiền mặt cuối kỳ (Ending Cash)"), is_currency: true },
			{ id: "ccc", label: __("8. Chu kỳ tiền mặt (CCC)"), is_days: true },
			{ id: "cash_shortfall", label: __("9. Thâm hụt dòng tiền (Shortfall)"), is_currency: true }
		];

		let rowsHtml = "";
		kpiList.forEach(k => {
			const item = kpis[k.id];
			if (!item) return;

			let baseStr = this.format_sim_val(item.baseline, k);
			let simStr = this.format_sim_val(item.simulation, k);
			let absStr = this.format_sim_val(item.absolute_change, k);
			let relStr = item.relative_change !== null ? `${(item.relative_change * 100).toFixed(1)}%` : "—";
			let statusBadge = `<span class="badge ${item.status === 'HEALTHY' ? 'badge-success' : (item.status === 'WARNING' ? 'badge-warning' : 'badge-danger')}">${item.status}</span>`;

			rowsHtml += `<tr>
				<td class="font-weight-bold">${k.label}</td>
				<td>${baseStr}</td>
				<td class="font-weight-bold text-primary">${simStr}</td>
				<td>${absStr}</td>
				<td>${relStr}</td>
				<td>${statusBadge}</td>
			</tr>`;
		});

		let shortfallAlert = "";
		if (res.shortfall_events && res.shortfall_events.length > 0) {
			const events = res.shortfall_events.map(e => `<li>${frappe.utils.escape_html(e)}</li>`).join("");
			shortfallAlert = `<div class="lotus-banner lotus-banner-danger mt-2">
				<div><b>⚠️ Cảnh báo thâm hụt tiền mặt (Cash Deficit):</b><ul class="mb-0 pl-3 mt-1">${events}</ul></div>
			</div>`;
		} else {
			shortfallAlert = `<div class="lotus-banner lotus-banner-warning mt-2">
				<div><b>✅ Kịch bản an toàn:</b> Dòng tiền sau mô phỏng vẫn duy trì số dư dương và không có sự kiện thâm hụt tiền mặt.</div>
			</div>`;
		}

		container.html(`
			<table class="lotus-table mt-2">
				<thead>
					<tr>
						<th>${__("Chỉ số KPI")}</th>
						<th>${__("Gốc (Baseline)")}</th>
						<th>${__("Sau mô phỏng")}</th>
						<th>${__("Biến động tuyệt đối")}</th>
						<th>${__("Biến động tương đối")}</th>
						<th>${__("Trạng thái")}</th>
					</tr>
				</thead>
				<tbody>
					${rowsHtml}
				</tbody>
			</table>
			${shortfallAlert}
		`);
	}

	format_sim_val(val, meta) {
		if (val === null || val === undefined) return "—";
		if (meta.is_ratio) {
			return `${(val * 100).toFixed(2)}%`;
		}
		if (meta.is_days) {
			return `${val.toFixed(1)} ngày`;
		}
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}

	ask_financing_copilot(queryText) {
		const me = this;
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const container = this.main.find("#lotus-copilot-result");
		container.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("AI Copilot đang phân tích nhu cầu và tìm kiếm gói tín dụng phù hợp...")}</div>`);

		frappe.call({
			method: "lotus_fin.AI005.service.ask_copilot",
			args: {
				company: company,
				query: queryText
			},
			callback(r) {
				if (r.exc || !r.message) {
					container.html(`<div class="lotus-banner lotus-banner-danger">${__("Không thể kết nối tới AI Financing Advisor.")}</div>`);
					return;
				}
				me.render_copilot_result(r.message);
			}
		});
	}

	render_copilot_result(res) {
		const container = this.main.find("#lotus-copilot-result").empty();
		const intent = res.parsed_intent || {};
		const advice = res.ai_advice || {};
		const matchRes = res.deterministic_matching_result || {};
		const matchedProds = matchRes.matched_products || [];

		// Intent Banner
		const intentHtml = `<div class="lotus-banner lotus-banner-info mb-2">
			<div>
				<b>🎯 Ý định nhận diện (NLU Intent):</b> Nhu cầu vốn: <b>${frappe.format(intent.amount, { fieldtype: "Currency", currency: "VND" })}</b> &bull; Kỳ hạn: <b>${intent.term_months} tháng</b> &bull; Mục đích: <b>${intent.purpose}</b>
			</div>
		</div>`;

		// Executive summary
		const execSummary = advice.executive_summary ? `<div class="lotus-ai-box facts mb-2"><div class="lotus-ai-box-title">📊 Đánh giá tổng quan từ AI</div><div>${frappe.utils.escape_html(advice.executive_summary)}</div></div>` : "";

		// Top Products
		let productsHtml = "";
		matchedProds.slice(0, 3).forEach((p, idx) => {
			const isTop = idx === 0;
			const ratePct = (p.nominal_rate_annual * 100).toFixed(1);
			const interestStr = frappe.format(p.estimated_monthly_interest, { fieldtype: "Currency", currency: "VND" });
			productsHtml += `
				<div class="lotus-product-card ${isTop ? 'top-recommended' : ''}">
					<div class="d-flex justify-content-between align-items-center mb-1">
						<div>
							<span class="font-weight-bold" style="font-size: 14px;">${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</span>
							${isTop ? '<span class="badge badge-success ml-2">⭐ Khuyến nghị tối ưu</span>' : ''}
						</div>
						<span class="lotus-score-badge">Điểm: ${p.match_score}/100</span>
					</div>
					<div class="row mt-2" style="font-size: 12px;">
						<div class="col-md-3"><b>Lãi suất:</b> <span class="text-success font-weight-bold">${ratePct}%/năm</span></div>
						<div class="col-md-3"><b>Lãi ước tính:</b> ~${interestStr}/tháng</div>
						<div class="col-md-3"><b>Giải ngân:</b> ~${p.disbursement_speed_days} ngày</div>
						<div class="col-md-3"><b>Loại:</b> ${p.tier === 'UNSECURED_WORKING_CAPITAL' ? 'Tín chấp' : 'Thế chấp'}</div>
					</div>
				</div>
			`;
		});

		// Tradeoff & Warning
		let warningHtml = "";
		if (advice.cashflow_impact_warning) {
			warningHtml = `<div class="lotus-banner lotus-banner-warning mt-2">
				<div><b>⚠️ Cảnh báo dòng tiền (Cash Flow Impact):</b> ${frappe.utils.escape_html(advice.cashflow_impact_warning)}</div>
			</div>`;
		}

		container.html(`
			${intentHtml}
			${execSummary}
			<div class="mt-2 mb-2 font-weight-bold" style="font-size: 13px;">🏆 Danh mục gói tín dụng phù hợp nhất (${matchedProds.length} gói):</div>
			${productsHtml || '<div class="text-muted p-2">Không tìm thấy gói tín dụng phù hợp với điều kiện.</div>'}
			${warningHtml}
		`);
	}
};

