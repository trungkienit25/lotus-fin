// Lotus Fin What-If Scenario Simulation & Cash Stress-Testing Studio Page Controller
frappe.provide("lotus_fin.what_if_page");

frappe.pages["what-if-studio"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("What-If Stress Testing Studio"),
		single_column: true
	});

	wrapper.what_if_page = new lotus_fin.what_if_page.Controller(wrapper);
};

frappe.pages["what-if-studio"].refresh = function (wrapper) {
	if (wrapper.what_if_page) {
		wrapper.what_if_page.refresh();
	}
};

lotus_fin.what_if_page.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
	}

	setup_breadcrumbs() {
		frappe.breadcrumbs.add("Accounts");
	}

	setup_filters() {
		const me = this;
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
				}
			}
		});

		this.current_company = this.company_field.get_value() || frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company");

		this.page.set_secondary_action(__("🤖 Lotus Fin Copilot"), function() {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("📊 Financial Health"), function() {
			frappe.set_route("financial-health");
		});

		this.page.set_primary_action(__("Run Stress-Test Simulation"), function () {
			if (me.studio && typeof me.studio.run_simulation === "function") {
				me.studio.run_simulation();
			}
		}, "octicon octicon-play");
	}

	setup_dom() {
		const me = this;
		this.main = $(`<div class="lotus-financial-health-container" style="max-width: 1100px; margin: 0 auto; padding-top: 10px;">
			<div class="lotus-fh-header-card" style="margin-bottom: 20px;">
				<div class="d-flex justify-content-between align-items-center">
					<div>
						<span class="lotus-brand-badge">Lotus Fin &bull; AI-F004 / AI-F005</span>
						<h1 class="lotus-fh-title">🔮 ${__("What-If Scenario Simulation & Cash Stress-Testing Studio")}</h1>
						<p class="lotus-fh-subtitle">${__("9-KPI quantitative stress engine: Revenue, AR/AP, Fixed Costs, and Financing Injections")}</p>
					</div>
					<div class="text-right">
						<span class="lotus-meta-tag status-ok">Engine: 9-KPI Deterministic Model</span>
					</div>
				</div>
			</div>
			<div id="what-if-container"></div>
		</div>`).appendTo(this.page.main);

		// Instantiate reusable WhatIfStudio component
		this.studio = new lotus_fin.components.WhatIfStudio({
			parent: this.main.find("#what-if-container"),
			get_company: () => me.company_field ? me.company_field.get_value() : me.current_company,
			title: __("What-If Scenario Simulation & Cash Stress-Testing Studio"),
			badge: __("9-KPI Deterministic Simulation • Multi-Variable Stress Engine")
		});
	}

	refresh() {
		// Nothing blocking on refresh
	}
};
