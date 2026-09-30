// Lotus Fin Financial Health Page Controller - Modular Core
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
		lotus_fin.financial_health.FilterWidget.setup(this);
	}

	apply_period_preset(preset) {
		lotus_fin.financial_health.FilterWidget.applyPeriodPreset(this, preset);
	}

	setup_dom() {
		const html = lotus_fin.financial_health.LayoutTemplate.getHtml();
		this.main = $(html).appendTo(this.page.main);
	}

	setup_events() {
		lotus_fin.financial_health.EventHandler.bind(this);
	}

	load_default_company_and_fetch() {
		const me = this;
		if (this.company_field && this.company_field.get_value()) {
			this.current_company = this.company_field.get_value();
			this.fetch_financial_health();
		} else {
			frappe.call({
				method: "frappe.client.get_list",
				args: { doctype: "Company", fields: ["name"], limit: 1 },
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
		if (this.current_company) this.fetch_financial_health();
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

		const compMode = this.comparison_field ? this.comparison_field.get_value() : "PREVIOUS_PERIOD";
		const W = lotus_fin.financial_health;

		W.ApiClient.fetchSnapshot({
			company: company,
			period_start: this.period_start,
			period_end: this.period_end,
			currency: "VND",
			comparison: compMode === "NONE" ? null : "PREVIOUS_PERIOD",
			include_explanation: force_include_explanation ? 1 : 0
		}).then(data => {
			me.data = data;
			me.render();
		}).catch(err => {
			const errMsg = (err && err.message) ? err.message : __("Failed to contact Lotus Fin engine.");
			me.render_error("FORBIDDEN", errMsg);
		});
	}

	render() {
		if (!this.data) return;
		const W = lotus_fin.financial_health;
		W.MetricsWidget.renderMetaBar(this.main.find("#lotus-meta-bar"), this.data);

		if (this.data.status === "FORBIDDEN") {
			this.render_error("FORBIDDEN", __("Access denied. You do not have permission to view financial records for this company."));
			return;
		}

		W.MetricsWidget.renderBanners(this.main.find("#lotus-banner-container"), this.data);
		W.MetricsWidget.renderCards(this.main.find("#lotus-kpi-cards"), this.data);
		W.ComparisonWidget.render(this.main.find("#lotus-comparison-content"), this.main.find("#lotus-comparison-subtitle"), this.data.comparison);
		W.NarrativeWidget.render(this.main.find("#lotus-ai-content"), this.main.find("#lotus-ai-status-badge"), this.data.explanation);
		W.NarrativeWidget.renderActions(this.main.find("#lotus-action-content"), this.data.explanation);
		W.EvidenceWidget.render(this.main.find("#lotus-evidence-content"), this.data.evidence_refs);
	}

	run_what_if_simulation() {
		const me = this;
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const container = this.main.find("#lotus-simulation-result");
		container.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("Đang tính toán mô phỏng 9 chỉ số...")}</div>`);

		lotus_fin.financial_health.ApiClient.simulateScenario({
			company: company,
			sales_change_pct: parseFloat(this.main.find("#input-sim-sales").val()) / 100.0,
			collection_delay_days: parseInt(this.main.find("#input-sim-delay").val(), 10),
			supplier_due_shift_days: parseInt(this.main.find("#input-sim-supplier").val(), 10),
			financing_amount: parseFloat(this.main.find("#input-sim-financing").val())
		}).then(res => {
			lotus_fin.financial_health.SimulatorWidget.renderResults(container, res);
		}).catch(err => {
			container.html(`<div class="lotus-banner lotus-banner-danger">${err.message}</div>`);
		});
	}

	ask_financing_copilot(queryText) {
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const container = this.main.find("#lotus-copilot-result");
		container.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("AI Copilot đang phân tích nhu cầu...")}</div>`);

		lotus_fin.financial_health.ApiClient.askCopilot({
			company: company,
			query: queryText
		}).then(res => {
			lotus_fin.financial_health.CopilotWidget.renderResult(container, res);
		}).catch(err => {
			container.html(`<div class="lotus-banner lotus-banner-danger">${err.message}</div>`);
		});
	}

	render_error(status, message) {
		const container = this.main.find("#lotus-banner-container").empty();
		$(`<div class="lotus-banner lotus-banner-danger">
			<div><b>${__("Security / Permission Error:")}</b> ${frappe.utils.escape_html(message)}</div>
		</div>`).appendTo(container);
		this.main.find("#lotus-kpi-cards").empty();
		this.main.find("#lotus-comparison-content").empty();
		this.main.find("#lotus-ai-content").empty();
		this.main.find("#lotus-evidence-content").empty();
		this.main.find("#lotus-retrieval-time").text(__("Failed"));
	}

	open_approved_report(reportName) {
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const filters = { company: company };
		if (reportName === "Profit and Loss Statement") {
			filters.from_fiscal_year = this.period_start.slice(0, 4);
			filters.to_fiscal_year = this.period_end.slice(0, 4);
			filters.period_start_date = this.period_start;
			filters.period_end_date = this.period_end;
		} else if (reportName === "Accounts Receivable" || reportName === "Accounts Payable") {
			filters.report_date = this.period_end;
		}
		frappe.set_route("query-report", reportName, filters);
	}
};
