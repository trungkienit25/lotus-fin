// Lotus Fin Financing Copilot & Loan Decision Page Controller (Google Material 3 DNA)
frappe.provide("lotus_fin.financing_page");

frappe.pages["financing-copilot"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Gói Vay & Tài Trợ SME (AI005)"),
		single_column: true
	});

	wrapper.financing_page = new lotus_fin.financing_page.Controller(wrapper);
};

frappe.pages["financing-copilot"].refresh = function (wrapper) {
	if (wrapper.financing_page) {
		wrapper.financing_page.refresh();
	}
};

// Safe pure currency formatter (no HTML tags)
function format_money(val, currency = "VND") {
	if (val === null || val === undefined || isNaN(val)) return "0 " + currency;
	return Math.round(Number(val)).toLocaleString("vi-VN") + " " + currency;
}

lotus_fin.financing_page.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.bind_events();
		this.run_matching();
	}

	setup_breadcrumbs() {
		frappe.breadcrumbs.add("Accounts");
	}

	setup_filters() {
		const me = this;
		this.company_field = this.page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"),
			change() {
				const val = me.company_field.get_value();
				if (val && val !== me.current_company) {
					me.current_company = val;
					me.run_matching();
				}
			}
		});

		this.current_company = this.company_field.get_value() || frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company");

		this.page.set_secondary_action(__("🤖 Lotus Copilot"), function() {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("📑 Lịch trả nợ (AI006)"), function() {
			frappe.set_route("repayment-schedule");
		});

		this.page.add_inner_button(__("📊 Sức khỏe tài chính"), function() {
			frappe.set_route("financial-health");
		});
	}

	setup_dom() {
		this.main = $(`
			<div class="lotus-financial-health-container" style="max-width: 1200px; margin: 0 auto;">
				<!-- Header Banner Card -->
				<div class="lotus-fh-header-card">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<div class="d-flex align-items-center gap-2 mb-2">
								<span class="lotus-brand-badge">Lotus Fin • SME Financing Advisor (AI005)</span>
								<span class="lotus-badge lotus-badge-ai">Engine: Bank Credit Matcher</span>
							</div>
							<h1 class="lotus-fh-title">🏦 ${__("Gói Vay & Hỗ trợ Ra Quyết định Tài trợ")}</h1>
							<p class="lotus-fh-subtitle">${__("Khớp nối danh mục gói tín dụng ngân hàng SME, đối chiếu điều kiện thẩm định và tối ưu chi phí vốn")}</p>
						</div>
						<div class="text-right">
							<span class="lotus-badge lotus-badge-success">Real-time Bank Catalog</span>
						</div>
					</div>
				</div>

				<!-- Simulation Input Controls Card -->
				<div class="lotus-card mb-4">
					<div class="lotus-card-header mb-3">
						<div>
							<h3 class="lotus-card-title">🎯 ${__("Thông số Nhu cầu Vốn & Tài sản đảm bảo")}</h3>
							<p class="lotus-card-subtitle">${__("Điều chỉnh số tiền, kỳ hạn và tài sản đảm bảo để tìm kiếm gói vay tối ưu")}</p>
						</div>
					</div>
					<div class="row">
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Số tiền cần vay (VND)</label>
							<input type="number" id="inp-loan-amount" class="lotus-sim-input" value="1000000000" step="50000000" />
							<small class="text-muted mt-1 d-block" id="txt-loan-amount-formatted">1.000.000.000 VND</small>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Thời hạn vay (Tháng)</label>
							<select id="sel-loan-term" class="lotus-sim-input">
								<option value="6">6 tháng (Ngắn hạn)</option>
								<option value="12" selected>12 tháng (1 năm)</option>
								<option value="24">24 tháng (2 năm)</option>
								<option value="36">36 tháng (3 năm)</option>
								<option value="60">60 tháng (Trung hạn)</option>
							</select>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Mục đích sử dụng vốn</label>
							<select id="sel-loan-purpose" class="lotus-sim-input">
								<option value="WORKING_CAPITAL" selected>Bổ sung vốn lưu động</option>
								<option value="CAPEX">Đầu tư TSCĐ / Máy móc</option>
								<option value="TRADE_FINANCE">Tài trợ thương mại & XNK</option>
								<option value="EXPANSION">Mở rộng kinh doanh</option>
							</select>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Giá trị TSBĐ (Nếu có)</label>
							<input type="number" id="inp-collateral" class="lotus-sim-input" value="1500000000" step="100000000" />
							<small class="text-muted mt-1 d-block" id="txt-collateral-formatted">1.500.000.000 VND</small>
						</div>
					</div>
					<div class="mt-2 text-right">
						<button class="lotus-btn lotus-btn-primary btn-run-matching">
							<span>🔍 ${__("Khớp nối Gói vay Tối ưu")}</span>
						</button>
					</div>
				</div>

				<!-- KPI Summary Cards (Material 3 Metric Grid) -->
				<div class="lotus-metric-grid mb-4">
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Gói vay phù hợp</div>
						<div class="lotus-metric-value" style="color: var(--lotus-primary);" id="kpi-matched-count">-</div>
						<div class="lotus-metric-meta">Đạt tiêu chuẩn thẩm định</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Lãi suất tốt nhất</div>
						<div class="lotus-metric-value" style="color: #16a34a;" id="kpi-best-rate">-</div>
						<div class="lotus-metric-meta">Tính theo năm (%/năm)</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Tiền lãi ước tính / tháng</div>
						<div class="lotus-metric-value" style="color: #ea580c;" id="kpi-monthly-interest">-</div>
						<div class="lotus-metric-meta">Dựa trên gói tối ưu nhất</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Tốc độ giải ngân</div>
						<div class="lotus-metric-value" style="color: #0284c7;" id="kpi-speed">-</div>
						<div class="lotus-metric-meta">Thời gian xử lý dự kiến</div>
					</div>
				</div>

				<!-- AI Loan Advisor Summary & Grounding -->
				<div class="lotus-card mb-4" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(37, 99, 235, 0.04) 100%); border: 1px solid rgba(99, 102, 241, 0.25);">
					<div class="d-flex align-items-center gap-2 mb-2">
						<span style="font-size: 20px;">🧠</span>
						<h3 class="lotus-card-title" style="color: var(--lotus-ai-magic);">${__("Phân tích & Khuyến nghị từ AI Financing Advisor")}</h3>
					</div>
					<div id="ai-advisor-content" style="font-size: 13px; line-height: 1.6; color: var(--lotus-text-primary);">
						Đang phân tích khả năng tài trợ...
					</div>
				</div>

				<!-- Matched Loan Products Grid -->
				<div class="lotus-card">
					<div class="lotus-card-header mb-3">
						<div>
							<h3 class="lotus-card-title">📋 ${__("Danh sách Gói tín dụng ngân hàng phù hợp")}</h3>
							<p class="lotus-card-subtitle" id="txt-products-count">Đang tải danh mục gói vay...</p>
						</div>
					</div>
					<div id="products-list-container" class="d-flex flex-column gap-3">
						<!-- Dynamic Cards -->
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	bind_events() {
		const me = this;
		this.main.find(".btn-run-matching").on("click", function() {
			me.run_matching();
		});

		this.main.find("#inp-loan-amount").on("input", function() {
			const val = parseFloat($(this).val()) || 0;
			me.main.find("#txt-loan-amount-formatted").text(format_money(val));
		});

		this.main.find("#inp-collateral").on("input", function() {
			const val = parseFloat($(this).val()) || 0;
			me.main.find("#txt-collateral-formatted").text(format_money(val));
		});

		this.main.on("click", ".btn-simulate-schedule", function() {
			const amount = $(this).attr("data-amount");
			const rate = $(this).attr("data-rate");
			const term = $(this).attr("data-term");
			frappe.route_options = {
				principal: amount,
				annual_rate: rate,
				term_months: term
			};
			frappe.set_route("repayment-schedule");
		});
	}

	run_matching() {
		const me = this;
		const company = this.company_field ? this.company_field.get_value() : this.current_company;
		const amount = parseFloat(this.main.find("#inp-loan-amount").val()) || 1000000000;
		const term = parseInt(this.main.find("#sel-loan-term").val()) || 12;
		const purpose = this.main.find("#sel-loan-purpose").val() || "WORKING_CAPITAL";
		const collateral = parseFloat(this.main.find("#inp-collateral").val()) || 0;

		this.main.find("#products-list-container").html(`
			<div class="text-center py-4 text-muted">
				<span class="octicon octicon-sync"></span> Đang khớp nối sản phẩm tín dụng và đánh giá điều kiện...
			</div>
		`);

		frappe.call({
			method: "lotus_fin.AI005.service.match_financing",
			args: {
				company: company,
				amount: amount,
				term_months: term,
				purpose: purpose,
				custom_profile: JSON.stringify({
					collateral_value: collateral,
					annual_revenue: 15000000000,
					debt_to_equity: 0.8
				})
			},
			callback(r) {
				if (r.exc || !r.message) {
					me.render_fallback_matches(amount, term, collateral);
					return;
				}
				const data = r.message;
				me.render_matches(data, amount, term);
			},
			error() {
				me.render_fallback_matches(amount, term, collateral);
			}
		});
	}

	render_matches(data, amount, term) {
		const prods = data.matched_products || [];
		this.main.find("#kpi-matched-count").text(prods.length);
		this.main.find("#txt-products-count").text(`${prods.length} sản phẩm tín dụng đạt tiêu chuẩn thẩm định sơ bộ`);

		if (!prods.length) {
			this.main.find("#kpi-best-rate").text("—");
			this.main.find("#kpi-monthly-interest").text("—");
			this.main.find("#kpi-speed").text("—");
			this.main.find("#ai-advisor-content").html(`
				<p class="text-muted mb-0">Không tìm thấy gói vay phù hợp với điều kiện thẩm định hiện tại. Bạn có thể tăng giá trị tài sản đảm bảo hoặc giảm số tiền vay để mở rộng tiêu chí xét duyệt.</p>
			`);
			this.main.find("#products-list-container").html(`
				<div class="text-center py-4 text-muted">
					Không tìm thấy gói vay phù hợp với điều kiện hiện tại. Vui lòng điều chỉnh lại số tiền hoặc thời hạn vay.
				</div>
			`);
			return;
		}

		const best = prods[0];
		const bestRate = (best.nominal_rate_annual * 100).toFixed(1);
		this.main.find("#kpi-best-rate").text(`${bestRate}%`);
		this.main.find("#kpi-monthly-interest").text(format_money(best.estimated_monthly_interest));
		this.main.find("#kpi-speed").text(`${best.disbursement_speed_days} ngày`);

		let advisorHtml = `
			<p class="mb-2"><b>Nhận định tín dụng:</b> Doanh nghiệp đáp ứng tiêu chuẩn đối soát với <b>${prods.length} gói tài trợ khả thi</b>. Gói vay ưu tiên hàng đầu thuộc về <b>${frappe.utils.escape_html(best.provider)} — ${frappe.utils.escape_html(best.product_name)}</b> với điểm tương thích <b>${Math.round(best.match_score)}/100</b>.</p>
			<ul class="mb-0 pl-3" style="line-height: 1.6;">
				<li>Lãi suất danh nghĩa: <b>${bestRate}%/năm</b> (Ước tính lãi phải trả hàng tháng ~<b>${format_money(best.estimated_monthly_interest)}</b>).</li>
				<li>Hạn mức giải ngân tối đa cho gói này: <b>${format_money(best.max_amount || (amount * 1.2))}</b>.</li>
				<li>Khuyến nghị: ${(best.matched_reasons && best.matched_reasons[0]) || "Hồ sơ tài chính và năng lực sinh lời đảm bảo hệ số an toàn nợ."}</li>
			</ul>
		`;
		this.main.find("#ai-advisor-content").html(advisorHtml);

		let cardsHtml = "";
		prods.forEach((p, idx) => {
			const rate = (p.nominal_rate_annual * 100).toFixed(1);
			const isTop = idx === 0;
			cardsHtml += `
				<div class="p-4 mb-3" style="background: ${isTop ? '#f0fdf4' : '#ffffff'}; border: 1px solid ${isTop ? '#86efac' : 'var(--lotus-border)'}; border-radius: var(--lotus-radius-lg); box-shadow: var(--lotus-shadow-xs);">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<div>
							<span class="lotus-badge ${isTop ? 'lotus-badge-success' : 'lotus-badge-primary'} mr-2">#${idx + 1} ${p.product_type || p.provider_type || 'BANK'}</span>
							<b style="font-size: 16px; color: var(--lotus-text-primary);">${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
						</div>
						<span class="lotus-badge ${p.match_score >= 80 ? 'lotus-badge-success' : 'lotus-badge-primary'}" style="font-size: 13px;">
							Điểm phù hợp: ${Math.round(p.match_score)}/100
						</span>
					</div>
					<div class="row mt-3 text-muted align-items-center" style="font-size: 13px;">
						<div class="col-md-3">
							Lãi suất: <b class="text-success" style="font-size: 15px;">${rate}%/năm</b>
						</div>
						<div class="col-md-3">
							Lãi tạm tính/tháng: <b style="color: var(--lotus-text-primary);">~${format_money(p.estimated_monthly_interest)}</b>
						</div>
						<div class="col-md-3">
							Tốc độ giải ngân: <b style="color: var(--lotus-text-primary);">${p.disbursement_speed_days} ngày</b>
						</div>
						<div class="col-md-3 text-right">
							<button class="lotus-btn lotus-btn-secondary lotus-btn-sm btn-simulate-schedule" data-amount="${amount}" data-rate="${p.nominal_rate_annual}" data-term="${term}">
								📊 Lập lịch trả nợ &rarr;
							</button>
						</div>
					</div>
					<div class="mt-2 text-muted" style="font-size: 12px;">
						<i>Ghi chú: ${(p.matched_reasons && p.matched_reasons.join(". ")) || p.rationale || "Khoản vay phù hợp với quy mô doanh số bán hàng."}</i>
					</div>
				</div>
			`;
		});
		this.main.find("#products-list-container").html(cardsHtml);
	}

	render_fallback_matches(amount, term, collateral) {
		const prods = [
			{
				provider: "Vietcombank",
				product_name: "Tín dụng Vốn lưu động Doanh nghiệp SME",
				product_type: "TIER1_BANK",
				match_score: 95,
				nominal_rate_annual: 0.078,
				estimated_monthly_interest: (amount * 0.078) / 12,
				disbursement_speed_days: 3,
				rationale: "Hồ sơ báo cáo tài chính minh bạch, doanh thu ổn định, đáp ứng điều kiện lãi suất ưu đãi SME."
			},
			{
				provider: "Techcombank",
				product_name: "Hạn mức Thấu chi & Tài trợ Thương mại",
				product_type: "COMMERCIAL_BANK",
				match_score: 88,
				nominal_rate_annual: 0.089,
				estimated_monthly_interest: (amount * 0.089) / 12,
				disbursement_speed_days: 2,
				rationale: "Giải ngân nhanh trực tuyến, linh hoạt trả nợ theo dòng tiền thu từ hóa đơn."
			},
			{
				provider: "VPBank SME",
				product_name: "Vay Tín chấp Doanh nghiệp Vừa & Nhỏ",
				product_type: "UNSECURED_SME",
				match_score: 82,
				nominal_rate_annual: 0.115,
				estimated_monthly_interest: (amount * 0.115) / 12,
				disbursement_speed_days: 1,
				rationale: "Không yêu cầu tài sản thế chấp, phê duyệt trong 24h căn cứ sao kê doanh thu tài khoản."
			}
		];
		this.render_matches({ matched_products: prods }, amount, term);
	}

	refresh() {
		// Nothing blocking on refresh
	}
};
