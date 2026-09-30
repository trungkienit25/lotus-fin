// Lotus Fin Financial Health - Layout Template
frappe.provide("lotus_fin.financial_health");

lotus_fin.financial_health.LayoutTemplate = class LayoutTemplate {
	static getHtml() {
		return `<div class="lotus-financial-health-container">
			<div class="lotus-fh-header-card">
				<div class="d-flex justify-content-between align-items-start">
					<div>
						<span class="lotus-brand-badge">Lotus Fin &bull; AI-F001</span>
						<h1 class="lotus-fh-title">${__("Financial Health Analyst")}</h1>
						<p class="lotus-fh-subtitle">${__("SME Financial Intelligence & Continuous Health Inspection")}</p>
					</div>
					<div class="text-right" id="lotus-meta-bar">
						<span class="lotus-meta-tag status-ok">${__("Data Mode: Actual")}</span>
						<span class="lotus-meta-tag status-warn ml-2" id="lotus-retrieval-time">${__("Waiting for analysis...")}</span>
					</div>
				</div>
			</div>
			<div id="lotus-banner-container"></div>
			<div class="lotus-section-card">
				<div class="lotus-section-title">
					<span>${__("Key Financial Metrics")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;">${__("Formula v2026.1 &bull; Deterministic Accounting Verification")}</span>
				</div>
				<div class="lotus-kpi-grid" id="lotus-kpi-cards"></div>
			</div>
			<div class="lotus-section-card" id="lotus-comparison-section">
				<div class="lotus-section-title">
					<span>${__("Period Comparison")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;" id="lotus-comparison-subtitle">${__("Equal-length historical span")}</span>
				</div>
				<div id="lotus-comparison-content"></div>
			</div>
			<div class="lotus-section-card" id="lotus-ai-section">
				<div class="lotus-section-title">
					<span>🤖 ${__("AI Financial Analysis & Narrative")}</span>
					<span class="lotus-ai-badge" id="lotus-ai-status-badge">${__("Grounded Explanation")}</span>
				</div>
				<div id="lotus-ai-content"></div>
			</div>
			<div class="lotus-section-card" id="lotus-simulator-section">
				<div class="lotus-section-title">
					<span>🔮 ${__("What-If Scenario Simulation & Cash Stress-Test")}</span>
					<span class="lotus-ai-badge">${__("9-KPI Engine • AI-F004")}</span>
				</div>
				<div class="lotus-sim-grid">
					<div class="lotus-sim-control">
						<div class="lotus-sim-label"><span>${__("Biến động Doanh thu (%)")}</span><b id="val-sim-sales">-15%</b></div>
						<input type="range" class="custom-range" id="input-sim-sales" min="-50" max="50" step="5" value="-15">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label"><span>${__("Khách hàng chậm trả (Ngày)")}</span><b id="val-sim-delay">+15 ngày</b></div>
						<input type="range" class="custom-range" id="input-sim-delay" min="0" max="60" step="5" value="15">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label"><span>${__("Dời hạn trả NCC (Ngày)")}</span><b id="val-sim-supplier">0 ngày</b></div>
						<input type="range" class="custom-range" id="input-sim-supplier" min="-30" max="60" step="5" value="0">
					</div>
					<div class="lotus-sim-control">
						<div class="lotus-sim-label"><span>${__("Tiếp nhận vốn vay (VND)")}</span></div>
						<select class="lotus-sim-input" id="input-sim-financing">
							<option value="0">${__("Không nhận vốn")}</option>
							<option value="300000000" selected>300.000.000 VND (12T - 9.5%)</option>
							<option value="500000000">500.000.000 VND (12T - 9.5%)</option>
							<option value="1000000000">1.000.000.000 VND (24T - 9.0%)</option>
						</select>
					</div>
				</div>
				<div class="mb-3 d-flex gap-2">
					<button class="lotus-sim-btn" id="btn-run-simulation">🚀 ${__("Chạy mô phỏng What-If (9 KPIs)")}</button>
				</div>
				<div id="lotus-simulation-result"></div>
			</div>
			<div class="lotus-section-card" id="lotus-copilot-section">
				<div class="lotus-section-title">
					<span>💡 ${__("AI Financing Copilot & Credit Matcher")}</span>
					<span class="lotus-ai-badge">${__("Decision Support • AI-F005")}</span>
				</div>
				<div>
					<div class="mb-2">
						<span class="text-muted" style="font-size: 11px;">${__("Gợi ý câu hỏi nhanh:")}</span>
						<span class="lotus-quick-pill" data-query="Vay 500 triệu bổ sung vốn lưu động 12 tháng">${__("Vay 500tr lưu động 12T")}</span>
						<span class="lotus-quick-pill" data-query="Doanh nghiệp cần vay 1.5 tỷ mua máy móc thiết bị mở rộng quy mô">${__("Vay 1.5 tỷ mua máy móc")}</span>
						<span class="lotus-quick-pill" data-query="Chiết khấu hóa đơn công nợ 300 triệu trong 6 tháng">${__("Chiết khấu hóa đơn 300tr")}</span>
					</div>
					<div class="lotus-copilot-input-box">
						<input type="text" class="lotus-copilot-input" id="input-copilot-query" placeholder="${__("Nhập câu hỏi hoặc nhu cầu vốn...")}" />
						<button class="lotus-sim-btn" id="btn-ask-copilot">🤖 ${__("Tư vấn gói vay")}</button>
					</div>
				</div>
				<div id="lotus-copilot-result"></div>
			</div>
			<div class="lotus-section-card" id="lotus-action-section">
				<div class="lotus-section-title">
					<span>🔍 ${__("Recommended Next Review Actions")}</span>
					<span class="text-muted" style="font-size: 11px; font-weight: normal;">${__("Bounded Drill-down & Ledger Inspection (Read-Only)")}</span>
				</div>
				<div id="lotus-action-content"></div>
			</div>
			<div class="lotus-section-card" id="lotus-evidence-section">
				<div class="lotus-section-title">
					<span>📋 ${__("Evidence & Audit Provenance")}</span>
					<button class="btn btn-xs btn-default" id="lotus-toggle-evidence-btn">${__("Toggle Details")}</button>
				</div>
				<div id="lotus-evidence-content" style="display: block;"></div>
			</div>
		</div>`;
	}
};
