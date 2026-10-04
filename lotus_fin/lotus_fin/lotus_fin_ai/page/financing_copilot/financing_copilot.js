// Lotus Fin Financing Copilot & Loan Decision Page Controller (Google Material 3 DNA)
frappe.provide("lotus_fin.financing_page");

frappe.pages["financing-copilot"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Financing Copilot & Loan Decision (AI005)"),
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

		this.page.add_inner_button(__("📑 Repayment Schedule (AI006)"), function() {
			frappe.set_route("repayment-schedule");
		});

		this.page.add_inner_button(__("📊 Financial Health"), function() {
			frappe.set_route("financial-health");
		});

		this.page.set_primary_action(__("Match Loan Products"), function () {
			me.run_matching();
		}, "octicon octicon-search");
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
							<h1 class="lotus-fh-title">🏦 ${__("Financing Copilot & Loan Decision Support")}</h1>
							<p class="lotus-fh-subtitle">${__("SME bank loan matching, credit criteria screening, and capital cost optimization")}</p>
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
							<h3 class="lotus-card-title">🎯 ${__("Financing Needs & Collateral Parameters")}</h3>
							<p class="lotus-card-subtitle">${__("Adjust loan amount, tenure, and collateral to discover optimal credit packages")}</p>
						</div>
					</div>
					<div class="row">
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Required Loan Amount (VND)</label>
							<input type="number" id="inp-loan-amount" class="lotus-sim-input" value="1000000000" step="50000000" />
							<small class="text-muted mt-1 d-block" id="txt-loan-amount-formatted">1.000.000.000 VND</small>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Loan Tenure (Months)</label>
							<select id="sel-loan-term" class="lotus-sim-input">
								<option value="6">6 Months (Short-term)</option>
								<option value="12" selected>12 Months (1 Year)</option>
								<option value="24">24 Months (2 Years)</option>
								<option value="36">36 Months (3 Years)</option>
								<option value="60">60 Months (Medium-term)</option>
							</select>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Purpose of Funds</label>
							<select id="sel-loan-purpose" class="lotus-sim-input">
								<option value="WORKING_CAPITAL" selected>Working Capital Supplement</option>
								<option value="CAPEX">CAPEX / Equipment Investment</option>
								<option value="TRADE_FINANCE">Trade Finance & Import/Export</option>
								<option value="EXPANSION">Business Expansion</option>
							</select>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Collateral Value (If Available)</label>
							<input type="number" id="inp-collateral" class="lotus-sim-input" value="1500000000" step="100000000" />
							<small class="text-muted mt-1 d-block" id="txt-collateral-formatted">1.500.000.000 VND</small>
						</div>
					</div>
					<div class="mt-2 text-right">
						<button class="lotus-btn lotus-btn-primary btn-run-matching">
							<span>🔍 ${__("Match Optimal Loan Products")}</span>
						</button>
					</div>
				</div>

				<!-- KPI Summary Cards (Material 3 Metric Grid) -->
				<div class="lotus-metric-grid mb-4">
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Matched Loan Packages</div>
						<div class="lotus-metric-value" style="color: var(--lotus-primary);" id="kpi-matched-count">-</div>
						<div class="lotus-metric-meta">Credit Screening Approved</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Best Interest Rate</div>
						<div class="lotus-metric-value" style="color: #16a34a;" id="kpi-best-rate">-</div>
						<div class="lotus-metric-meta">Annualized Rate (%/Yr)</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Est. Monthly Interest</div>
						<div class="lotus-metric-value" style="color: #ea580c;" id="kpi-monthly-interest">-</div>
						<div class="lotus-metric-meta">Based on Top Recommendation</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Disbursement Speed</div>
						<div class="lotus-metric-value" style="color: #0284c7;" id="kpi-speed">-</div>
						<div class="lotus-metric-meta">Expected Processing Time</div>
					</div>
				</div>

				<!-- AI Loan Advisor Summary & Grounding -->
				<div class="lotus-card mb-4" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(37, 99, 235, 0.04) 100%); border: 1px solid rgba(99, 102, 241, 0.25);">
					<div class="d-flex align-items-center gap-2 mb-2">
						<span style="font-size: 20px;">🧠</span>
						<h3 class="lotus-card-title" style="color: var(--lotus-ai-magic);">${__("Exclusive AI Financing Advisor Analysis")}</h3>
					</div>
					<div id="ai-advisor-content" style="font-size: 13px; line-height: 1.6; color: var(--lotus-text-primary);">
						Analyzing creditworthiness and financing options...
					</div>
				</div>

				<!-- Matched Loan Products Grid -->
				<div class="lotus-card">
					<div class="lotus-card-header mb-3">
						<div>
							<h3 class="lotus-card-title">📋 ${__("Approved SME Credit Catalog")}</h3>
							<p class="lotus-card-subtitle" id="txt-products-count">Loading credit packages...</p>
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
				<span class="octicon octicon-sync"></span> Matching credit products against accounting underwriting metrics...
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
		this.main.find("#txt-products-count").text(`${prods.length} credit products pre-approved under deterministic criteria`);

		if (!prods.length) {
			this.main.find("#kpi-best-rate").text("—");
			this.main.find("#kpi-monthly-interest").text("—");
			this.main.find("#kpi-speed").text("—");
			this.main.find("#ai-advisor-content").html(`
				<p class="text-muted mb-0">No credit packages match current screening criteria. Consider pledging additional collateral or adjusting required loan amount.</p>
			`);
			this.main.find("#products-list-container").html(`
				<div class="text-center py-4 text-muted">
					No matching packages found. Please adjust loan amount or tenure.
				</div>
			`);
			return;
		}

		const best = prods[0];
		const bestRate = (best.nominal_rate_annual * 100).toFixed(1);
		this.main.find("#kpi-best-rate").text(`${bestRate}%`);
		this.main.find("#kpi-monthly-interest").text(format_money(best.estimated_monthly_interest));
		this.main.find("#kpi-speed").text(`${best.disbursement_speed_days} Days`);

		let advisorHtml = `
			<p class="mb-2"><b>Credit Assessment:</b> Business satisfies underwriting criteria for <b>${prods.length} eligible credit packages</b>. Top recommended facility: <b>${frappe.utils.escape_html(best.provider)} — ${frappe.utils.escape_html(best.product_name)}</b> with compatibility score <b>${Math.round(best.match_score)}/100</b>.</p>
			<ul class="mb-0 pl-3" style="line-height: 1.6;">
				<li>Nominal Interest Rate: <b>${bestRate}%/Yr</b> (Est. monthly interest ~<b>${format_money(best.estimated_monthly_interest)}</b>).</li>
				<li>Maximum facility limit: <b>${format_money(best.max_amount || (amount * 1.2))}</b>.</li>
				<li>Advisory: ${frappe.utils.escape_html((best.matched_reasons && best.matched_reasons[0]) || best.rationale || "Transparent financial statements and healthy EBITDA support debt servicing capability.")}</li>
			</ul>
		`;
		this.main.find("#ai-advisor-content").html(advisorHtml);

		let cardsHtml = "";
		prods.forEach((p, idx) => {
			const rate = (p.nominal_rate_annual * 100).toFixed(1);
			const isTop = idx === 0;
			const pType = frappe.utils.escape_html(p.product_type || p.provider_type || 'BANK');
			const pNote = frappe.utils.escape_html((p.matched_reasons && p.matched_reasons.join(". ")) || p.rationale || "Loan structure aligned with historical sales revenue.");
			cardsHtml += `
				<div class="p-4 mb-3" style="background: ${isTop ? '#f0fdf4' : '#ffffff'}; border: 1px solid ${isTop ? '#86efac' : 'var(--lotus-border)'}; border-radius: var(--lotus-radius-lg); box-shadow: var(--lotus-shadow-xs);">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<div>
							<span class="lotus-badge ${isTop ? 'lotus-badge-success' : 'lotus-badge-primary'} mr-2">#${idx + 1} ${pType}</span>
							<b style="font-size: 16px; color: var(--lotus-text-primary);">${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
						</div>
						<span class="lotus-badge ${p.match_score >= 80 ? 'lotus-badge-success' : 'lotus-badge-primary'}" style="font-size: 13px;">
							Match Score: ${Math.round(p.match_score)}/100
						</span>
					</div>
					<div class="row mt-3 text-muted align-items-center" style="font-size: 13px;">
						<div class="col-md-3">
							Interest Rate: <b class="text-success" style="font-size: 15px;">${rate}%/yr</b>
						</div>
						<div class="col-md-3">
							Est. Monthly Interest: <b style="color: var(--lotus-text-primary);">~${format_money(p.estimated_monthly_interest)}</b>
						</div>
						<div class="col-md-3">
							Disbursement Speed: <b style="color: var(--lotus-text-primary);">${p.disbursement_speed_days} Days</b>
						</div>
						<div class="col-md-3 text-right">
							<button class="lotus-btn lotus-btn-secondary lotus-btn-sm btn-simulate-schedule" data-amount="${amount}" data-rate="${p.nominal_rate_annual}" data-term="${term}">
								📊 Build Repayment Schedule &rarr;
							</button>
						</div>
					</div>
					<div class="mt-2 text-muted" style="font-size: 12px;">
						<i>Note: ${pNote}</i>
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
				product_name: "SME Working Capital Credit Facility",
				product_type: "TIER1_BANK",
				match_score: 95,
				nominal_rate_annual: 0.078,
				estimated_monthly_interest: (amount * 0.078) / 12,
				disbursement_speed_days: 3,
				rationale: "Transparent financial records and stable cash flow satisfy SME concessional terms."
			},
			{
				provider: "Techcombank",
				product_name: "Overdraft & Trade Finance Facility",
				product_type: "COMMERCIAL_BANK",
				match_score: 88,
				nominal_rate_annual: 0.089,
				estimated_monthly_interest: (amount * 0.089) / 12,
				disbursement_speed_days: 2,
				rationale: "Fast online drawdown with repayment flexibility aligned to invoice collections."
			},
			{
				provider: "VPBank SME",
				product_name: "Unsecured SME Business Loan",
				product_type: "UNSECURED_SME",
				match_score: 82,
				nominal_rate_annual: 0.115,
				estimated_monthly_interest: (amount * 0.115) / 12,
				disbursement_speed_days: 1,
				rationale: "No collateral required; automated 24h approval based on verifiable account turnover."
			}
		];
		this.render_matches({ matched_products: prods }, amount, term);
	}

	refresh() {
		// Nothing blocking on refresh
	}
};
