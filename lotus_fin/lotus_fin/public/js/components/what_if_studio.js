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
						<button class="lotus-btn-secondary btn-reset-sim-defaults" style="font-size: 11px; padding: 4px 12px;" title="${__("Khôi phục kịch bản gốc")}">
							↺ ${__("Mặc định")}
						</button>
					</div>
				</div>
				<p class="text-muted" style="font-size: 12px; margin-bottom: 14px;">
					${__("Mô phỏng áp lực tài chính đa biến theo tiêu chuẩn định lượng (Stress-Testing). Khảo sát tác động đồng thời của biến động doanh số, độ trễ thanh toán AR/AP, chi phí vận hành định phí và gói tài trợ vốn lên 9 chỉ số sống còn của doanh nghiệp.")}
				</p>

				<!-- Kịch bản stress-test mẫu cấu hình sẵn -->
				<div class="mb-3">
					<span class="text-muted" style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">🎯 ${__("Kịch bản áp lực tiêu biểu (Stress Presets):")}</span>
					<div class="lotus-preset-scenarios mt-1">
						<button class="lotus-preset-btn" data-preset="sales_slump">
							📉 <b>${__("Khủng hoảng cầu (Sales Slump -30%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="credit_crunch">
							⏱️ <b>${__("Nợ đọng kéo dài (AR Delay +30 ngày)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="cost_inflation">
							📈 <b>${__("Lạm phát chi phí (OPEX +20%, Lương +10%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="black_swan">
							⚡ <b>${__("Cú sốc kép (Doanh thu -25%, Khách trễ 20N, Chi phí +15%)")}</b>
						</button>
						<button class="lotus-preset-btn" data-preset="growth_injection">
							🚀 <b>${__("Tăng tốc mở rộng (Doanh số +30%, Vay 500tr)")}</b>
						</button>
					</div>
				</div>

				<!-- Khối tham số 1: Thị trường & Doanh thu & Công nợ -->
				<div class="lotus-sim-group-title">
					<span>📊 Nhóm 1: Doanh thu & Chu kỳ Công nợ thương mại (AR / AP)</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Biến động Doanh thu thuần")}</span>
							<span class="lotus-sim-val-badge negative" id="val-sim-sales">-15%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-sales" min="-50" max="50" step="5" value="-15">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-50% (Suy thoái sâu)</span>
							<span>0% (Cơ sở)</span>
							<span>+50% (Tăng trưởng)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Tác động trực tiếp đến dòng tiền vào và biên lợi nhuận gộp.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Khách hàng thanh toán chậm (DSO Shift)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-delay">+15 ngày</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-delay" min="0" max="60" step="5" value="15">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>0 ngày (Đúng hạn)</span>
							<span>+30 ngày</span>
							<span>+60 ngày (Nợ khó đòi)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Làm tăng công nợ AR treo và kéo dài chu kỳ tiền mặt CCC.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Đàm phán giãn nợ Nhà cung cấp (DPO Shift)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-supplier">0 ngày</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-supplier" min="-30" max="60" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30 ngày (Bị siết nợ)</span>
							<span>0 ngày</span>
							<span>+60 ngày (Tối ưu vốn)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Hoãn thanh toán phải trả AP để bảo toàn số dư tiền mặt.")}</div>
					</div>
				</div>

				<!-- Khối tham số 2: Chi phí vận hành & Cú sốc phát sinh -->
				<div class="lotus-sim-group-title">
					<span>🏢 Nhóm 2: Chi phí vận hành (OPEX), Quỹ lương & Cú sốc đột xuất</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Biến động Chi phí Vận hành (OPEX)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-opex">0%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-opex" min="-30" max="50" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30% (Thắt chặt chi phí)</span>
							<span>0%</span>
							<span>+50% (Đội chi phí)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Thuê mặt bằng, marketing, logistic, điện nước, hành chính...")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Biến động Quỹ lương & Nhân sự (Payroll)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-payroll">0%</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-payroll" min="-30" max="40" step="5" value="0">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>-30% (Cắt giảm nhân sự)</span>
							<span>0%</span>
							<span>+40% (Mở rộng tuyển dụng)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Lương cứng, bảo hiểm, thưởng định kỳ của toàn công ty.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Chi phí đột xuất phát sinh (One-off Shock)")}</span>
							<span class="lotus-sim-val-badge" id="val-sim-one-off">0 VND</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-one-off">
							<option value="0" selected>${__("Không phát sinh (0 VND)")}</option>
							<option value="50000000">50.000.000 VND (Sửa chữa máy móc/thiết bị)</option>
							<option value="100000000">100.000.000 VND (Truy thu thuế / phạt hành chính)</option>
							<option value="200000000">200.000.000 VND (Đặt cọc mở rộng chi nhánh mới)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Khoản rút tiền đột xuất một lần tạo áp lực thanh khoản ngay lập tức.")}</div>
					</div>
				</div>

				<!-- Khối tham số 3: Tiếp nhận vốn vay & Lãi suất tài trợ -->
				<div class="lotus-sim-group-title">
					<span>💰 Nhóm 3: Tài trợ Vốn vay & Cấu trúc Tín dụng bổ sung (AI-F005)</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Gói Tín dụng Tiếp nhận")}</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-financing">
							<option value="0">${__("Không nhận vốn bổ sung (Tự cân đối)")}</option>
							<option value="200000000">200.000.000 VND (Vay thấu chi / hạn mức)</option>
							<option value="300000000" selected>300.000.000 VND (Vay bổ sung VLĐ ngắn hạn)</option>
							<option value="500000000">500.000.000 VND (Vay trung hạn mở rộng)</option>
							<option value="1000000000">1.000.000.000 VND (Gói hợp vốn ngân hàng)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Số tiền giải ngân sẽ bơm trực tiếp vào dòng tiền ròng của kỳ.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Thời hạn vay (Kỳ hạn)")}</span>
						</div>
						<select class="lotus-sim-input" id="input-sim-fin-term">
							<option value="6">6 tháng (Vay lưu động ngắn hạn)</option>
							<option value="12" selected>12 tháng (Tiêu chuẩn tài trợ 1 năm)</option>
							<option value="24">24 tháng (Trung hạn)</option>
							<option value="36">36 tháng (Đầu tư dài hạn)</option>
						</select>
						<div class="lotus-sim-subhint">${__("Ảnh hưởng đến tốc độ phân bổ hoàn trả và chi phí lãi.")}</div>
					</div>

					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Lãi suất danh nghĩa hàng năm (%/năm)")}</span>
							<span class="lotus-sim-val-badge positive" id="val-sim-rate">9.5%/năm</span>
						</div>
						<input type="range" class="custom-range" id="input-sim-rate" min="5" max="18" step="0.5" value="9.5">
						<div class="d-flex justify-content-between text-muted" style="font-size: 10px; margin-top: 4px;">
							<span>5.0% (Ưu đãi)</span>
							<span>9.5% (Thị trường)</span>
							<span>18.0% (Tín chấp cao)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Chi phí lãi vay phát sinh được trừ vào dòng tiền thuần kỳ.")}</div>
					</div>
				</div>

				<div class="mb-3 d-flex gap-2">
					<button class="lotus-sim-btn btn-run-simulation" style="padding: 10px 24px; font-size: 14px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); box-shadow: 0 2px 6px rgba(13, 148, 136, 0.3);">
						🚀 ${__("Chạy mô phỏng Stress-Test (Định lượng 9 KPIs)")}
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
			me.$el.find("#val-sim-delay").text("+" + $(this).val() + " ngày");
		});

		this.$el.on("input", "#input-sim-supplier", function () {
			const val = $(this).val();
			me.$el.find("#val-sim-supplier").text((val > 0 ? "+" : "") + val + " ngày");
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
			badge.text(frappe.format(val, { fieldtype: "Currency", currency: "VND" }));
			badge.removeClass("negative").addClass(val > 0 ? "negative" : "");
		});

		this.$el.on("input", "#input-sim-rate", function () {
			me.$el.find("#val-sim-rate").text($(this).val() + "%/năm");
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

		this.$result.html(`<div class="text-muted p-3 text-center"><i class="octicon octicon-sync"></i> ${__("Đang chạy mô hình stress-test 9 lớp chỉ số tài chính...")}</div>`);

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
					me.$result.html(`<div class="lotus-banner lotus-banner-danger">${__("Không thể chạy mô phỏng kịch bản. Vui lòng kiểm tra tham số đầu vào.")}</div>`);
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
					<div class="lotus-impact-card-title">💵 ${__("Tiền mặt cuối kỳ (Ending Cash)")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(endingCash.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${endingCash.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${endingCash.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(endingCash.absolute_change, { is_currency: true })}</span>
						<span class="text-muted">(${endingCash.relative_change !== null ? (endingCash.relative_change * 100).toFixed(1) + '%' : '—'})</span>
					</div>
				</div>

				<div class="lotus-impact-card ${ncfStatus}">
					<div class="lotus-impact-card-title">🌊 ${__("Dòng tiền thuần (Net Cash Flow)")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(ncf.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${ncf.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${ncf.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(ncf.absolute_change, { is_currency: true })}</span>
					</div>
				</div>

				<div class="lotus-impact-card status-healthy">
					<div class="lotus-impact-card-title">📈 ${__("Doanh thu sau sốc (Revenue)")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(rev.simulation, { is_currency: true })}</div>
					<div class="lotus-impact-card-delta ${rev.absolute_change < 0 ? 'delta-down' : 'delta-up'}">
						<span>${rev.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(rev.absolute_change, { is_currency: true })}</span>
					</div>
				</div>

				<div class="lotus-impact-card ${ccc.simulation > 90 ? 'status-warning' : 'status-healthy'}">
					<div class="lotus-impact-card-title">⏳ ${__("Chu kỳ tiền mặt (Cash Conversion Cycle)")}</div>
					<div class="lotus-impact-card-val">${this.format_sim_val(ccc.simulation, { is_days: true })}</div>
					<div class="lotus-impact-card-delta ${ccc.absolute_change > 0 ? 'delta-down' : 'delta-up'}">
						<span>${ccc.absolute_change >= 0 ? '▲ +' : '▼ '}${this.format_sim_val(ccc.absolute_change, { is_days: true })}</span>
					</div>
				</div>
			</div>
		`;

		const kpiList = [
			{ id: "revenue", label: __("1. Doanh thu thuần (Revenue)"), desc: __("Quy mô bán hàng sau cú sốc"), is_currency: true },
			{ id: "gross_profit", label: __("2. Lợi nhuận gộp (Gross Profit)"), desc: __("Lãi gộp đóng góp trang trải định phí"), is_currency: true },
			{ id: "gross_margin", label: __("3. Biên lợi nhuận gộp (Gross Margin)"), desc: __("Tỷ suất sinh lời trực tiếp"), is_ratio: true },
			{ id: "ar_outstanding", label: __("4. Công nợ phải thu (AR)"), desc: __("Vốn lưu động đang bị khách hàng chiếm dụng"), is_currency: true },
			{ id: "dso", label: __("5. Số ngày thu tiền bình quân (DSO)"), desc: __("Độ trễ dòng tiền vào"), is_days: true },
			{ id: "net_cash_flow", label: __("6. Dòng tiền thuần kỳ (Net Cash Flow)"), desc: __("Dòng tiền vào trừ toàn bộ chi trả và lãi vay"), is_currency: true },
			{ id: "ending_cash", label: __("7. Số dư tiền mặt cuối kỳ (Ending Cash)"), desc: __("Bộ đệm thanh khoản tiền & ngân hàng"), is_currency: true },
			{ id: "ccc", label: __("8. Chu kỳ chuyển hóa tiền (CCC)"), desc: __("Thời gian từ chi tiền mua hàng đến khi thu được tiền"), is_days: true },
			{ id: "cash_shortfall", label: __("9. Mức độ thâm hụt thanh khoản (Shortfall)"), desc: __("Chênh lệch thiếu hụt so với bộ đệm an toàn 50tr VND"), is_currency: true }
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
					<b>[${frappe.utils.escape_html(e.date || "Kỳ phân tích")} - ${e.urgency_level || "CRITICAL"}]:</b> 
					Số dư tiền giảm sâu còn <b>${frappe.format(e.projected_cash, { fieldtype: "Currency", currency: "VND" })}</b>, 
					thâm hụt dòng tiền <b>${frappe.format(e.deficit_amount, { fieldtype: "Currency", currency: "VND" })}</b>.
					<div class="text-danger mt-1">👉 <b>Hành động xử lý:</b> ${frappe.utils.escape_html(e.recommended_action || "Cần bù đắp thanh khoản khẩn cấp.")}</div>
				</li>
			`).join("");
			shortfallAlert = `
				<div class="lotus-banner lotus-banner-danger mt-3" style="border-left: 4px solid #ef4444; background: #fff5f5;">
					<div class="d-flex align-items-start">
						<span style="font-size: 20px; margin-right: 10px;">⚠️</span>
						<div>
							<b style="color: #b91c1c; font-size: 13px;">CẢNH BÁO RỦI RO THANH KHOẢN TRỌNG YẾU (LIQUIDITY STRESS ALERT):</b>
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
							<b style="color: #15803d; font-size: 13px;">KỊCH BẢN VƯỢT QUA BÀI KIỂM TRA ÁP LỰC (STRESS TEST PASSED):</b>
							<div class="text-muted" style="font-size: 12px; margin-top: 2px;">
								Dưới các giả định sốc đã áp dụng, doanh nghiệp vẫn bảo toàn được số dư tiền mặt trên ngưỡng an toàn tối thiểu và không bị âm dòng tiền thanh khoản.
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
							<th style="width: 32%;">${__("Chỉ số KPI Chiến lược")}</th>
							<th style="width: 15%;">${__("Kỳ cơ sở (Baseline)")}</th>
							<th style="width: 17%;">${__("Sau mô phỏng (Scenario)")}</th>
							<th style="width: 15%;">${__("Biến động tuyệt đối (Δ)")}</th>
							<th style="width: 11%;">${__("Tỷ lệ %")}</th>
							<th style="width: 10%;">${__("Đánh giá")}</th>
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
			return `${val.toFixed(1)} ngày`;
		}
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}
};
