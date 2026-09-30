// Lotus Fin Financial Health - Filter Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.FilterWidget = class FilterWidget {
	static setup(ctrl) {
		const curYear = frappe.datetime.get_today().slice(0, 4);

		ctrl.company_field = ctrl.page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"),
			change() {
				const val = ctrl.company_field.get_value();
				if (val && val !== ctrl.current_company) {
					ctrl.current_company = val;
					ctrl.fetch_financial_health();
				}
			}
		});

		ctrl.period_field = ctrl.page.add_field({
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
				ctrl.apply_period_preset(ctrl.period_field.get_value());
				ctrl.fetch_financial_health();
			}
		});

		ctrl.comparison_field = ctrl.page.add_field({
			fieldname: "comparison_mode",
			label: __("Comparison"),
			fieldtype: "Select",
			options: [
				{ label: "Previous Period", value: "PREVIOUS_PERIOD" },
				{ label: "None", value: "NONE" }
			],
			default: "PREVIOUS_PERIOD",
			change() {
				ctrl.fetch_financial_health();
			}
		});

		ctrl.page.set_primary_action(__("Analyze Financial Health"), function () {
			ctrl.fetch_financial_health(true);
		}, "octicon octicon-sync");

		ctrl.apply_period_preset("CURRENT_YEAR");
		if (ctrl.period_field) ctrl.period_field.set_value("CURRENT_YEAR");
	}

	static applyPeriodPreset(ctrl, preset) {
		if (preset === "FY2020") {
			ctrl.period_start = "2020-01-01";
			ctrl.period_end = "2020-12-31";
		} else if (preset === "FY2025") {
			ctrl.period_start = "2025-01-01";
			ctrl.period_end = "2025-12-31";
		} else {
			const curYear = frappe.datetime.get_today().slice(0, 4);
			ctrl.period_start = `${curYear}-01-01`;
			ctrl.period_end = `${curYear}-12-31`;
		}
	}
};
