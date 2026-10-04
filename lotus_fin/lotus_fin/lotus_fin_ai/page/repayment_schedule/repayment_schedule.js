// Lotus Fin Debt & Repayment Simulation Page Controller (Google Material 3 DNA)
frappe.provide("lotus_fin.repayment_page");

frappe.pages["repayment-schedule"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Debt Repayment Schedule & Rate Shock (AI006)"),
		single_column: true
	});

	wrapper.repayment_page = new lotus_fin.repayment_page.Controller(wrapper);
};

frappe.pages["repayment-schedule"].refresh = function (wrapper) {
	if (wrapper.repayment_page) {
		wrapper.repayment_page.refresh();
	}
};

// Safe pure currency formatter (no HTML tags)
function format_money(val, currency = "VND") {
	if (val === null || val === undefined || isNaN(val)) return "0 " + currency;
	return Math.round(Number(val)).toLocaleString("vi-VN") + " " + currency;
}

lotus_fin.repayment_page.Controller = class Controller {
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
		this.calculate_schedule();
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
				}
			}
		});

		this.current_company = this.company_field.get_value() || frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company");

		this.page.set_secondary_action(__("🤖 Lotus Copilot"), function() {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("🏦 Financing (AI005)"), function() {
			frappe.set_route("financing-copilot");
		});

		this.page.add_inner_button(__("🔮 Stress Studio (AI004)"), function() {
			frappe.set_route("what-if-studio");
		});

		this.page.set_primary_action(__("Calculate Repayment Schedule"), function () {
			me.calculate_schedule();
		}, "octicon octicon-calendar");
	}

	setup_dom() {
		this.main = $(`
			<div class="lotus-financial-health-container" style="max-width: 1200px; margin: 0 auto;">
				<!-- Header Banner Card -->
				<div class="lotus-fh-header-card">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<div class="d-flex align-items-center gap-2 mb-2">
								<span class="lotus-brand-badge">Lotus Fin • Debt Repayment Engine (AI006)</span>
								<span class="lotus-badge lotus-badge-ai">Amortization & Stress Engine</span>
							</div>
							<h1 class="lotus-fh-title">📑 ${__("Debt Repayment Simulation & Interest Rate Shock Testing")}</h1>
							<p class="lotus-fh-subtitle">${__("Simulate amortization schedules (Equal Installment PMT vs. Equal Principal) and test cashflow resilience under interest rate shocks (+bps)")}</p>
						</div>
						<div class="text-right">
							<span class="lotus-badge lotus-badge-success">Multi-Scenario Simulator</span>
						</div>
					</div>
				</div>

				<!-- Loan Simulation Parameters Card -->
				<div class="lotus-card mb-4">
					<div class="lotus-card-header mb-3">
						<div>
							<h3 class="lotus-card-title">🎛️ ${__("Loan Parameters & Interest Rate Shock Settings")}</h3>
							<p class="lotus-card-subtitle">${__("Assess capital cost sensitivity under volatile financial market interest rates")}</p>
						</div>
					</div>
					<div class="row">
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Loan Principal (VND)</label>
							<input type="number" id="inp-principal" class="lotus-sim-input" value="1000000000" step="50000000" />
							<small class="text-muted mt-1 d-block" id="txt-principal-formatted">1.000.000.000 VND</small>
						</div>
						<div class="col-md-2 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Base Interest Rate (%/Yr)</label>
							<input type="number" id="inp-rate" class="lotus-sim-input" value="8.5" step="0.1" />
							<small class="text-muted mt-1 d-block">Initial base rate</small>
						</div>
						<div class="col-md-2 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Tenure (Months)</label>
							<input type="number" id="inp-term" class="lotus-sim-input" value="12" step="1" />
							<small class="text-muted mt-1 d-block">Total installment periods</small>
						</div>
						<div class="col-md-3 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Repayment Method</label>
							<select id="sel-method" class="lotus-sim-input">
								<option value="EQUAL_INSTALLMENT" selected>Equal Installment (PMT: Fixed Principal + Interest)</option>
								<option value="EQUAL_PRINCIPAL">Equal Principal (Declining Balance Interest)</option>
							</select>
						</div>
						<div class="col-md-2 mb-3">
							<label class="text-muted font-weight-bold" style="font-size: 12px; margin-bottom: 6px; display: block;">Interest Rate Shock (+bps)</label>
							<select id="sel-shock-bps" class="lotus-sim-input" style="border-color: #fca5a5;">
								<option value="0" selected>0 bps (Baseline)</option>
								<option value="100">+100 bps (+1.0%)</option>
								<option value="200">+200 bps (+2.0%)</option>
								<option value="300">+300 bps (+3.0%)</option>
							</select>
						</div>
					</div>
					<div class="mt-2 text-right">
						<button class="lotus-btn lotus-btn-primary btn-calc-schedule">
							<span>⚡ ${__("Calculate Schedule & Stress Test")}</span>
						</button>
					</div>
				</div>

				<!-- KPI Summary Cards (Material 3 Metric Grid) -->
				<div class="lotus-metric-grid mb-4">
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Monthly Payment (Period 1)</div>
						<div class="lotus-metric-value" style="color: var(--lotus-primary);" id="kpi-monthly-pmt">-</div>
						<div class="lotus-metric-meta" id="kpi-monthly-sub">Initial Principal + Interest</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Total Interest Payable</div>
						<div class="lotus-metric-value" style="color: #ea580c;" id="kpi-total-interest">-</div>
						<div class="lotus-metric-meta">Over Entire Loan Tenure</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Total Loan Obligation</div>
						<div class="lotus-metric-value" style="color: var(--lotus-text-primary);" id="kpi-total-payment">-</div>
						<div class="lotus-metric-meta">Principal + All Interest</div>
					</div>
					<div class="lotus-metric-card">
						<div class="lotus-metric-label">Rate Shock Impact</div>
						<div class="lotus-metric-value" id="kpi-shock-impact" style="color: #dc2626;">0 VND</div>
						<div class="lotus-metric-meta" id="kpi-shock-sub">Additional Interest Cost</div>
					</div>
				</div>

				<!-- AI Repayment Advisor Insights -->
				<div class="lotus-card mb-4" style="background: linear-gradient(135deg, rgba(22, 163, 74, 0.04) 0%, rgba(37, 99, 235, 0.04) 100%); border: 1px solid rgba(22, 163, 74, 0.25);">
					<div class="d-flex align-items-center gap-2 mb-2">
						<span style="font-size: 20px;">💡</span>
						<h3 class="lotus-card-title" style="color: #166534;">${__("AI Debt Advisory & Cashflow Structuring Insights")}</h3>
					</div>
					<div id="ai-repayment-advisor" style="font-size: 13px; line-height: 1.6; color: var(--lotus-text-primary);">
						Analyzing repayment structure and solvency...
					</div>
				</div>

				<!-- Detailed Amortization Table Card -->
				<div class="lotus-card">
					<div class="lotus-card-header mb-3">
						<div>
							<h3 class="lotus-card-title">📅 ${__("Period-by-Period Amortization Schedule")}</h3>
							<p class="lotus-card-subtitle" id="txt-periods-count">12 payment periods</p>
						</div>
					</div>
					<div class="lotus-table-container">
						<table class="lotus-table">
							<thead>
								<tr>
									<th style="width: 80px; text-align: center;">Period #</th>
									<th style="text-align: right;">Beginning Balance</th>
									<th style="text-align: right;">Principal</th>
									<th style="text-align: right;">Interest</th>
									<th style="text-align: right;">Total Payment</th>
									<th style="text-align: right;">Ending Balance</th>
								</tr>
							</thead>
							<tbody id="schedule-tbody">
								<!-- Dynamic rows -->
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	bind_events() {
		const me = this;
		this.main.find(".btn-calc-schedule").on("click", function() {
			me.calculate_schedule();
		});

		this.main.find("#inp-principal").on("input", function() {
			const val = parseFloat($(this).val()) || 0;
			me.main.find("#txt-principal-formatted").text(format_money(val));
		});

		if (frappe.route_options) {
			if (frappe.route_options.principal) {
				this.main.find("#inp-principal").val(frappe.route_options.principal);
				this.main.find("#txt-principal-formatted").text(format_money(parseFloat(frappe.route_options.principal)));
			}
			if (frappe.route_options.annual_rate) {
				this.main.find("#inp-rate").val((parseFloat(frappe.route_options.annual_rate) * 100).toFixed(1));
			}
			if (frappe.route_options.term_months) {
				this.main.find("#inp-term").val(frappe.route_options.term_months);
			}
			frappe.route_options = null;
			this.calculate_schedule();
		}
	}

	calculate_schedule() {
		const principal = parseFloat(this.main.find("#inp-principal").val()) || 1000000000;
		const baseRatePct = parseFloat(this.main.find("#inp-rate").val()) || 8.5;
		const term = parseInt(this.main.find("#inp-term").val()) || 12;
		const method = this.main.find("#sel-method").val() || "EQUAL_INSTALLMENT";
		const shockBps = parseInt(this.main.find("#sel-shock-bps").val()) || 0;

		const baseAnnualRate = baseRatePct / 100.0;
		const stressedAnnualRate = (baseRatePct + (shockBps / 100.0)) / 100.0;
		const monthlyRate = stressedAnnualRate / 12.0;

		let balance = principal;
		let totalInterest = 0;
		let rows = [];

		if (method === "EQUAL_INSTALLMENT") {
			let pmt = 0;
			if (monthlyRate > 0) {
				pmt = principal * (monthlyRate * Math.pow(1 + monthlyRate, term)) / (Math.pow(1 + monthlyRate, term) - 1);
			} else {
				pmt = principal / term;
			}

			for (let i = 1; i <= term; i++) {
				const startBal = balance;
				const interest = startBal * monthlyRate;
				let principalPaid = pmt - interest;
				if (i === term || principalPaid > startBal) {
					principalPaid = startBal;
					pmt = principalPaid + interest;
				}
				const endBal = Math.max(0, startBal - principalPaid);
				balance = endBal;
				totalInterest += interest;

				rows.push({
					period: i,
					startBal: startBal,
					principalPaid: principalPaid,
					interest: interest,
					totalPayment: pmt,
					endBal: endBal
				});
			}
		} else {
			const fixedPrincipal = principal / term;
			for (let i = 1; i <= term; i++) {
				const startBal = balance;
				const interest = startBal * monthlyRate;
				const principalPaid = (i === term) ? startBal : fixedPrincipal;
				const totalPayment = principalPaid + interest;
				const endBal = Math.max(0, startBal - principalPaid);
				balance = endBal;
				totalInterest += interest;

				rows.push({
					period: i,
					startBal: startBal,
					principalPaid: principalPaid,
					interest: interest,
					totalPayment: totalPayment,
					endBal: endBal
				});
			}
		}

		let baseInterest = totalInterest;
		if (shockBps > 0) {
			const bMonthlyRate = baseAnnualRate / 12.0;
			if (method === "EQUAL_INSTALLMENT") {
				const bPmt = principal * (bMonthlyRate * Math.pow(1 + bMonthlyRate, term)) / (Math.pow(1 + bMonthlyRate, term) - 1);
				baseInterest = (bPmt * term) - principal;
			} else {
				baseInterest = 0;
				let bBal = principal;
				const bFixed = principal / term;
				for (let i = 1; i <= term; i++) {
					baseInterest += bBal * bMonthlyRate;
					bBal -= bFixed;
				}
			}
		}
		const shockAddedCost = Math.max(0, totalInterest - baseInterest);

		const firstPmt = rows.length ? rows[0].totalPayment : 0;
		this.main.find("#kpi-monthly-pmt").text(format_money(firstPmt));
		this.main.find("#kpi-total-interest").text(format_money(totalInterest));
		this.main.find("#kpi-total-payment").text(format_money(principal + totalInterest));
		
		if (shockBps > 0) {
			this.main.find("#kpi-shock-impact").text(`+${format_money(shockAddedCost)}`).css("color", "#dc2626");
			this.main.find("#kpi-shock-sub").text(`Under +${shockBps} bps rate shock (${(stressedAnnualRate * 100).toFixed(1)}%)`);
		} else {
			this.main.find("#kpi-shock-impact").text("0 VND").css("color", "#16a34a");
			this.main.find("#kpi-shock-sub").text("No rate shock applied");
		}

		this.main.find("#txt-periods-count").text(`${term} Payment Periods (${method === 'EQUAL_INSTALLMENT' ? 'Equal Installment (PMT)' : 'Equal Principal'})`);

		let advisorHtml = `
			<p class="mb-2"><b>Cashflow Structuring Insight:</b> For a loan principal of <b>${format_money(principal)}</b> with tenure of <b>${term} months</b>:</p>
			<ul class="mb-0 pl-3" style="line-height: 1.6;">
				<li>Payment method <b>${method === 'EQUAL_INSTALLMENT' ? 'Equal Installments (PMT)' : 'Equal Principal Monthly'}</b> allows the business to ${method === 'EQUAL_INSTALLMENT' ? 'fix monthly obligations (' + format_money(firstPmt) + ')' : 'accelerate principal reduction and reduce total interest costs over time'}.</li>
				${shockBps > 0 ? `<li class="text-danger font-weight-bold">CRITICAL RATE SHOCK ALERT (+${shockBps} bps): Additional interest cost of ${format_money(shockAddedCost)} across the loan term. Ensure operating margins can absorb increased financing costs.</li>` : '<li>Nominal rate remains within safe parameters. Maintain a cash reserve buffer of 1-2 installment periods to safeguard against AR collection delays.</li>'}
			</ul>
		`;
		this.main.find("#ai-repayment-advisor").html(advisorHtml);

		let tbodyHtml = "";
		rows.forEach(r => {
			tbodyHtml += `
				<tr>
					<td style="text-align: center; font-weight: 700; color: var(--lotus-text-primary);">${r.period}</td>
					<td style="text-align: right; color: var(--lotus-text-secondary);">${format_money(r.startBal)}</td>
					<td style="text-align: right; font-weight: 600; color: var(--lotus-primary);">${format_money(r.principalPaid)}</td>
					<td style="text-align: right; color: #ea580c;">${format_money(r.interest)}</td>
					<td style="text-align: right; font-weight: 700; color: var(--lotus-text-primary);">${format_money(r.totalPayment)}</td>
					<td style="text-align: right; color: var(--lotus-text-muted);">${format_money(r.endBal)}</td>
				</tr>
			`;
		});
		this.main.find("#schedule-tbody").html(tbodyHtml);
	}

	refresh() {
		// Nothing blocking on refresh
	}
};
