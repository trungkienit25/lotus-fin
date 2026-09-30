// Lotus Fin Financial Health - Copilot Widget
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.CopilotWidget = class CopilotWidget {
	static renderResult(container, res) {
		container.empty();
		const intent = res.parsed_intent || {};
		const advice = res.ai_advice || {};
		const matchRes = res.deterministic_matching_result || {};
		const matchedProds = matchRes.matched_products || [];

		// Intent Banner
		const intentHtml = `<div class="lotus-banner lotus-banner-info mb-2">
			<div>
				<b>🎯 Ý định nhận diện (NLU Intent):</b> Nhu cầu vốn: <b>${frappe.format(intent.amount, { fieldtype: "Currency", currency: "VND" })}</b> &bull; Kỳ hạn: <b>${intent.term_months} tháng</b> &bull; Mục đích: <b>${intent.purpose}</b>
			</div>
		</div>`;

		// Executive summary
		const execSummary = advice.executive_summary ? `<div class="lotus-ai-box facts mb-2"><div class="lotus-ai-box-title">📊 Đánh giá tổng quan từ AI</div><div>${frappe.utils.escape_html(advice.executive_summary)}</div></div>` : "";

		// Top Products
		let productsHtml = "";
		matchedProds.slice(0, 3).forEach((p, idx) => {
			const isTop = idx === 0;
			const ratePct = (p.nominal_rate_annual * 100).toFixed(1);
			const interestStr = frappe.format(p.estimated_monthly_interest, { fieldtype: "Currency", currency: "VND" });
			productsHtml += `
				<div class="lotus-product-card ${isTop ? 'top-recommended' : ''}">
					<div class="d-flex justify-content-between align-items-center mb-1">
						<div>
							<span class="font-weight-bold" style="font-size: 14px;">${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</span>
							${isTop ? '<span class="badge badge-success ml-2">⭐ Khuyến nghị tối ưu</span>' : ''}
						</div>
						<span class="lotus-score-badge">Điểm: ${p.match_score}/100</span>
					</div>
					<div class="row mt-2" style="font-size: 12px;">
						<div class="col-md-3"><b>Lãi suất:</b> <span class="text-success font-weight-bold">${ratePct}%/năm</span></div>
						<div class="col-md-3"><b>Lãi ước tính:</b> ~${interestStr}/tháng</div>
						<div class="col-md-3"><b>Giải ngân:</b> ~${p.disbursement_speed_days} ngày</div>
						<div class="col-md-3"><b>Loại:</b> ${p.product_type === 'UNSECURED_LOAN' ? 'Tín chấp' : 'Thế chấp'}</div>
					</div>
				</div>
			`;
		});

		// Tradeoff & Warning
		let warningHtml = "";
		if (advice.cashflow_impact_warning) {
			warningHtml = `<div class="lotus-banner lotus-banner-warning mt-2">
				<div><b>⚠️ Cảnh báo dòng tiền (Cash Flow Impact):</b> ${frappe.utils.escape_html(advice.cashflow_impact_warning)}</div>
			</div>`;
		}

		container.html(`
			${intentHtml}
			${execSummary}
			<div class="mt-2 mb-2 font-weight-bold" style="font-size: 13px;">🏆 Danh mục gói tín dụng phù hợp nhất (${matchedProds.length} gói):</div>
			${productsHtml || '<div class="text-muted p-2">Không tìm thấy gói tín dụng phù hợp với điều kiện.</div>'}
			${warningHtml}
		`);
	}
};
