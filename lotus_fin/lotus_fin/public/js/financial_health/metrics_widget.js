// Lotus Fin Financial Health - Metrics & Banner Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.MetricsWidget = class MetricsWidget {
	static renderMetaBar(metaBar, data) {
		const status = data.status || "UNKNOWN";
		const timeStr = data.as_of ? frappe.datetime.comment_when(data.as_of) : __("Just now");
		let statusClass = "status-ok";
		if (status === "PARTIAL" || status === "INSUFFICIENT_DATA") statusClass = "status-warn";
		if (status === "SOURCE_ERROR" || status === "FORBIDDEN") statusClass = "status-error";

		metaBar.html(`
			<span class="lotus-meta-tag ${statusClass}">${__("Status: ")}${frappe.utils.escape_html(status)}</span>
			<span class="lotus-meta-tag status-ok ml-1">${__("Actual Data &bull; ")}${frappe.utils.escape_html(data.currency || "VND")}</span>
			<span class="lotus-meta-tag ml-1 text-muted">${__("Updated: ")}${timeStr}</span>
		`);
	}

	static renderBanners(container, data) {
		container.empty();
		const limitations = data.limitations || [];

		if (data.status === "INSUFFICIENT_DATA") {
			$(`<div class="lotus-banner lotus-banner-warning">
				<div><b>${__("No Financial Activity:")}</b> ${__("No recorded transactions or financial statements exist for the selected period. Displaying verified state.")}</div>
			</div>`).appendTo(container);
		} else if (data.status === "PARTIAL") {
			$(`<div class="lotus-banner lotus-banner-warning">
				<div><b>${__("Notice on Data Availability:")}</b> ${__("Certain report sources returned partial or unconfigured values. Metrics with verified ledger data remain authoritative.")}</div>
			</div>`).appendTo(container);
		}

		if (limitations.length > 0) {
			const limItems = limitations.map(l => `<li>${frappe.utils.escape_html(l)}</li>`).join("");
			$(`<div class="lotus-banner lotus-banner-info">
				<div><b>${__("Active System Boundaries & Limitations:")}</b><ul class="mb-0 mt-1 pl-3">${limItems}</ul></div>
			</div>`).appendTo(container);
		}
	}

	static renderCards(container, data) {
		container.empty();
		const metrics = data.metrics || [];
		const metricMap = {};
		metrics.forEach(m => { metricMap[m.metric_id] = m; });

		const approved = [
			{ id: "revenue", label: __("Revenue"), is_currency: true },
			{ id: "cogs", label: __("COGS"), is_currency: true },
			{ id: "gross_margin", label: __("Gross Margin"), is_ratio: true },
			{ id: "cash_balance", label: __("Cash Balance"), is_currency: true },
			{ id: "ar_outstanding", label: __("AR Outstanding"), is_currency: true },
			{ id: "overdue_ar_ratio", label: __("Overdue AR Ratio"), is_ratio: true },
			{ id: "ap_outstanding", label: __("AP Outstanding"), is_currency: true },
			{ id: "near_term_ap", label: __("Near-Term AP"), is_currency: true }
		];

		approved.forEach(meta => {
			const m = metricMap[meta.id];
			let valHtml = `<span class="text-muted font-weight-normal">${__("Unavailable")}</span>`;
			let stateBadge = `<span class="lotus-kpi-state-badge lotus-kpi-state-unavailable">${__("Unavailable")}</span>`;
			let subtext = "";
			let isCashNegative = false;

			if (m && m.status === "AVAILABLE" && m.value !== null) {
				stateBadge = `<span class="lotus-kpi-state-badge lotus-kpi-state-available">${__("Verified")}</span>`;
				if (meta.is_ratio) {
					const pct = (m.value * 100).toFixed(2);
					valHtml = `${pct}<span class="lotus-kpi-unit">%</span>`;
				} else {
					const formatted = frappe.format(m.value, { fieldtype: "Currency", currency: m.currency_or_unit || "VND" });
					if (meta.id === "cash_balance" && m.value < 0) isCashNegative = true;
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
				<div class="lotus-kpi-value ${isCashNegative ? 'cash-negative' : ''}">${valHtml}</div>
				<div class="lotus-kpi-subtext">${subtext}</div>
			</div>`);
			container.append(card);
		});
	}
};
