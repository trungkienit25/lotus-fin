// Lotus Fin Cash Forecast Copilot Page Controller & UI (Google Material 3 DNA)
frappe.provide("lotus_fin.cash_forecast");

frappe.pages["cash-forecast"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Dự báo Dòng tiền & Runway (AI002)"),
		single_column: true
	});

	wrapper.cash_forecast = new lotus_fin.cash_forecast.Controller(wrapper);
};

frappe.pages["cash-forecast"].refresh = function (wrapper) {
	if (wrapper.cash_forecast) {
		wrapper.cash_forecast.refresh();
	}
};

// Safe pure currency formatter (no HTML tags)
function format_money(val, currency = "VND") {
	if (val === null || val === undefined || isNaN(val)) return "0 " + currency;
	return Math.round(Number(val)).toLocaleString("vi-VN") + " " + currency;
}

lotus_fin.cash_forecast.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.financial_as_of = "2026-09-26";
		this.request_generation = 0;
		this.data = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.load_default_company_and_fetch();
	}

	setup_breadcrumbs() {
		frappe.breadcrumbs.add("Accounts");
	}

	setup_filters() {
		const me = this;

		// 1. Company selector
		this.company_field = this.page.add_field({
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"),
			change() {
				const val = me.company_field.get_value();
				if (val !== me.current_company) {
					me.current_company = val;
					me.on_company_change();
				}
			}
		});

		// 2. Financial As-Of Date
		this.as_of_field = this.page.add_field({
			fieldname: "financial_as_of",
			label: __("As of Date"),
			fieldtype: "Date",
			default: "2026-09-26",
			change() {
				me.financial_as_of = me.as_of_field.get_value();
				me.fetch_forecast();
			}
		});

		// Navigation buttons
		this.page.add_inner_button(__("🤖 Lotus Copilot"), function () {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("⚠️ Tín hiệu Rủi ro (AI003)"), function () {
			frappe.set_route("risk-signal");
		});

		this.page.add_inner_button(__("🔮 What-If Studio (AI004)"), function () {
			frappe.set_route("what-if-studio");
		});

		this.page.set_primary_action(__("Chạy dự báo dòng tiền"), function () {
			me.fetch_forecast(true);
		}, "octicon octicon-sync");
	}

	setup_dom() {
		this.page.main.empty();
		this.container = $(`
			<div class="lotus-financial-health-container" style="max-width: 1280px; margin: 0 auto;">
				<!-- Header Banner (Material 3 Style) -->
				<div class="lotus-fh-header-card">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<div class="d-flex align-items-center gap-2 mb-2">
								<span class="lotus-brand-badge">Lotus Fin • Cash Forecast & Runway (AI002)</span>
								<span class="lotus-badge lotus-badge-primary">Horizon: 30 Days</span>
							</div>
							<h1 class="lotus-fh-title">💧 ${__("Dự báo Dòng tiền & Đường băng Thanh khoản")}</h1>
							<p class="lotus-fh-subtitle">${__("Mô hình dự báo dòng tiền tất định 30 ngày, đối chiếu cân đối sổ cái & cảnh báo điểm thâm hụt")}</p>
						</div>
						<div id="cf-verification-badge">
							<span class="lotus-badge lotus-badge-neutral">Đang chờ dữ liệu...</span>
						</div>
					</div>
				</div>

				<!-- Alert Containers (Account Imbalance / Shortfall / Forbidden) -->
				<div id="cf-alert-area"></div>

				<!-- Server-resolved account scope banner (Fix C) -->
				<div id="cf-scope-status" class="mb-4"></div>

				<!-- Main 3-Tier Dashboard Grid -->
				<div class="row">
					<!-- Left 8 Cols: Finance Viewport -->
					<div class="col-lg-8 col-md-12">
						<!-- Tier 1: Ledger Truth & Opening Cash -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>🏦</span>
										<span>${__("Tier 1: Số dư Tiền & Ngân hàng Khởi tạo")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("Đối chiếu độc lập giữa General Ledger (GL) và Bảng cân đối thử (Trial Balance)")}</p>
								</div>
								<span id="cf-reconciliation-status" class="lotus-badge lotus-badge-neutral">Đang xác thực...</span>
							</div>

							<div class="p-4 rounded-2xl mb-3" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid var(--lotus-border);">
								<div class="text-muted" style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${__("Tổng số dư tiền mặt hợp nhất (Aggregate Cash)")}</div>
								<div id="cf-opening-amount" style="font-size: 32px; font-weight: 800; color: var(--lotus-text-primary); margin-top: 4px; letter-spacing: -0.5px;">-- VND</div>
							</div>

							<div class="text-muted mb-2" style="font-size: 12px; font-weight: 600;">${__("Chi tiết từng tài khoản thanh khoản:")}</div>
							<div id="cf-account-breakdown" class="d-flex flex-wrap gap-2"></div>
						</div>

						<!-- 30-Day Forecast Table / Trajectory -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>📈</span>
										<span>${__("Quỹ đạo Dòng tiền 30 Ngày (Daily EOD Trajectory)")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("Dòng tiền cuối ngày theo các sự kiện thanh toán đã xác nhận")}</p>
								</div>
								<span id="cf-points-count" class="lotus-badge lotus-badge-primary">30 Daily Points</span>
							</div>

							<div class="lotus-table-container" style="max-height: 320px; overflow-y: auto;">
								<table class="lotus-table">
									<thead>
										<tr>
											<th style="width: 25%;">${__("Ngày (Date)")}</th>
											<th style="width: 35%;">${__("Số dư dự báo (EOD Cash)")}</th>
											<th style="width: 25%;">${__("Sự kiện quyết toán")}</th>
											<th style="width: 15%; text-align: center;">${__("Trạng thái")}</th>
										</tr>
									</thead>
									<tbody id="cf-points-tbody">
										<tr><td colspan="4" class="text-center text-muted py-4">${__("Chưa có dữ liệu dự báo được tạo.")}</td></tr>
									</tbody>
								</table>
							</div>
						</div>

						<!-- Tier 2: Obligations (Contractual Due Dates) -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-3">
								<div>
									<h3 class="lotus-card-title">
										<span>📑</span>
										<span>${__("Tier 2: Nghĩa vụ Thanh toán (AR / AP Due Dates)")}</span>
									</h3>
									<p class="lotus-card-subtitle">${__("Hạn nợ hợp đồng của Hóa đơn Bán hàng (AR) & Hóa đơn Mua hàng (AP)")}</p>
								</div>
							</div>

							<div class="lotus-table-container" style="max-height: 260px; overflow-y: auto;">
								<table class="lotus-table">
									<thead>
										<tr>
											<th style="width: 12%; text-align: center;">${__("Loại")}</th>
											<th style="width: 22%;">${__("Mã đối tác (Hash)")}</th>
											<th style="width: 20%;">${__("Hạn thanh toán")}</th>
											<th style="width: 26%;">${__("Số tiền còn lại")}</th>
											<th style="width: 20%;">${__("Chứng từ gốc")}</th>
										</tr>
									</thead>
									<tbody id="cf-obligations-tbody">
										<tr><td colspan="5" class="text-center text-muted py-4">${__("Không có nghĩa vụ công nợ tồn đọng.")}</td></tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>

					<!-- Right 4 Cols: Decoupled Copilot & Explanations -->
					<div class="col-lg-4 col-md-12">
						<!-- Bounded AI Copilot Explanation Card -->
						<div class="lotus-card mb-4" style="border: 1px solid rgba(99, 102, 241, 0.25); box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);">
							<div class="lotus-card-header mb-2">
								<h3 class="lotus-card-title" style="color: var(--lotus-ai-magic);">
									<span>🤖</span>
									<span>${__("AI Financial Copilot")}</span>
								</h3>
								<span id="cf-explanation-badge" class="lotus-badge lotus-badge-ai">Bounded AI</span>
							</div>
							<div id="cf-copilot-content" style="font-size: 13px; line-height: 1.6; color: var(--lotus-text-secondary);">
								<p class="text-muted">${__("Nhấn nút <b>Chạy dự báo dòng tiền</b> để AI tổng hợp bằng chứng sổ cái và đưa ra hướng dẫn quản trị.")}</p>
							</div>
						</div>

						<!-- Next Checks & Deep Links -->
						<div class="lotus-card mb-4">
							<div class="lotus-card-header mb-2">
								<h3 class="lotus-card-title" style="font-size: 14px;">
									<span>🎯</span>
									<span>${__("Khuyến nghị Hành động (Next Checks)")}</span>
								</h3>
							</div>
							<ul id="cf-next-checks-list" class="list-unstyled mb-0 d-flex flex-column gap-2" style="font-size: 13px;">
								<li>
									<a href="/app/bank-reconciliation-tool" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>🏦 Đối chiếu sao kê ngân hàng</span>
										<span>&rarr;</span>
									</a>
								</li>
								<li>
									<a href="/app/query-report/Accounts%20Receivable?status=Overdue" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>⚠️ Thu hồi nợ quá hạn AR</span>
										<span>&rarr;</span>
									</a>
								</li>
								<li>
									<a href="/app/purchase-invoice" class="lotus-action-btn w-100 justify-content-between" style="text-decoration: none;">
										<span>📦 Xác nhận lịch thanh toán AP</span>
										<span>&rarr;</span>
									</a>
								</li>
							</ul>
						</div>

						<!-- Limitations & Disclosures -->
						<div class="lotus-card" style="background: var(--lotus-surface-app); border: 1px dashed var(--lotus-border);">
							<div class="text-muted" style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
								🛡️ ${__("Giới hạn Phạm vi Hợp đồng (Contract Limitations)")}
							</div>
							<div id="cf-limitations-list" style="font-size: 12px; color: var(--lotus-text-muted); line-height: 1.6;">
								<div>• Phạm vi mô hình tập trung vào Thương mại AR/AP và Số dư đầu kỳ GL.</div>
								<div>• Không tự ý suy diễn các khoản thuế, lương, và chi phí dịch vụ chưa có chứng từ.</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);
		this.page.main.append(this.container);
	}

	load_default_company_and_fetch() {
		const comp = this.company_field.get_value();
		if (comp) {
			this.current_company = comp;
			this.fetch_forecast();
		}
	}

	refresh() {
		this.fetch_forecast();
	}

	on_company_change() {
		this.request_generation += 1;
		this.data = null;
		$("#cf-alert-area").empty();
		$("#cf-scope-status").empty();
		$("#cf-opening-amount").text("-- VND");
		$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
		$("#cf-account-breakdown").empty();
		$("#cf-verification-badge").empty();
		$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Đang tải dữ liệu dự báo cho công ty đã chọn...</td></tr>');
		$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Đang tải danh sách nghĩa vụ...</td></tr>');
		$("#cf-copilot-content").html('<p class="text-muted">Đang kết nối AI Copilot...</p>');
		this.fetch_forecast();
	}

	fetch_forecast(want_explanation = true) {
		const me = this;
		const company = this.company_field.get_value();
		const as_of = this.as_of_field.get_value() || "2026-09-26";

		if (!company) {
			return;
		}

		const request_token = ++this.request_generation;

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_ai002_cash_account_scope",
			args: { company: company }
		}).then(function (r) {
			if (request_token !== me.request_generation) {
				return;
			}
			if (r.exc) {
				me.render_error("Không thể xác định phạm vi tài khoản tiền mặt.");
				return;
			}
			const scope = r.message;
			if (!scope || scope.status !== "RESOLVED" || !Array.isArray(scope.scope) || scope.scope.length === 0) {
				me.render_scope_needs_review(scope || {});
				return;
			}
			me.render_scope_banner(scope);

			return frappe.call({
				method: "lotus_fin.api.ai_insights.get_ai002_cash_forecast",
				args: {
					company: company,
					financial_as_of: as_of,
					currency: "VND",
					include_explanation: want_explanation
				}
			}).then(function (r2) {
				if (request_token !== me.request_generation) {
					return;
				}
				if (r2.exc) {
					me.render_error("Lỗi máy chủ khi tính toán dự báo dòng tiền.");
					return;
				}
				const resp = r2.message;
				if (resp && resp.verified_company && resp.verified_company !== me.company_field.get_value()) {
					return;
				}
				me.data = resp;
				me.render_dashboard(resp);
			});
		}).catch(function () {
			if (request_token === me.request_generation) {
				me.render_error("Không thể nạp dữ liệu dự báo dòng tiền.");
			}
		});
	}

	render_scope_banner(scope) {
		const el = $("#cf-scope-status").empty();
		const count = (scope.count !== undefined && scope.count !== null)
			? scope.count
			: (scope.scope ? scope.scope.length : 0);
		const approval = scope.approval || "APPROVED";
		let html = `<div class="d-flex align-items-center gap-2">
			<span class="lotus-badge lotus-badge-success">Phạm vi tài khoản: ${count} tài khoản hợp lệ — ${approval}</span>`;
		if (scope.unapproved_excluded && scope.unapproved_excluded.length > 0) {
			html += `<span class="lotus-badge lotus-badge-warning">${scope.unapproved_excluded.length} tài khoản chưa phê duyệt bị loại trừ</span>`;
		}
		html += `</div>`;
		el.html(html);
	}

	render_scope_needs_review(scope) {
		const approval = scope.approval || "MISSING_CONFIG";
		const reasons = {
			MISSING_CONFIG: "Chưa cấu hình danh sách tài khoản tiền/ngân hàng được phê duyệt cho công ty này.",
			INVALID_CONFIG: "Cấu hình phạm vi tài khoản tiền mặt bị trống hoặc không hợp lệ.",
			STALE_CONFIG: "Phạm vi tài khoản tham chiếu đến tài khoản không còn tồn tại hoặc đã bị vô hiệu hóa."
		};
		const reason = reasons[approval] || "Không thể xác nhận phạm vi tài khoản tiền mặt được phê duyệt.";
		$("#cf-scope-status").html(`
			<div class="lotus-banner lotus-banner-warning">
				<b>Cần kiểm tra lại phạm vi tài khoản (${approval}):</b><br/>
				${reason} Mô hình dự báo tạm khóa cho đến khi quản trị viên tài chính phê duyệt danh mục tài khoản trên hồ sơ Công ty.
			</div>
		`);
		$("#cf-opening-amount").text("-- VND");
		$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
		$("#cf-account-breakdown").empty();
		$("#cf-verification-badge").html('<span class="lotus-badge lotus-badge-warning">Cần duyệt cấu hình</span>');
		$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Dự báo tạm khóa: Cần kiểm tra lại phạm vi tài khoản.</td></tr>');
		$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Dự báo tạm khóa: Cần kiểm tra lại phạm vi tài khoản.</td></tr>');
		$("#cf-copilot-content").html('<p class="text-muted">Vui lòng cấu hình tài khoản tiền mặt để kích hoạt dự báo.</p>');
	}

	render_dashboard(resp) {
		const alertArea = $("#cf-alert-area").empty();

		if (resp.status === "FORBIDDEN" || (resp.reason_code && resp.reason_code === "UNAUTHORIZED_ACCESS")) {
			alertArea.html(`
				<div class="lotus-banner lotus-banner-danger mb-4">
					<h5 style="margin-top: 0; color: #b91c1c;">Từ chối truy cập (FORBIDDEN)</h5>
					<p class="mb-2">Bạn không có quyền truy cập dữ liệu dự báo tài chính của công ty được yêu cầu.</p>
					<button class="lotus-btn lotus-btn-primary lotus-btn-sm" onclick="frappe.set_route('Form', 'Company')">Chuyển công ty</button>
				</div>
			`);
			$("#cf-opening-amount").text("-- VND");
			$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
			$("#cf-account-breakdown").empty();
			$("#cf-verification-badge").empty();
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Từ chối truy cập.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Từ chối truy cập.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Từ chối truy cập.</p>');
			return;
		}

		if (resp.status === "SOURCE_ERROR" || resp.status === "TIMEOUT") {
			alertArea.html(`
				<div class="lotus-banner lotus-banner-danger mb-4">
					<h5 style="margin-top: 0; color: #b91c1c;">Lỗi Nguồn Dữ liệu Tài chính</h5>
					<p class="mb-1">Một nguồn dữ liệu bắt buộc (AR / AP / Trial Balance) không thể đọc được. Dự báo bị dừng để đảm bảo tính an toàn dữ liệu.</p>
					<p class="text-muted mb-0" style="font-size: 12px;">${(resp.limitations && resp.limitations[0]) || "Nguồn dữ liệu tạm thời không khả dụng."}</p>
				</div>
			`);
			$("#cf-opening-amount").text("-- VND");
			$("#cf-reconciliation-status").text("").attr("class", "lotus-badge lotus-badge-neutral");
			$("#cf-account-breakdown").empty();
			$("#cf-verification-badge").html('<span class="lotus-badge lotus-badge-danger">Lỗi nguồn dữ liệu</span>');
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Dự báo tạm dừng do lỗi nguồn dữ liệu.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Dự báo tạm dừng do lỗi nguồn dữ liệu.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Vui lòng xử lý lỗi nguồn dữ liệu và thử lại.</p>');
			return;
		}

		if (resp.status === "INSUFFICIENT_DATA" || resp.status === "INCONSISTENT_DATA") {
			const isInconsistent = resp.status === "INCONSISTENT_DATA";
			alertArea.html(`
				<div class="lotus-banner ${isInconsistent ? 'lotus-banner-danger' : 'lotus-banner-warning'} mb-4">
					<h5 style="margin-top: 0; color: ${isInconsistent ? '#b91c1c' : '#c2410c'};">${isInconsistent ? "Dữ liệu Sổ cái Không đồng nhất" : "Số dư Tiền chưa được Xác thực"}</h5>
					<p class="mb-1">${isInconsistent
						? "Sổ cái General Ledger không khớp với Bảng cân đối thử Trial Balance cho danh mục tài khoản được chỉ định. Dự báo bị dừng."
						: "Chưa có bằng chứng đối chiếu số dư đầu kỳ, không thể tính toán quỹ đạo dòng tiền."}</p>
					<p class="text-muted mb-0" style="font-size: 12px;">${(resp.limitations && resp.limitations[0]) || ""}</p>
				</div>
			`);
			if (resp.opening_cash) {
				$("#cf-opening-amount").text(format_money(resp.opening_cash.aggregate_amount, resp.currency || "VND"));
				$("#cf-reconciliation-status").text(resp.opening_cash.reconciliation).attr("class", "lotus-badge lotus-badge-warning");
			}
			$("#cf-verification-badge").html(isInconsistent
				? '<span class="lotus-badge lotus-badge-danger">Sổ cái không khớp</span>'
				: '<span class="lotus-badge lotus-badge-warning">Chưa đối chiếu</span>');
			$("#cf-points-tbody").html('<tr><td colspan="4" class="text-center text-muted py-4">Dự báo tạm dừng: Số dư đầu kỳ chưa được xác thực.</td></tr>');
			$("#cf-obligations-tbody").html('<tr><td colspan="5" class="text-center text-muted py-4">Dự báo tạm dừng: Số dư đầu kỳ chưa được xác thực.</td></tr>');
			$("#cf-copilot-content").html('<p class="text-muted">Vui lòng đối chiếu sổ cái, sau đó tính toán lại dự báo.</p>');
			return;
		}

		const recon = resp.opening_cash ? resp.opening_cash.reconciliation : null;
		const isLedgerVerified = recon === "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED"
			|| recon === "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED";
		$("#cf-verification-badge").html(isLedgerVerified
			? '<span class="lotus-badge lotus-badge-success">🛡️ Sổ cái đã Đối chiếu Hợp lệ</span>'
			: '<span class="lotus-badge lotus-badge-warning">⚠️ Sổ cái Chưa đối chiếu</span>');

		// Check Shortfall Alerts
		if (resp.shortfall_events && resp.shortfall_events.length > 0) {
			const sf = resp.shortfall_events[0];
			const isInherited = sf.breach_kind === "INHERITED_FROM_OPENING";
			const title = isInherited ? "Cảnh báo Thâm hụt Kế thừa từ Đầu kỳ" : "CẢNH BÁO NGUY CƠ THÂM HỤT THANH KHOẢN (LIQUIDITY SHORTFALL)";
			alertArea.append(`
				<div class="lotus-banner ${isInherited ? 'lotus-banner-warning' : 'lotus-banner-danger'} mb-4">
					<b>${title}:</b> Dòng tiền dự kiến rơi xuống dưới 0 vào ngày <b>${sf.first_date}</b>, chạm đáy thâm hụt <b>${format_money(sf.minimum_modeled_cash, "VND")}</b> vào ngày <b>${sf.minimum_date}</b>.
				</div>
			`);
		}

		// Check Constituent Account Deficit
		if (resp.opening_cash && resp.opening_cash.has_constituent_deficit) {
			alertArea.append(`
				<div class="lotus-banner lotus-banner-warning mb-4">
					<b>Cảnh báo Lệch tài khoản nội bộ:</b> Một hoặc nhiều tài khoản ngân hàng thành viên bị âm số dư, mặc dù tổng dòng tiền hợp nhất vẫn dương. Cần điều chuyển vốn nội bộ.
				</div>
			`);
		}

		// Render Opening Cash
		if (resp.opening_cash) {
			$("#cf-opening-amount").text(format_money(resp.opening_cash.aggregate_amount, resp.currency || "VND"));
			$("#cf-reconciliation-status")
				.text(resp.opening_cash.reconciliation)
				.attr("class", isLedgerVerified ? "lotus-badge lotus-badge-success" : "lotus-badge lotus-badge-warning");
			
			let accHtml = "";
			if (resp.opening_cash.accounts) {
				accHtml = resp.opening_cash.accounts.map(a => `
					<div class="lotus-evidence-item mb-0" style="padding: 6px 12px; border-radius: var(--lotus-radius-pill); font-size: 12px;">
						<span style="font-weight: 500;">${frappe.utils.escape_html(a.account)}:</span>
						<b style="color: ${a.deficit ? '#dc2626' : 'var(--lotus-text-primary)'}; margin-left: 4px;">
							${format_money(a.amount, a.currency || "VND")}
						</b>
					</div>
				`).join("");
			}
			$("#cf-account-breakdown").html(accHtml);
		}

		// Render Forecast Points
		const tbody = $("#cf-points-tbody").empty();
		if (!resp.forecast_points || resp.forecast_points.length === 0) {
			tbody.html(`
				<tr><td colspan="4" class="text-center text-muted py-4">
					<b>Không tìm thấy sự kiện thanh toán tương lai đã xác nhận.</b><br/>
					Mô hình dừng lại theo chính sách an toàn tất định.
				</td></tr>
			`);
		} else {
			resp.forecast_points.forEach(p => {
				const val = parseFloat(p.modeled_cash);
				const isNeg = val < 0;
				const eventsCount = p.included_event_ids ? p.included_event_ids.length : 0;
				tbody.append(`
					<tr style="${isNeg ? 'background-color: #fef2f2;' : ''}">
						<td><span class="font-weight-bold" style="color: var(--lotus-text-primary);">${p.date}</span></td>
						<td style="${isNeg ? 'color: #dc2626; font-weight: 700;' : 'color: var(--lotus-primary); font-weight: 600;'}">
							${format_money(p.modeled_cash, resp.currency || "VND")}
						</td>
						<td>${eventsCount > 0 ? `<span class="lotus-badge lotus-badge-primary">${eventsCount} sự kiện</span>` : '<span class="text-muted">—</span>'}</td>
						<td style="text-align: center;"><span class="lotus-badge lotus-badge-neutral">${p.status}</span></td>
					</tr>
				`);
			});
		}

		// Render Obligations
		const obTbody = $("#cf-obligations-tbody").empty();
		if (!resp.obligations || resp.obligations.length === 0) {
			obTbody.html('<tr><td colspan="5" class="text-center text-muted py-4">Không có nghĩa vụ công nợ tồn đọng.</td></tr>');
		} else {
			resp.obligations.forEach(o => {
				const isAR = o.type === "AR";
				obTbody.append(`
					<tr>
						<td style="text-align: center;"><span class="lotus-badge ${isAR ? 'lotus-badge-success' : 'lotus-badge-warning'}">${o.type}</span></td>
						<td><span class="lotus-code-badge">${o.party_hash || '-'}</span></td>
						<td style="color: var(--lotus-text-secondary);">${o.due_date || 'N/A'}</td>
						<td style="font-weight: 600; color: var(--lotus-text-primary);">${format_money(o.remaining_amount, o.currency || "VND")}</td>
						<td><span class="text-muted" style="font-size: 11px;">${frappe.utils.escape_html(o.source_ref)}</span></td>
					</tr>
				`);
			});
		}

		// Render Copilot Explanation
		const copilotDiv = $("#cf-copilot-content").empty();
		if (resp.explanation) {
			let factsHtml = "<div class='mb-2'><b>Bằng chứng Sổ cái Đã xác thực:</b></div><ul class='pl-3 mb-3' style='line-height: 1.6;'>";
			(resp.explanation.facts || []).forEach(f => {
				factsHtml += `<li>${frappe.utils.escape_html(f.statement)}</li>`;
			});
			factsHtml += "</ul>";

			let driversHtml = "";
			if (resp.explanation.drivers && resp.explanation.drivers.length > 0) {
				driversHtml = "<div class='mb-2'><b>Nhận định & Diễn giải AI:</b></div><div class='p-3 rounded-xl' style='background: var(--lotus-surface-subtle); border-left: 3px solid var(--lotus-ai-magic); line-height: 1.6;'>" +
					resp.explanation.drivers.map(d => frappe.utils.escape_html(d.statement)).join("<br/>") +
					"</div>";
			}

			copilotDiv.html(factsHtml + driversHtml);
		} else {
			copilotDiv.html(`
				<p class="text-muted">Đã tính toán dự báo tất định. Bấm <b>Chạy dự báo dòng tiền</b> để yêu cầu AI tổng hợp phân tích.</p>
			`);
		}
	}

	render_error(msg) {
		frappe.msgprint({
			title: __("Thông báo Dòng tiền"),
			indicator: "orange",
			message: msg
		});
	}
};
