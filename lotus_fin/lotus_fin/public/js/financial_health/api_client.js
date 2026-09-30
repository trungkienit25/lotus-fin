// Lotus Fin Financial Health - Modular API Client
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.ApiClient = class ApiClient {
	static fetchSnapshot(args) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "lotus_fin.api.ai_insights.get_financial_snapshot",
				args: args,
				freeze: false,
				callback(r) {
					if (r.exc) {
						reject(new Error(__("An error occurred while gathering financial snapshot.")));
					} else if (r.message) {
						resolve(r.message);
					} else {
						reject(new Error(__("Empty response from financial snapshot service.")));
					}
				},
				error(err) {
					reject(err);
				}
			});
		});
	}

	static simulateScenario(args) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "lotus_fin.AI005.service.simulate_what_if",
				args: args,
				callback(r) {
					if (r.exc || !r.message) {
						reject(new Error(__("Mô phỏng What-if thất bại hoặc lỗi máy chủ.")));
					} else {
						resolve(r.message);
					}
				},
				error(err) {
					reject(err);
				}
			});
		});
	}

	static askCopilot(args) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "lotus_fin.AI005.service.ask_copilot",
				args: args,
				callback(r) {
					if (r.exc || !r.message) {
						reject(new Error(__("Không thể kết nối tới AI Financing Advisor.")));
					} else {
						resolve(r.message);
					}
				},
				error(err) {
					reject(err);
				}
			});
		});
	}
};
