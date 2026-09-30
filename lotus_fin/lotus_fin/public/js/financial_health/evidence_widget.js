// Lotus Fin Financial Health - Evidence & Provenance Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.EvidenceWidget = class EvidenceWidget {
	static render(container, evidenceRefs) {
		container.empty();

		if (!evidenceRefs || evidenceRefs.length === 0) {
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
};
