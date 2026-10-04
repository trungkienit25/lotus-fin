// Lotus Fin AI Copilot Page Controller
frappe.provide("lotus_fin.copilot_page");

frappe.pages["lotus-copilot"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Lotus Fin AI Copilot"),
		single_column: true
	});

	wrapper.copilot_page = new lotus_fin.copilot_page.Controller(wrapper);
};

frappe.pages["lotus-copilot"].refresh = function (wrapper) {
	if (wrapper.copilot_page) {
		wrapper.copilot_page.refresh();
	}
};

lotus_fin.copilot_page.Controller = class Controller {
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

		this.page.set_secondary_action(__("📊 Sức khỏe tài chính"), function() {
			frappe.set_route("financial-health");
		});

		this.page.add_inner_button(__("💧 Dòng tiền (AI002)"), function() {
			frappe.set_route("cash-forecast");
		});

		this.page.add_inner_button(__("⚠️ Rủi ro (AI003)"), function() {
			frappe.set_route("risk-signal");
		});

		this.page.add_inner_button(__("🔮 What-If (AI004)"), function() {
			frappe.set_route("what-if-studio");
		});

		this.page.add_inner_button(__("🏦 Gói vay (AI005)"), function() {
			frappe.set_route("financing-copilot");
		});

		this.page.add_inner_button(__("📑 Lịch trả nợ (AI006)"), function() {
			frappe.set_route("repayment-schedule");
		});
	}

	setup_dom() {
		const me = this;
		this.main = $(`<div class="lotus-financial-health-container" style="max-width: 1040px; margin: 0 auto; padding-top: 10px;">
			<div class="lotus-fh-header-card" style="margin-bottom: 20px;">
				<div class="d-flex justify-content-between align-items-center">
					<div>
						<span class="lotus-brand-badge">Lotus Fin &bull; AI Agentic Copilot</span>
						<h1 class="lotus-fh-title">🤖 ${__("Trợ lý Tài chính AI Copilot")}</h1>
						<p class="lotus-fh-subtitle">${__("Hỏi đáp thông minh, phân tích tự nhiên, điều phối Tool-Calling chuyên sâu")}</p>
					</div>
					<div class="text-right">
						<span class="lotus-meta-tag status-ok">Engine: Tool Calling Active</span>
					</div>
				</div>
			</div>
			<div id="copilot-container"></div>
		</div>`).appendTo(this.page.main);

		// Instantiate reusable ChatCopilot component
		this.copilot = new lotus_fin.components.ChatCopilot({
			parent: this.main.find("#copilot-container"),
			get_company: () => me.company_field ? me.company_field.get_value() : me.current_company,
			title: __("Lotus Fin AI Copilot — Đối thoại & Điều phối Nghiệp vụ"),
			badge: __("Deterministic Tool Calling • Real-time Accounting Data"),
			min_height: "560px",
			show_quick_pills: true
		});
	}

	refresh() {
		// Nothing blocking on refresh
	}
};
