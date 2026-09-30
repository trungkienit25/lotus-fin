// Lotus Fin Financial Health - Narrative & Drilldown Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.NarrativeWidget = class NarrativeWidget {
	static render(container, badgeEl, exp) {
		container.empty();

		if (!exp || exp.status === "UNAVAILABLE" || exp.status !== "AVAILABLE") {
			badgeEl.removeClass("lotus-ai-badge").addClass("badge badge-secondary").text(__("Degraded / Unavailable"));
			container.html(`
				<div class="lotus-banner lotus-banner-warning">
					<div><b>${__("AI Explanation Unavailable:")}</b> ${__("AI narrative generation is currently unavailable. Deterministic financial metrics, period comparison, and evidence refs remain authoritative and fully preserved.")}</div>
				</div>
			`);
			return;
		}

		badgeEl.removeClass("badge-secondary").addClass("lotus-ai-badge").text(__("Grounded Analysis"));

		const factsHtml = (exp.facts || []).map(f => `<li>${frappe.utils.escape_html(f)}</li>`).join("");
		const interpHtml = (exp.interpretations || []).map(i => `<li>${frappe.utils.escape_html(i)}</li>`).join("");
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

	static renderActions(container, exp) {
		container.empty();
		const nextChecks = (exp && exp.next_checks) || [
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
};
