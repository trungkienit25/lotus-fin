// Lotus Fin — Core DOM & Formatting Helper
frappe.provide("lotus_fin.core");

lotus_fin.core.cn = function (...classes) {
	return classes.filter(Boolean).join(" ");
};

lotus_fin.core.format_currency = function (value, currency = "VND") {
	if (value === null || value === undefined || isNaN(value)) {
		return "—";
	}
	return frappe.format(value, { fieldtype: "Currency", currency: currency });
};

lotus_fin.core.format_percent = function (value, decimals = 1) {
	if (value === null || value === undefined || isNaN(value)) {
		return "—";
	}
	const pct = value > 1 ? value : value * 100;
	return `${pct.toFixed(decimals)}%`;
};

lotus_fin.core.format_date = function (dateStr) {
	if (!dateStr) return "—";
	return frappe.datetime.str_to_user(dateStr);
};
