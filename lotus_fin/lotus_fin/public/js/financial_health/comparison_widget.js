// Lotus Fin Financial Health - Comparison Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.ComparisonWidget = class ComparisonWidget {
	static formatVal(val, meta) {
		if (val === null || val === undefined) return __("N/A");
		if (meta.is_ratio) {
			return `${(val * 100).toFixed(2)}%`;
		}
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}

	static render(container, subtitleEl, comp) {
		container.empty();

		if (!comp || comp.status === "UNAVAILABLE") {
			const reason = (comp && comp.limitations && comp.limitations[0]) 
				? comp.limitations[0] 
				: __("Previous-period data unavailable");
			container.html(`
				<div class="text-muted p-3 bg-light rounded text-center">
					<i class="octicon octicon-info mr-1"></i> ${frappe.utils.escape_html(reason)}
				</div>
			`);
			return;
		}

		const pPeriod = comp.previous_period || {};
		if (subtitleEl) {
			subtitleEl.text(__("Compared against previous period: ") + `${pPeriod.start || ""} to ${pPeriod.end || ""}`);
		}

		const compMetrics = comp.metrics || {};
		const rows = [
			{ id: "revenue", label: __("Revenue"), is_currency: true },
			{ id: "cogs", label: __("COGS"), is_currency: true },
			{ id: "gross_margin", label: __("Gross Margin"), is_ratio: true },
			{ id: "cash_balance", label: __("Cash Balance"), is_currency: true },
			{ id: "ar_outstanding", label: __("AR Outstanding"), is_currency: true },
			{ id: "overdue_ar_ratio", label: __("Overdue AR Ratio"), is_ratio: true },
			{ id: "ap_outstanding", label: __("AP Outstanding"), is_currency: true }
		];

		let tableRowsHtml = "";
		rows.forEach(r => {
			const item = compMetrics[r.id];
			if (!item) return;

			let curStr = item.current !== null ? this.formatVal(item.current, r) : __("N/A");
			let prevStr = item.previous !== null ? this.formatVal(item.previous, r) : __("Unavailable");
			let absChangeStr = __("N/A");
			let relChangeStr = __("N/A");

			if (item.status === "AVAILABLE") {
				if (item.absolute_change !== null) {
					absChangeStr = this.formatVal(item.absolute_change, r);
				}
				if (item.relative_change !== null) {
					const pct = (item.relative_change * 100).toFixed(2);
					relChangeStr = `${item.relative_change > 0 ? '+' : ''}${pct}%`;
				}
			}

			tableRowsHtml += `<tr>
				<td class="font-weight-bold">${r.label}</td>
				<td>${curStr}</td>
				<td>${prevStr}</td>
				<td>${absChangeStr}</td>
				<td>${relChangeStr}</td>
				<td><span class="badge ${item.status === 'AVAILABLE' ? 'badge-success' : 'badge-light'}">${item.status}</span></td>
			</tr>`;
		});

		container.html(`
			<table class="lotus-table">
				<thead>
					<tr>
						<th>${__("Metric")}</th>
						<th>${__("Current Period")}</th>
						<th>${__("Previous Period")}</th>
						<th>${__("Absolute Change")}</th>
						<th>${__("Relative Change")}</th>
						<th>${__("Availability")}</th>
					</tr>
				</thead>
				<tbody>
					${tableRowsHtml}
				</tbody>
			</table>
		`);
	}
};
