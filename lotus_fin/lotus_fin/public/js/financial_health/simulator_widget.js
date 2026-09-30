// Lotus Fin Financial Health - Simulator Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.SimulatorWidget = class SimulatorWidget {
	static formatSimVal(val, meta) {
		if (val === null || val === undefined) return "—";
		if (meta.is_ratio) {
			return `${(val * 100).toFixed(2)}%`;
		}
		if (meta.is_days) {
			return `${val.toFixed(1)} ngày`;
		}
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}

	static renderResults(container, res) {
		container.empty();

		const kpis = [
			{ id: "revenue", label: __("1. Doanh thu (Revenue)"), is_currency: true },
			{ id: "gross_profit", label: __("2. Lợi nhuận gộp (Gross Profit)"), is_currency: true },
			{ id: "gross_margin", label: __("3. Biên lợi nhuận gộp (Gross Margin)"), is_ratio: true },
			{ id: "ar_outstanding", label: __("4. Phải thu khách hàng (AR)"), is_currency: true },
			{ id: "dso", label: __("5. Số ngày thu tiền (DSO)"), is_days: true },
			{ id: "net_cash_flow", label: __("6. Dòng tiền thuần (Net Cash Flow)"), is_currency: true },
			{ id: "ending_cash", label: __("7. Số dư tiền cuối kỳ (Ending Cash)"), is_currency: true },
			{ id: "ccc", label: __("8. Chu kỳ chuyển đổi tiền (CCC)"), is_days: true },
			{ id: "cash_shortfall", label: __("9. Thâm hụt tiền an toàn (Cash Shortfall)"), is_currency: true }
		];

		let rowsHtml = "";
		kpis.forEach(k => {
			const item = res[k.id];
			if (!item) return;

			const baseStr = this.formatSimVal(item.baseline, k);
			const simStr = this.formatSimVal(item.simulation, k);
			const absStr = this.formatSimVal(item.absolute_change, k);
			let relStr = "—";
			if (item.relative_change !== null && item.relative_change !== undefined) {
				const pct = (item.relative_change * 100).toFixed(2);
				relStr = `${item.relative_change > 0 ? '+' : ''}${pct}%`;
			}

			let statusBadge = `<span class="badge ${item.status === 'HEALTHY' ? 'badge-success' : (item.status === 'WARNING' ? 'badge-warning' : 'badge-danger')}">${item.status}</span>`;

			rowsHtml += `<tr>
				<td class="font-weight-bold">${k.label}</td>
				<td>${baseStr}</td>
				<td class="font-weight-bold text-primary">${simStr}</td>
				<td>${absStr}</td>
				<td>${relStr}</td>
				<td>${statusBadge}</td>
			</tr>`;
		});

		let shortfallAlert = "";
		if (res.shortfall_events && res.shortfall_events.length > 0) {
			const events = res.shortfall_events.map(e => `<li>${frappe.utils.escape_html(typeof e === 'string' ? e : e.recommended_action || e.date)}</li>`).join("");
			shortfallAlert = `<div class="lotus-banner lotus-banner-danger mt-2">
				<div><b>⚠️ Cảnh báo thâm hụt tiền mặt (Cash Deficit):</b><ul class="mb-0 pl-3 mt-1">${events}</ul></div>
			</div>`;
		} else {
			shortfallAlert = `<div class="lotus-banner lotus-banner-warning mt-2">
				<div><b>✅ Kịch bản an toàn:</b> Dòng tiền sau mô phỏng vẫn duy trì số dư dương và không có sự kiện thâm hụt tiền mặt.</div>
			</div>`;
		}

		container.html(`
			<table class="lotus-table mt-2">
				<thead>
					<tr>
						<th>${__("Chỉ số KPI")}</th>
						<th>${__("Gốc (Baseline)")}</th>
						<th>${__("Sau mô phỏng")}</th>
						<th>${__("Biến động tuyệt đối")}</th>
						<th>${__("Biến động tương đối")}</th>
						<th>${__("Trạng thái")}</th>
					</tr>
				</thead>
				<tbody>
					${rowsHtml}
				</tbody>
			</table>
			${shortfallAlert}
		`);
	}
};
