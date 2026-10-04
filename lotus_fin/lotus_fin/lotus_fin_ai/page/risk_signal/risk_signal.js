// AI003 Risk Signal Page Controller & UI (Google Material 3 DNA, contract V2.2, DEMO_ONLY)
// Data is never interpolated into HTML: every dynamic value is set with
// textContent (text-node-only rendering; server output is escaped by design).
frappe.provide("lotus_fin.risk_signal");

frappe.pages["risk-signal"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Tín hiệu Rủi ro (AI003)"),
		single_column: true
	});
	wrapper.risk_signal = new lotus_fin.risk_signal.Controller(wrapper);
};

frappe.pages["risk-signal"].refresh = function (wrapper) {
	if (wrapper.risk_signal) {
		wrapper.risk_signal.refresh();
	}
};

lotus_fin.risk_signal.Controller = class Controller {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.current_company = null;
		this.in_flight = false;
		this.request_seq = 0;
		this.in_flight_request = null;
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.setup_events();
	}

	refresh() {
		// Called on page refresh / switch
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
			default:
				frappe.defaults.get_user_default("Company") ||
				frappe.defaults.get_global_default("company"),
			change() {
				me.invalidate_requests(__("Company changed — the previous result was cleared."));
			}
		});

		if (this.company_field && this.company_field.$input) {
			$(this.wrapper).on("input", "input[data-fieldname='company']", function () {
				const typed = $(this).val();
				me.last_typed_company = typed || "";
				me.invalidate_requests(__("Company changed — the previous result was cleared."));
			});
		}
		$(this.wrapper).on("input", "input[data-fieldname='as_of_date']", function () {
			me.invalidate_requests(__("Date changed — the previous result was cleared."));
		});

		this.signal_field = this.page.add_field({
			fieldname: "signal_id",
			label: __("Signal"),
			fieldtype: "Select",
			options: [
				{ label: __("AR Overdue Spike (Đột biến nợ quá hạn)"), value: "AR_OVERDUE_SPIKE" },
				{ label: __("AP Due Cluster (Áp lực đáo hạn nợ phải trả)"), value: "AP_DUE_CLUSTER" }
			],
			default: "AR_OVERDUE_SPIKE",
			change() {
				me.invalidate_requests(__("Signal changed — the previous result was cleared."));
			}
		});

		this.as_of_field = this.page.add_field({
			fieldname: "as_of_date",
			label: __("As-of Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			change() {
				me.invalidate_requests(__("Date changed — the previous result was cleared."));
			}
		});

		this.explanation_field = this.page.add_field({
			fieldname: "include_explanation",
			label: __("AI Explanation"),
			fieldtype: "Check",
			default: 1
		});

		// Navigation buttons
		this.page.add_inner_button(__("🤖 Lotus Copilot"), function () {
			frappe.set_route("lotus-copilot");
		});

		this.page.add_inner_button(__("📊 Sức khỏe tài chính"), function () {
			frappe.set_route("financial-health");
		});

		this.page.add_inner_button(__("💧 Dự báo dòng tiền"), function () {
			frappe.set_route("cash-forecast");
		});

		this.page.set_primary_action(__("Đánh giá Tín hiệu"), function () {
			me.evaluate();
		}, "octicon octicon-pulse");
	}

	setup_dom() {
		this.main = $(this.wrapper).find(".layout-main-section");
		this.main.children(":not(.page-form)").remove();

		this.container = document.createElement("div");
		this.container.className = "lotus-financial-health-container";
		this.container.style.maxWidth = "1180px";
		this.container.style.margin = "0 auto";

		// Header Card
		const headerCard = this.el("div", "lotus-fh-header-card");
		const headerFlex = this.el("div", "d-flex justify-content-between align-items-center");
		const headerLeft = this.el("div");

		const tagRow = this.el("div", "d-flex align-items-center gap-2 mb-2");
		tagRow.append(
			this.el("span", "lotus-brand-badge", "Lotus Fin • Risk Signal Agent (AI003)"),
			this.el("span", "lotus-badge lotus-badge-ai", "Deterministic Policy Engine")
		);

		const title = this.el("h1", "lotus-fh-title", "⚠️ " + __("Đánh giá & Nhận diện Tín hiệu Rủi ro"));
		const subtitle = this.el("p", "lotus-fh-subtitle", __("Phát hiện bất thường nợ quá hạn AR Spike và dồn cục nghĩa vụ trả nợ AP Cluster"));
		headerLeft.append(tagRow, title, subtitle);

		const headerRight = this.el("div", "text-right");
		headerRight.append(this.el("span", "lotus-badge lotus-badge-primary", "Standard Contract V2.2"));
		headerFlex.append(headerLeft, headerRight);
		headerCard.append(headerFlex);

		// Notice Banner
		const banner = this.el("div", "lotus-banner lotus-banner-warning mb-4");
		const bannerText = this.el("div");
		const bannerTitle = this.el("b", null, __("DEMO_ONLY — NOT APPROVED FOR PRODUCTION"));
		const bannerBody = this.el(
			"div",
			null,
			__("Chính sách AI003_DEMO_POLICY_V1 hoạt động theo tham số thử nghiệm. Ngưỡng cảnh báo và cửa sổ thời gian dùng cho mục đích trình diễn và không tạo hiệu lực pháp lý.")
		);
		bannerText.append(bannerTitle, bannerBody);
		banner.append(bannerText);

		// Glossary Card
		const glossaryCard = this.el("div", "lotus-card mb-4");
		glossaryCard.style.padding = "16px 24px";
		const glossaryHeader = this.el("div", "d-flex align-items-center gap-2 mb-2");
		glossaryHeader.append(
			this.el("span", null, "📖"),
			this.el("b", null, __("Quy ước mức độ kết quả đánh giá (Verdict Levels):"))
		);
		const glossaryPills = this.el("div", "d-flex flex-wrap gap-2");
		glossaryPills.append(
			this.el("span", "lotus-badge lotus-badge-success", "BENIGN: Không vượt ngưỡng rủi ro"),
			this.el("span", "lotus-badge lotus-badge-warning", "WATCH: Khuyến nghị theo dõi sát"),
			this.el("span", "lotus-badge lotus-badge-danger", "HIGH: Cần ưu tiên xử lý khẩn cấp"),
			this.el("span", "lotus-badge lotus-badge-neutral", "INCONCLUSIVE: Dữ liệu chưa đủ kết luận")
		);
		glossaryCard.append(glossaryHeader, glossaryPills);

		this.state_box = this.el("div", "rs-state mb-4");
		this.result_box = this.el("div", "rs-result");

		this.container.append(headerCard, banner, glossaryCard, this.state_box, this.result_box);
		this.main.append(this.container);
		this.show_empty();
	}

	setup_events() {
		this.main.attr("tabindex", "-1");
	}

	el(tag, className, text) {
		const node = document.createElement(tag);
		if (className) node.className = className;
		if (text !== undefined && text !== null) node.textContent = __(String(text));
		return node;
	}

	kv_row(label, value, className) {
		const row = this.el("div", "lotus-evidence-item d-flex justify-content-between align-items-center " + (className || ""));
		row.style.marginBottom = "8px";
		row.style.padding = "10px 16px";
		row.append(
			this.el("span", "text-muted", label),
			this.el("span", "font-weight-bold", value)
		);
		return row;
	}

	set_state(node) {
		this.state_box.innerHTML = "";
		if (node) this.state_box.append(node);
	}

	show_empty() {
		const box = this.el("div", "lotus-card text-center p-5");
		const icon = this.el("div", "mb-2", "🔍");
		icon.style.fontSize = "32px";
		box.append(icon);
		box.append(this.el("h3", "lotus-card-title justify-content-center mb-2", __("Chưa có kết quả đánh giá")));
		box.append(this.el("p", "text-muted mb-0",
			__("Chọn công ty, loại tín hiệu và ngày chốt số liệu, sau đó bấm <b>Đánh giá Tín hiệu</b> để hệ thống kích hoạt pipeline phân tích.")));
		this.set_state(box);
	}

	show_loading() {
		const box = this.el("div", "lotus-card text-center p-5");
		const icon = this.el("div", "mb-2", "⚡");
		icon.style.fontSize = "32px";
		box.append(icon);
		box.append(this.el("h3", "lotus-card-title justify-content-center mb-2", __("Đang chạy pipeline đánh giá...")));
		box.append(this.el("p", "text-muted mb-0", __("Hệ thống đang truy xuất chứng từ và áp dụng chính sách tất định. Không làm thay đổi dữ liệu.")));
		this.set_state(box);
		this.result_box.innerHTML = "";
	}

	clear_result(message) {
		this.result_box.innerHTML = "";
		if (message) {
			const note = this.el("div", "lotus-banner lotus-banner-info mb-4");
			note.append(this.el("div", null, message));
			this.result_box.append(note);
		} else {
			this.show_empty();
		}
	}

	invalidate_requests(message) {
		this.current_company = null;
		const had_in_flight = this.in_flight_request !== null;
		this.in_flight_request = null;
		if (had_in_flight) {
			this.in_flight = false;
			this.restore_primary_action();
			this.set_state(null);
		}
		this.clear_result(message);
	}

	reason_text(code) {
		const map = {
			ACCESS_DENIED: __("Bạn không có quyền truy cập công ty hoặc báo cáo được yêu cầu."),
			UNAUTHORIZED_ACCESS: __("Phiên làm việc chưa được xác thực."),
			INVALID_REQUEST: __("Yêu cầu không hợp lệ. Vui lòng kiểm tra lại công ty, tín hiệu và ngày chốt."),
			FUTURE_AS_OF: __("Ngày chốt không được nằm trong tương lai."),
			UNSUPPORTED_CURRENCY: __("Phiên bản hiện tại chỉ hỗ trợ đơn vị tiền tệ VND."),
			UNSUPPORTED_COMPANY_CURRENCY: __("Đơn vị tiền tệ kế toán của công ty không phải VND."),
			FINANCE_BOOK_NOT_SUPPORTED: __("Chưa hỗ trợ phạm vi Sổ tài chính (Finance Book)."),
			HISTORY_INSUFFICIENT: __("Không tìm thấy dữ liệu tháng trước của công ty để so sánh đường cơ sở."),
			BASELINE_DENOMINATOR_INVALID: __("Tháng trước có số dư nợ phải thu bằng 0, không xác định được tỷ lệ cơ sở."),
			CURRENT_DENOMINATOR_INVALID: __("Tại thời điểm chốt, số dư nợ phải thu bằng 0."),
			ZERO_DENOMINATOR: __("Không có số dư nợ phải trả tương lai tại thời điểm này."),
			INVALID_DENOMINATOR: __("Mẫu số tính toán không hợp lệ."),
			INCOMPLETE_DUE_DATE_COVERAGE: __("Hóa đơn thiếu thông tin hạn thanh toán."),
			UNSUPPORTED_ALLOCATION_SCOPE: __("Hóa đơn phân bổ qua nhiều tài khoản phức tạp."),
			UNSUPPORTED_MULTI_SCHEDULE: __("Hóa đơn có nhiều đợt trả góp phức tạp."),
			CONFLICTING_OBSERVATION: __("Nguồn dữ liệu trả về các dòng mâu thuẫn."),
			INCONSISTENT_DATA: __("Dữ liệu nguồn không nhất quán."),
			SOURCE_UNAVAILABLE: __("Nguồn dữ liệu kế toán tạm thời không khả dụng."),
			SOURCE_TIMEOUT: __("Thời gian phản hồi từ nguồn dữ liệu quá lâu."),
			SOURCE_INVALID: __("Dữ liệu từ nguồn bị lỗi cấu trúc."),
			UNSUPPORTED_SOURCE_VERSION: __("Phiên bản hợp đồng dữ liệu nguồn không khớp."),
			POLICY_NOT_APPROVED: __("Chính sách rủi ro tương ứng chưa được phê duyệt."),
			POLICY_UNAVAILABLE: __("Không thể truy xuất chính sách rủi ro."),
			INVALID_POLICY_CONFIG: __("Cấu hình chính sách rủi ro bị lỗi.")
		};
		return map[code] || __("Đánh giá dừng lại với mã nguyên nhân: " + code);
	}

	status_label(status) {
		const map = {
			OK: __("Đánh giá hoàn tất"),
			INCONCLUSIVE: __("Chưa thể kết luận"),
			FORBIDDEN: __("Từ chối truy cập"),
			VALIDATION_ERROR: __("Cần kiểm tra"),
			SOURCE_ERROR: __("Lỗi nguồn dữ liệu"),
			POLICY_PENDING: __("Chờ phê duyệt chính sách")
		};
		return map[status] || status;
	}

	evaluate() {
		const me = this;
		if (this.in_flight) return;

		const company_input = this.company_field.$input ? this.company_field.$input.val() : null;
		const company = company_input
			|| (company_input === "" ? "" : (this.company_field.get_value() || this.last_typed_company));
		const signal_id = this.signal_field.get_value();
		const date_input = this.as_of_field.$input ? this.as_of_field.$input.val() : null;
		const as_of_date = date_input || (date_input === "" ? "" : this.as_of_field.get_value());
		
		if (!company) {
			this.clear_result(__("Vui lòng chọn công ty cần đánh giá."));
			return;
		}
		if (!as_of_date) {
			this.clear_result(__("Vui lòng chọn ngày chốt đánh giá."));
			return;
		}
		
		this.current_company = company;
		const seq = ++this.request_seq;
		this.in_flight_request = seq;
		this.in_flight = true;
		this.page.set_primary_action(__("Đang đánh giá…"), function () {}, "octicon octicon-sync");
		this.show_loading();

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_risk_signal",
			args: {
				company: company,
				signal_id: signal_id,
				as_of_date: as_of_date,
				include_explanation: this.explanation_field.get_value() ? 1 : 0
			},
			type: "POST"
		})
			.then(function (r) {
				if (me.in_flight_request !== seq) return;
				me.in_flight = false;
				me.in_flight_request = null;
				me.restore_primary_action();
				me.render_result(r.message || r);
			})
			.fail(function () {
				if (me.in_flight_request !== seq) return;
				me.in_flight = false;
				me.in_flight_request = null;
				me.restore_primary_action();
				me.render_transport_error();
			});
	}

	restore_primary_action() {
		const me = this;
		this.page.set_primary_action(__("Đánh giá Tín hiệu"), function () {
			me.evaluate();
		}, "octicon octicon-pulse");
	}

	render_transport_error() {
		const box = this.el("div", "lotus-banner lotus-banner-danger mb-4");
		box.append(this.el("h5", "mb-1", __("Lỗi kết nối")));
		box.append(this.el("div", null,
			__("Yêu cầu đánh giá không thể gửi tới máy chủ (Transport error). Dữ liệu được bảo toàn an toàn.")));
		this.set_state(box);
	}

	render_result(wire) {
		this.set_state(null);
		this.result_box.innerHTML = "";
		if (!wire || !wire.status) {
			this.render_transport_error();
			return;
		}

		const panel = this.el("div", "lotus-card mb-4");
		panel.append(this.render_status_header(wire));
		panel.append(this.render_reason(wire));

		if (wire.status === "FORBIDDEN") {
			this.result_box.append(panel);
			return;
		}

		if (wire.status === "OK") panel.append(this.render_evaluation(wire));
		panel.append(this.render_counts(wire));
		panel.append(this.render_materiality(wire));
		panel.append(this.render_evidence(wire));
		panel.append(this.render_explanation(wire));
		panel.append(this.render_limitations(wire));
		panel.append(this.render_next_actions(wire));
		
		const debug = this.render_debug(wire);
		if (debug) panel.append(debug);

		this.result_box.append(panel);
	}

	render_status_header(wire) {
		const header = this.el("div", "d-flex flex-wrap align-items-center gap-2 mb-4 pb-3");
		header.style.borderBottom = "1px solid var(--lotus-border)";

		const statusClass = {
			OK: "lotus-badge-primary",
			INCONCLUSIVE: "lotus-badge-neutral",
			FORBIDDEN: "lotus-badge-danger",
			VALIDATION_ERROR: "lotus-badge-warning",
			SOURCE_ERROR: "lotus-badge-danger",
			POLICY_PENDING: "lotus-badge-neutral"
		}[wire.status] || "lotus-badge-neutral";

		header.append(this.el("span", "lotus-badge " + statusClass, this.status_label(wire.status)));

		if (wire.status === "OK" && wire.finding === "TRIGGERED" && wire.severity) {
			const sevClass = wire.severity === "HIGH" ? "lotus-badge-danger" : "lotus-badge-warning";
			header.append(this.el("span", "lotus-badge " + sevClass, wire.severity === "HIGH" ? "🚨 " + __("MỨC ĐỘ: CAO (HIGH)") : "⚠️ " + __("MỨC ĐỘ: THEO DÕI (WATCH)")));
		}
		if (wire.status === "OK" && wire.finding === "BENIGN") {
			header.append(this.el("span", "lotus-badge lotus-badge-success", "🛡️ " + __("BENIGN — AN TOÀN (Không vi phạm ngưỡng)")));
		}
		if (wire.as_of_date) {
			header.append(this.el("span", "text-muted", __("Ngày chốt: {0}", [wire.as_of_date])));
		}
		if (wire.signal_id) {
			header.append(this.el("span", "lotus-code-badge", wire.signal_id === "AR_OVERDUE_SPIKE" ? "Tín hiệu AR Overdue Spike" : "Tín hiệu AP Due Cluster"));
		}
		return header;
	}

	render_reason(wire) {
		const box = this.el("div", "mb-4");
		box.append(this.el("h4", "lotus-card-title mb-2", "🔍 " + __("Lý do & Nguyên nhân kết luận:")));
		const reasonBox = this.el("div", "p-3 rounded-xl", this.reason_text(wire.reason_code));
		reasonBox.style.background = "var(--lotus-surface-app)";
		reasonBox.style.border = "1px solid var(--lotus-border)";
		box.append(reasonBox);
		return box;
	}

	render_evaluation(wire) {
		const box = this.el("div", "mb-4");
		box.append(this.el("h4", "lotus-card-title mb-3", "📊 " + __("Chi tiết Chỉ số Đo lường (Observed Metrics):")));
		
		if (wire.signal_id === "AR_OVERDUE_SPIKE") {
			box.append(this.kv_row(__("Tỷ lệ nợ quá hạn hiện tại (Current Overdue Ratio)"), wire.observed ? wire.observed.value : null));
			box.append(this.kv_row(__("Tỷ lệ nợ quá hạn đường cơ sở (Baseline {0})", [wire.baseline ? wire.baseline.cutoff : ""]), wire.baseline ? wire.baseline.value : null));
			box.append(this.kv_row(__("Mức tăng điểm phần trăm (Δ Delta)"), wire.delta_pp !== null && wire.delta_pp !== undefined ? wire.delta_pp + " pp" : null));
			box.append(this.kv_row(__("Tổng giá trị nợ phải thu thuần (Net AR)"), wire.observed ? wire.observed.supporting_amount : null));
			box.append(this.kv_row(__("Ngưỡng kích hoạt chính sách (Demo Policy)"),
				wire.rule ? wire.rule.threshold + " / " + wire.rule.high_threshold + " pp (WATCH / HIGH)" : null));
		} else {
			let pct = null;
			if (wire.observed && wire.observed.value !== null && wire.observed.value !== undefined) {
				pct = (parseFloat(wire.observed.value) * 100).toFixed(2) + "%";
			}
			box.append(this.kv_row(__("Tỷ trọng nợ phải trả đáo hạn trong cửa sổ"), pct));
			box.append(this.kv_row(__("Tổng tiền đáo hạn trong cửa sổ (N)"), wire.observed ? wire.observed.supporting_amount : null));
			box.append(this.kv_row(__("Tổng nợ phải trả tương lai (D)"), wire.numerator_denominator_detail || null));
			box.append(this.kv_row(__("Ngưỡng kích hoạt chính sách"),
				wire.rule ? (parseFloat(wire.rule.threshold) * 100).toFixed(1) + "% / " + (parseFloat(wire.rule.high_threshold) * 100).toFixed(1) + "% (WATCH / HIGH)" : null));
			if (wire.rule && wire.rule.window_start && wire.rule.window_end) {
				box.append(this.kv_row(__("Cửa sổ đáo hạn"), wire.rule.window_start + " → " + wire.rule.window_end));
			}
		}
		return box;
	}

	render_counts(wire) {
		if (wire.count_positive_vouchers === null || wire.count_positive_vouchers === undefined) return document.createDocumentFragment();
		const box = this.el("div", "mb-4");
		box.append(this.kv_row(__("Số lượng chứng từ phải trả tương lai"), String(wire.count_positive_vouchers)));
		if (wire.count_due_vouchers !== null && wire.count_due_vouchers !== undefined) {
			box.append(this.kv_row(__("Số chứng từ rơi vào cửa sổ đáo hạn"), String(wire.count_due_vouchers)));
		}
		return box;
	}

	render_materiality(wire) {
		if (!wire.rule || wire.rule.floor === null || wire.rule.floor === undefined) return document.createDocumentFragment();
		const box = this.el("div", "mb-4");
		const definitionLabel = wire.rule.materiality_definition === "CURRENT_NET_AR_TOTAL"
			? __("tổng nợ phải thu thuần")
			: __("số tiền đáo hạn trong cửa sổ");
		const floorText = parseFloat(wire.rule.floor) === 0
			? __("0.00 VND (Không áp dụng lọc trọng yếu)")
			: wire.rule.floor + " VND";
		box.append(this.kv_row(__("Ngưỡng giá trị trọng yếu (Materiality Floor)"), floorText));
		box.append(this.el("div", "text-muted mt-1",
			__("Ngưỡng trọng yếu áp dụng cho {0}.", [definitionLabel])));
		return box;
	}

	render_evidence(wire) {
		const me = this;
		const box = this.el("div", "mb-4");
		box.append(this.el("h4", "lotus-card-title mb-2", "🧾 " + __("Bằng chứng Snapshot (Evidence Ref):")));
		const refs = wire.evidence || [];
		if (!refs.length) {
			box.append(this.el("div", "text-muted",
				__("Không có bằng chứng snapshot đính kèm.")));
			return box;
		}
		const note = this.el("div", "text-muted mb-2",
			__("Mỗi lần mở snapshot, hệ thống sẽ tái xác thực quyền truy cập trên máy chủ theo cơ chế Zero-Trust."));
		box.append(note);
		
		const btnRow = this.el("div", "d-flex flex-wrap gap-2");
		refs.forEach(function (ref) {
			const btn = me.el("button", "lotus-btn lotus-btn-secondary lotus-btn-sm");
			btn.type = "button";
			btn.textContent = `📋 Xem snapshot (${ref.kind} · ${ref.as_of_date || ""})`;
			btn.addEventListener("click", function () {
				me.open_evidence(ref.ref);
			});
			btnRow.append(btn);
		});
		box.append(btnRow);
		return box;
	}

	open_evidence(ref) {
		const me = this;
		frappe.call({
			method: "lotus_fin.api.ai_insights.get_risk_signal_evidence",
			args: { evidence_ref: ref, company: this.current_company },
			type: "POST"
		})
			.then(function (r) {
				const res = r.message || r;
				const box = me.el("div", "lotus-banner " + (res.status === "MATCH" ? "lotus-banner-success" : res.status === "FORBIDDEN" ? "lotus-banner-danger" : "lotus-banner-warning") + " mt-3");
				const label = {
					MATCH: __("Bằng chứng đã đối chiếu khớp 100%: Nguồn dữ liệu không bị thay đổi kể từ lúc chụp snapshot (MATCH)."),
					RESTATED: __("Dữ liệu nguồn đã thay đổi sau thời điểm chụp snapshot (RESTATED)."),
					UNAVAILABLE: __("Nguồn dữ liệu tạm thời không thể phát lại (UNAVAILABLE)."),
					FORBIDDEN: __("Từ chối quyền truy cập bằng chứng (FORBIDDEN).")
				}[res.status] || res.status;
				box.append(me.el("b", "d-block mb-2", label));
				if (res.payload) {
					const keys = Object.keys(res.payload);
					keys.forEach(function (key) {
						box.append(me.kv_row(key, String(res.payload[key])));
					});
				}
				const existing = me.result_box.querySelector(".rs-evidence-live");
				if (existing) existing.remove();
				box.classList.add("rs-evidence-live");
				me.result_box.append(box);
			})
			.fail(function () {
				frappe.msgprint(__("Không thể phát lại bằng chứng (Transport error)."));
			});
	}

	render_explanation(wire) {
		const box = this.el("div", "mb-4");
		const exp = wire.explanation || {};
		if (exp.status === "AVAILABLE" && exp.text) {
			box.append(this.el("h4", "lotus-card-title mb-2", "🤖 " + __("Giải thích & Diễn giải AI:")));
			const expCard = this.el("div", "p-3 rounded-xl", exp.text);
			expCard.style.background = "linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(37, 99, 235, 0.03) 100%)";
			expCard.style.borderLeft = "4px solid var(--lotus-ai-magic)";
			expCard.style.lineHeight = "1.6";
			box.append(expCard);
		} else if (exp.status === "UNAVAILABLE") {
			box.append(this.el("div", "lotus-banner lotus-banner-warning",
				this.el("div", null, __("Diễn giải AI không khả dụng. Kết quả tất định phía trên vẫn hoàn toàn chính xác."))));
		}
		return box;
	}

	render_limitations(wire) {
		const lims = wire.limitations || [];
		if (!lims.length) return document.createDocumentFragment();
		const box = this.el("div", "mb-4");
		box.append(this.el("h4", "lotus-card-title mb-2", "⚠️ " + __("Giới hạn Phạm vi (Limitations):")));
		lims.forEach((lim) => {
			box.append(this.el("div", "text-muted mb-1", "• " + lim));
		});
		return box;
	}

	render_next_actions(wire) {
		const actions = wire.next_check_actions || [];
		if (!actions.length) return document.createDocumentFragment();
		const box = this.el("div", "mb-4");
		box.append(this.el("h4", "lotus-card-title mb-2", "🎯 " + __("Khuyến nghị Hành động Tiếp theo:")));
		const actionList = this.el("div", "d-flex flex-column gap-2");
		actions.forEach(function (action) {
			const item = document.createElement("div");
			item.className = "lotus-evidence-item d-flex align-items-center gap-2 mb-0";
			const bullet = document.createElement("span");
			bullet.textContent = "👉 ";
			const text = document.createElement("span");
			text.className = "font-weight-bold";
			text.textContent = __(action);
			item.append(bullet, text);
			actionList.append(item);
		});
		box.append(actionList);
		return box;
	}

	render_debug(wire) {
		const trace = wire.stage_trace || [];
		if (!trace.length) return document.createDocumentFragment();
		const box = this.el("div", "text-muted pt-3");
		box.style.borderTop = "1px dashed var(--lotus-border)";
		box.style.fontSize = "11px";
		box.append(this.el("span", null,
			__("Pipeline trace: {0} · policy {1} · method {2}", [trace.join(" → "), wire.policy_version || "—", wire.method_version || "—"])));
		return box;
	}
};
