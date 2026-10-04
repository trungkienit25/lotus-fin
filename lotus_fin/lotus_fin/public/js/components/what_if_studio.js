// Lotus Fin — Reusable What-If Stress-Testing Studio Component
frappe.provide("lotus_fin.components");

lotus_fin.components.WhatIfStudio = class WhatIfStudio {
	constructor(opts) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company"));
		this.title = opts.title || __("What-If Scenario Simulation & Cash Stress-Testing Studio");
		this.badge = opts.badge || __("9-KPI Deterministic Simulation • Multi-Variable Stress Engine");
		this.on_run_complete = opts.on_run_complete || null;
		this.render();
		this.bind_events();
	}

	render() {
		this.$el = $(`
			<div class="lotus-section-card lotus-what-if-card" style="padding: 18px 20px;">
				<div class="d-flex justify-content-between align-items-center mb-2">
					<div class="lotus-section-title mb-0">
						<span style="font-size: 16px;">🔮 <b>${this.title}</b></span>
						<span class="lotus-ai-badge" style="background: #ede9fe; color: #6d28d9;">${this.badge}</span>
					</div>
					<div class="d-flex gap-1">
						<button class="lotus-btn-secondary btn-reset-sim-defaults" style="font-size: 11px; padding: 4px 12px;" title="${__("Reset to default scenario")}">
							↺ ${__("Defaults")}
						</button>
					</div>
				</div>
				<p class="text-muted" style="font-size: 12px; margin-bottom: 14px;">
					${__("Multi-variable quantitative stress-testing simulation. Evaluate the simultaneous impact of sales shocks, AR/AP payment delays, fixed OPEX changes, and capital financing injections across 9 mission-critical business KPIs.")}
				</p>

				<!-- Preconfigured stress test presets -->
				<div class="mb-3">
					<span class="text-muted" style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">🎯 ${__("Preconfigured Stress Presets:")}</span>
					<div class="lotus-preset-scenarios mt-1">
						<button class="lotus-preset-btn" data-preset="sales_slump">
							📉 <b>${__("Demand Shock (Sales Slump -30%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="credit_crunch">
							⏱️ <b>${__("Delayed Collections (AR Delay +30 Days)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="cost_inflation">
							📈 <b>${__("Cost Inflation (OPEX +20%, Payroll +10%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="black_swan">
							⚡ <b>${__("Compound Crisis (Sales -25%, AR +20D, OPEX +15%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="growth_injection">
							🚀 <b>${__("Growth Expansion (Sales +30%, Debt 500M)")}</b>
						</button>
					</div>
				</div>

				<!-- Parameter group 1: Revenue & Working Capital -->
				<div class="lotus-sim-group-title">
					<span>📊 Group 1: Revenue & Working Capital Cycles (AR / AP)</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Net Revenue Shock")}</span>
							<span class="lotus-sim-val-badge negative" id="val-sim-sales">-15%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-sales" min="-50" max="50" step="5" value="-15">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-50% (Deep Slump)</span>
							<span>0% (Baseline)</span>
							<span>+50% (High Growth)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Directly impacts cash inflow and gross profit margin.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Customer Payment Delay (DSO Shift)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-delay">+15 Days</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-delay" min="0" max="60" step="5" value="15">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>0 Days (On-Time)</span>
							<span>+30 Days</span>
							<span>+60 Days (Delinquent)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Increases uncollected AR and lengthens Cash Conversion Cycle.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Supplier Payment Extension (DPO Shift)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-supplier">0 Days</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-supplier" min="-30" max="60" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30 Days (Tightened Terms)</span>
							<span>0 Days</span>
							<span>+60 Days (Capital Preserved)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Postpones AP disbursements to conserve cash buffer.")}</div>
					</div>
				</div>

				<!-- Parameter group 2: OPEX & Shocks -->
				<div class="lotus-sim-group-title">
					<span>🏢 Group 2: Operating Expenses (OPEX), Payroll & One-Off Shocks</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Operating Expense Shock (OPEX)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-opex">0%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-opex" min="-30" max="50" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30% (Austerity)</span>
							<span>0%</span>
							<span>+50% (Overrun)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Leasing, marketing, logistics, utilities, admin overhead...")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Payroll & Staffing Shock (Payroll)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-payroll">0%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-payroll" min="-30" max="40" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30% (Downsizing)</span>
							<span>0%</span>
							<span>+40% (Aggressive Hiring)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Base salaries, social insurance, and company-wide compensation.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("One-Off Shock Expense")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-one-off">0 VND</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-one-off">
							<option value="0" selected>${__("None (0 VND)")}</option>
							<option value="50000000">50,000,000 VND (Equipment Repair / Overhaul)</option>
							<option value="100000000">100,000,000 VND (Tax Arrears / Regulatory Penalty)</option>
							<option value="200000000">200,000,000 VND (New Branch Lease Deposit)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Lump-sum cash outflow creating immediate liquidity pressure.")}</div>
					</div>
				</div>

				<!-- Parameter group 3: Financing & Interest -->
				<div class="lotus-sim-group-title">
					<span>💰 Group 3: Debt Financing & Capital Injection (AI-F005)</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Debt Financing Facility")}</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-financing">
							<option value="0">${__("No External Debt (Self-Funded)")}</option>
							<option value="200000000">200,000,000 VND (Overdraft / Working Capital Line)</option>
							<option value="300000000" selected>300,000,000 VND (Short-Term Working Capital Loan)</option>
							<option value="500000000">500,000,000 VND (Medium-Term Expansion Loan)</option>
							<option value="1000000000">1,000,000,000 VND (Syndicated Bank Facility)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Disbursed proceeds are directly injected into net cash flow.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Loan Tenure (Months)")}</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-fin-term">
							<option value="6">6 Months (Short-term Working Capital)</option>
							<option value="12" selected>12 Months (Standard 1-Year Facility)</option>
							<option value="24">24 Months (Medium-term Facility)</option>
							<option value="36">36 Months (Long-term CAPEX Facility)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Determines repayment amortization pace and monthly interest.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Annual Nominal Interest Rate (%/Year)")}</span>
							<span class="lotus-sim-val-badge positive" id="val-sim-rate">9.5%/yr</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-rate" min="5" max="18" step="0.5" value="9.5">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>5.0% (Concessional)</span>
							<span>9.5% (Market Rate)</span>
							<span>18.0% (Unsecured/High Risk)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Interest expenses are deducted from net operational cash flow.")}</div>
					</div>
				</div>

				<div class="mb-3 d-flex gap-2">
					<button class="lotus-sim-btn btn-run-simulation" style="padding: 10px 24px; font-size: 14px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); box-shadow: 0 2px 6px rgba(13, 148, 136, 0.3);">
						🚀 ${__("Run Stress-Test Simulation (9-KPI Engine)")}
					</button>
				</div>
				<div class="lotus-simulation-result-container">
					<!-- Simulation table & waterfall rendered here -->
				</div>
			</div>
		`);

		this.parent.append(this.$el);
		this.$result = this.$el.find(".lotus-simulation-result-container");
	}

	bind_events() {
		const me = this;

		this.$el.on("input", "#input-sim-sales", function () {
			const val = $(this).val();
			const badge = me.$el.find("#val-sim-sales");
			badge.text((val > 0 ? "+" : "") + val + "%");
			badge.removeClass("negative positive").addClass(val < 0 ? "negative" : (val > 0 ? "positive" : ""));
		});

		this.$el.on("input", "#input-sim-delay", function () {
			me.$el.find("#val-sim-delay").text("+" + $(this).val() + " Days");
		});

		this.$el.on("input", "#input-sim-supplier", function () {
			const val = $(this).val();
			me.$el.find("#val-sim-supplier").text((val > 0 ? "+" : "") + val + " Days");
		});

		this.$el.on("input", "#input-sim-opex", function () {
			const val = $(this).val();
			const badge = me.$el.find("#val-sim-opex");
			badge.text((val > 0 ? "+" : "") + val + "%");
			badge.removeClass("negative positive").addClass(val > 0 ? "negative" : (val < 0 ? "positive" : ""));
		});

		this.$el.on("input", "#input-sim-payroll", function () {
			const val = $(this).val();
			const badge = me.$el.find("#val-sim-payroll");
			badge.text((val > 0 ? "+" : "") + val + "%");
			badge.removeClass("negative positive").addClass(val > 0 ? "negative" : (val < 0 ? "positive" : ""));
		});

		this.$el.on("change", "#input-sim-one-off", function () {
			const val = parseFloat($(this).val()) || 0;
			const badge = me.$el.find("#val-sim-one-off");
			badge.text(lotus_fin.core.format_currency(val, "VND"));
			badge.removeClass("negative").addClass(val > 0 ? "negative" : "");
		});

		this.$el.on("input", "#input-sim-rate", function () {
			me.$el.find("#val-sim-rate").text($(this).val() + "%/yr");
		});

		this.$el.on("click", ".lotus-preset-btn", function () {
			const preset = $(this).attr("data-preset");
			me.$el.find(".lotus-preset-btn").removeClass("active");
			$(this).addClass("active");
			me.apply_stress_preset(preset);
		});

		this.$el.on("click", ".btn-reset-sim-defaults", function () {
			me.$el.find(".lotus-preset-btn").removeClass("active");
			me.reset_sim_controls();
		});

		this.$el.on("click", ".btn-run-simulation", function () {
			me.run_simulation();
		});
	}

	apply_stress_preset(presetKey) {
		const presets = {
			sales_slump: { sales: -30, delay: 10, supplier: 0, opex: -5, payroll: 0, one_off: 0, fin: 0, fin_term: 12, rate: 9.5 },
			credit_crunch: { sales: -10, delay: 30, supplier: 10, opex: 0, payroll: 0, one_off: 0, fin: 0, fin_term: 12, rate: 9.5 },
			cost_inflation: { sales: 0, delay: 5, supplier: -10, opex: 20, payroll: 10, one_off: 50000000, fin: 0, fin_term: 12, rate: 10.0 },
			black_swan: { sales: -25, delay: 20, supplier: -15, opex: 15, payroll: 0, one_off: 100000000, fin: 300000000, fin_term: 12, rate: 9.5 },
			growth_injection: { sales: 30, delay: 10, supplier: 15, opex: 15, payroll: 20, one_off: 100000000, fin: 500000000, fin_term: 24, rate: 9.0 }
		};

		const p = presets[presetKey];
		if (!p) return;

		this.$el.find("#input-sim-sales").val(p.sales).trigger("input");
		this.$el.find("#input-sim-delay").val(p.delay).trigger("input");
		this.$el.find("#input-sim-supplier").val(p.supplier).trigger("input");
		this.$el.find("#input-sim-opex").val(p.opex).trigger("input");
		this.$el.find("#input-sim-payroll").val(p.payroll).trigger("input");
		this.$el.find("#input-sim-one-off").val(p.one_off).trigger("change");
		this.$el.find("#input-sim-financing").val(p.fin);
		this.$el.find("#input-sim-fin-term").val(p.fin_term);
		this.$el.find("#input-sim-rate").val(p.rate).trigger("input");

		this.run_simulation();
	}

	reset_sim_controls() {
		this.$el.find("#input-sim-sales").val(-15).trigger("input");
		this.$el.find("#input-sim-delay").val(15).trigger("input");
		this.$el.find("#input-sim-supplier").val(0).trigger("input");
		this.$el.find("#input-sim-opex").val(0).trigger("input");
		this.$el.find("#input-sim-payroll").val(0).trigger("input");
		this.$el.find("#input-sim-one-off").val(0).trigger("change");
		this.$el.find("#input-sim-financing").val(300000000);
		this.$el.find("#input-sim-fin-term").val(12);
		this.$el.find("#input-sim-rate").val(9.5).trigger("input");

		this.run_simulation();
	}

	run_simulation() {
		const me = this;
		const company = this.get_company();
		const salesPct = (parseFloat(this.$el.find("#input-sim-sales").val()) || 0) / 100.0;
		const delayDays = parseInt(this.$el.find("#input-sim-delay").val()) || 0;
		const supplierDays = parseInt(this.$el.find("#input-sim-supplier").val()) || 0;
		const opexPct = (parseFloat(this.$el.find("#input-sim-opex").val()) || 0) / 100.0;
		const payrollPct = (parseFloat(this.$el.find("#input-sim-payroll").val()) || 0) / 100.0;
		const oneOffExpense = parseFloat(this.$el.find("#input-sim-one-off").val()) || 0;
		const finAmount = parseFloat(this.$el.find("#input-sim-financing").val()) || 0;
		const finTerm = parseInt(this.$el.find("#input-sim-fin-term").val()) || 12;
		const finRate = (parseFloat(this.$el.find("#input-sim-rate").val()) || 9.5) / 100.0;

		this.$result.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("Running 9-layer financial stress-testing model...")}</div>`);

		frappe.call({
			method: "lotus_fin.AI005.service.simulate_what_if",
			args: {
				company: company,
				sales_change_pct: salesPct,
				collection_delay_days: delayDays,
				supplier_due_shift_days: supplierDays,
				payroll_change_pct: payrollPct,
				opex_change_pct: opexPct,
				one_off_expense: oneOffExpense,
				financing_amount: finAmount,
				financing_term_months: finAmount > 0 ? finTerm : 0,
				financing_rate_annual: finAmount > 0 ? finRate : 0.0
			},
			callback(r) {
				if (r.exc || !r.message) {
					me.$result.html(`<div class="lotus-banner lotus-banner-danger">${__("Failed to run scenario simulation. Please check input parameters.")}</div>`);
					return;
				}
				me.render_simulation_result(r.message);
				if (me.on_run_complete) {
					me.on_run_complete(r.message);
				}
			}
		});
	}

	render_simulation_result(res) {
		const container = this.$result.empty();
		const kpis = res.kpis_9_layer || {};

		const rev = kpis["revenue"] || {};
		const ncf = kpis["net_cash_flow"] || {};
		const endingCash = kpis["ending_cash"] || {};
		const ccc = kpis["ccc"] || {};

		const endingCashStatus = endingCash.simulation !== null && endingCash.simulation < 0 ? "status-danger" : (endingCash.simulation < 50000000 ? "status-warning" : "status-healthy");
		const ncfStatus = ncf.simulation !== null && ncf.simulation < 0 ? "status-danger" : "status-healthy";

		const impactCardsHtml = `
			<div class="lotus-impact-cards-grid mt-3">
				<div class="lotus-impact-card ${endingCashStatus}">
					<div class="lotus-impact-card-title">💵 ${__("Ending Cash Balance")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(endingCash.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${endingCash.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${endingCash.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(endingCash.absolute_change, { is_currency: true })}</span>
						<span class="text-muted">(${endingCash.relative_change !== null ? (endingCash.relative_change * 100).toFixed(1) + '%' : '—'})</span>
					</div>
				</div>

				<div class="lotus-impact-card ${ncfStatus}">
					<div class="lotus-impact-card-title">🌊 ${__("Net Cash Flow")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(ncf.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${ncf.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${ncf.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(ncf.absolute_change, { is_currency: true })}</span>
					</div>
				</div>

				<div class="lotus-impact-card status-healthy">
					<div class="lotus-impact-card-title">📈 ${__("Post-Shock Net Revenue")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(rev.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${rev.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${rev.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(rev.absolute_change, { is_currency: true })}</span>
					</div>
				</div>

				<div class="lotus-impact-card ${ccc.simulation > 90 ? 'status-warning' : 'status-healthy'}">
					<div class="lotus-impact-card-title">⏳ ${__("Cash Conversion Cycle (CCC)")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(ccc.simulation, { is_days: true })}</div>
					<div class="lotus-impact-card-delta ${ccc.absolute_change > 0 ? 'delta-down' : 'delta-up'}">
						<span>${ccc.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(ccc.absolute_change, { is_days: true })}</span>
					</div>
				</div>
			</div>
		`;

		const kpiList = [
			{ id: "revenue", label: __("1. Net Revenue (Revenue)"), desc: __("Sales volume after simulated shock"), is_currency: true },
			{ id: "gross_profit", label: __("2. Gross Profit"), desc: __("Gross profit contribution to fixed overhead"), is_currency: true },
			{ id: "gross_margin", label: __("3. Gross Margin (%)"), desc: __("Direct product profitability margin"), is_ratio: true },
			{ id: "ar_outstanding", label: __("4. Accounts Receivable (AR)"), desc: __("Working capital locked in uncollected receivables"), is_currency: true },
			{ id: "dso", label: __("5. Days Sales Outstanding (DSO)"), desc: __("Average customer collection latency"), is_days: true },
			{ id: "net_cash_flow", label: __("6. Net Cash Flow"), desc: __("Cash inflows minus all cash operating outflows and debt service"), is_currency: true },
			{ id: "ending_cash", label: __("7. Ending Cash Balance"), desc: __("Total available liquidity buffer across accounts"), is_currency: true },
			{ id: "ccc", label: __("8. Cash Conversion Cycle (CCC)"), desc: __("Days from cash outflow for inventory to cash receipt"), is_days: true },
			{ id: "cash_shortfall", label: __("9. Liquidity Shortfall Deficit"), desc: __("Deficit amount relative to 50M VND safety reserve buffer"), is_currency: true }
		];

		let rowsHtml = "";
		kpiList.forEach(k => {
			const item = kpis[k.id];
			if (!item) return;

			let baseStr = this.format_sim_val(item.baseline, k);
			let simStr = this.format_sim_val(item.simulation, k);
			let absVal = item.absolute_change;
			let absSign = absVal > 0 ? "+" : "";
			let absStr = absVal !== null ? `${absSign}${this.format_sim_val(absVal, k)}` : "—";
			let relStr = item.relative_change !== null ? `${(item.relative_change * 100).toFixed(1)}%` : "—";
			let statusBadge = `<span class="badge ${item.status === 'HEALTHY' ? 'badge-success' : (item.status === 'WARNING' ? 'badge-warning' : 'badge-danger')}">${item.status}</span>`;

			let diffColor = "text-muted";
			if (["revenue", "gross_profit", "gross_margin", "net_cash_flow", "ending_cash"].includes(k.id)) {
				diffColor = absVal > 0 ? "text-success font-weight-bold" : (absVal < 0 ? "text-danger font-weight-bold" : "text-muted");
			} else {
				diffColor = absVal > 0 ? "text-danger font-weight-bold" : (absVal < 0 ? "text-success font-weight-bold" : "text-muted");
			}

			rowsHtml += `<tr>
				<td>
					<div class="font-weight-bold">${k.label}</div>
					<div class="text-muted" style="font-size: 11px;">${k.desc}</div>
				</td>
				<td class="text-muted">${baseStr}</td>
				<td class="font-weight-bold" style="font-size: 14px; color: #0f172a;">${simStr}</td>
				<td class="${diffColor}">${absStr}</td>
				<td class="${diffColor}">${relStr}</td>
				<td>${statusBadge}</td>
			</tr>`;
		});

		let shortfallAlert = "";
		if (res.shortfall_events && res.shortfall_events.length > 0) {
			const eventsHtml = res.shortfall_events.map(e => `
				<li class="mb-1">
					<b>[${frappe.utils.escape_html(e.date || "Analysis Horizon")} - ${e.urgency_level || "CRITICAL"}]:</b> 
					Projected cash balance drops to <b>${lotus_fin.core.format_currency(e.projected_cash, "VND")}</b>, 
					with cashflow deficit of <b>${lotus_fin.core.format_currency(e.deficit_amount, "VND")}</b>.
					<div class="text-danger mt-1">👉 <b>Action Plan:</b> ${frappe.utils.escape_html(e.recommended_action || "Urgent liquidity infusion required.")}</div>
				</li>
			`).join("");
			shortfallAlert = `
				<div class="lotus-banner lotus-banner-danger mt-3" style="border-left: 4px solid #ef4444; background: #fff5f5;">
					<div class="d-flex align-items-start">
						<span style="font-size: 20px; margin-right: 10px;">⚠️</span>
						<div>
							<b style="color: #b91c1c; font-size: 13px;">CRITICAL LIQUIDITY STRESS ALERT:</b>
							<ul class="mb-0 pl-3 mt-1" style="font-size: 12px; line-height: 1.6;">${eventsHtml}</ul>
						</div>
					</div>
				</div>
			`;
		} else {
			shortfallAlert = `
				<div class="lotus-banner lotus-banner-warning mt-3" style="border-left: 4px solid #10b981; background: #f0fdf4;">
					<div class="d-flex align-items-center">
						<span style="font-size: 20px; margin-right: 10px;">🛡️</span>
						<div>
							<b style="color: #15803d; font-size: 13px;">STRESS TEST PASSED (NO SHORTFALL):</b>
							<div class="text-muted" style="font-size: 12px; margin-top: 2px;">
								Under all applied shock assumptions, the business successfully maintains its cash buffer above the minimum threshold without liquidity insolvency.
							</div>
						</div>
					</div>
				</div>
			`;
		}

		container.html(`
			${impactCardsHtml}
			<div class="table-responsive mt-3">
				<table class="lotus-table">
					<thead>
						<tr>
							<th style="width: 32%;">${__("Strategic Financial KPI")}</th>
							<th style="width: 15%;">${__("Baseline")}</th>
							<th style="width: 17%;">${__("Simulated (Scenario)")}</th>
							<th style="width: 15%;">${__("Absolute Change (Δ)")}</th>
							<th style="width: 11%;">${__("Percent (%)")}</th>
							<th style="width: 10%;">${__("Health Status")}</th>
						</tr>
					</thead>
					<tbody>
						${rowsHtml}
					</tbody>
				</table>
			</div>
			${shortfallAlert}
		`);
	}

	format_sim_val(val, meta) {
		if (val === null || val === undefined) return "—";
		if (meta.is_ratio) {
			return `${(val * 100).toFixed(2)}%`;
		}
		if (meta.is_days) {
			return `${val.toFixed(1)} Days`;
		}
		return lotus_fin.core.format_currency(val, "VND");
	}
};
