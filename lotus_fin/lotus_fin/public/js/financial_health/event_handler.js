// Lotus Fin Financial Health - Event Handler
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.EventHandler = class EventHandler {
	static bind(controller) {
		const main = controller.main;

		main.on("click", "#lotus-toggle-evidence-btn", () => {
			main.find("#lotus-evidence-content").slideToggle(150);
		});

		main.on("click", "[data-open-report]", function (e) {
			e.preventDefault();
			controller.open_approved_report($(this).attr("data-open-report"));
		});

		main.on("input", "#input-sim-sales", function () {
			main.find("#val-sim-sales").text($(this).val() + "%");
		});

		main.on("input", "#input-sim-delay", function () {
			main.find("#val-sim-delay").text("+" + $(this).val() + " ngày");
		});

		main.on("input", "#input-sim-supplier", function () {
			main.find("#val-sim-supplier").text($(this).val() + " ngày");
		});

		main.on("click", "#btn-run-simulation", () => {
			controller.run_what_if_simulation();
		});

		main.on("click", ".lotus-quick-pill", function () {
			const q = $(this).attr("data-query");
			main.find("#input-copilot-query").val(q);
			controller.ask_financing_copilot(q);
		});

		main.on("click", "#btn-ask-copilot", () => {
			const q = main.find("#input-copilot-query").val();
			if (q && q.trim()) controller.ask_financing_copilot(q.trim());
		});
	}
};
