// Lotus Fin Unified Desk Bundle & Client Extensions (Google Material 3 DNA)
frappe.provide("lotus_fin");
frappe.provide("lotus_fin.core");
frappe.provide("lotus_fin.core.api");
frappe.provide("lotus_fin.ui");
frappe.provide("lotus_fin.widgets");
frappe.provide("lotus_fin.components");

// ============================================================================
// Core Utilities
// ============================================================================
lotus_fin.core.cn = function (...classes) {
	return classes.filter(Boolean).join(" ");
};

lotus_fin.core.format_currency = function (value, currency = "VND") {
	if (value === null || value === undefined || isNaN(value)) {
		return "—";
	}
	return frappe.format(value, { fieldtype: "Currency", currency: currency });
};

lotus_fin.core.format_percent = function (value, decimals = 1) {
	if (value === null || value === undefined || isNaN(value)) {
		return "—";
	}
	const pct = value > 1 ? value : value * 100;
	return `${pct.toFixed(decimals)}%`;
};

lotus_fin.core.api.call = function (method, args = {}) {
	return new Promise((resolve, reject) => {
		frappe.call({
			method: method,
			args: args,
			callback: function (r) {
				if (r.exc) reject(new Error(r.exc));
				else resolve(r.message);
			},
			error: function (err) {
				reject(err);
			}
		});
	});
};

// ============================================================================
// UI Primitives: Button, Card, Badge, MetricCard, Table, Input
// ============================================================================
lotus_fin.ui.Button = class Button {
	constructor(opts = {}) {
		this.label = opts.label || "";
		this.variant = opts.variant || "primary";
		this.size = opts.size || "md";
		this.icon = opts.icon || "";
		this.onClick = opts.onClick || null;
		this.className = opts.className || "";
		this.isLoading = false;
		this.render();
		this.bind_events();
	}

	render() {
		const variantClass = `lotus-btn-${this.variant}`;
		const sizeClass = this.size !== "md" ? `lotus-btn-${this.size}` : "";
		const iconHtml = this.icon ? `<span class="lotus-btn-icon mr-1">${this.icon}</span>` : "";

		this.$el = $(`
			<button class="lotus-btn ${variantClass} ${sizeClass} ${this.className}">
				${iconHtml}
				<span class="lotus-btn-label">${this.label}</span>
			</button>
		`);
	}

	bind_events() {
		if (this.onClick) {
			this.$el.on("click", (e) => {
				if (!this.isLoading) {
					this.onClick(e, this);
				}
			});
		}
	}

	set_loading(loading = true, loadingText = "Đang xử lý...") {
		this.isLoading = loading;
		this.$el.prop("disabled", loading);
		if (loading) {
			this.$el.find(".lotus-btn-label").html(`<i class="octicon octicon-sync"></i> ${loadingText}`);
		} else {
			this.$el.find(".lotus-btn-label").text(this.label);
		}
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};

lotus_fin.ui.Card = class Card {
	constructor(opts = {}) {
		this.title = opts.title || "";
		this.subtitle = opts.subtitle || "";
		this.badge = opts.badge || "";
		this.className = opts.className || "";
		this.content = opts.content || "";
		this.render();
	}

	render() {
		let headerHtml = "";
		if (this.title || this.badge) {
			const badgeHtml = this.badge ? `<span class="lotus-badge lotus-badge-primary">${this.badge}</span>` : "";
			const subHtml = this.subtitle ? `<p class="lotus-card-subtitle">${this.subtitle}</p>` : "";
			headerHtml = `
				<div class="lotus-card-header">
					<div>
						<h3 class="lotus-card-title">${this.title}</h3>
						${subHtml}
					</div>
					<div>${badgeHtml}</div>
				</div>
			`;
		}

		this.$el = $(`
			<div class="lotus-card ${this.className}">
				${headerHtml}
				<div class="lotus-card-body"></div>
			</div>
		`);

		this.$body = this.$el.find(".lotus-card-body");
		if (this.content) {
			this.$body.append(this.content);
		}
	}

	set_content(content) {
		this.$body.empty().append(content);
		return this;
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};

lotus_fin.ui.Badge = class Badge {
	constructor(opts = {}) {
		this.text = opts.text || "";
		this.variant = opts.variant || "primary";
		this.icon = opts.icon || "";
		this.render();
	}

	render() {
		const iconHtml = this.icon ? `<span class="mr-1">${this.icon}</span>` : "";
		this.$el = $(`
			<span class="lotus-badge lotus-badge-${this.variant}">
				${iconHtml}
				<span>${this.text}</span>
			</span>
		`);
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};

lotus_fin.ui.MetricCard = class MetricCard {
	constructor(opts = {}) {
		this.label = opts.label || "";
		this.value = opts.value || "—";
		this.subtext = opts.subtext || "";
		this.delta = opts.delta || "";
		this.deltaType = opts.deltaType || "neutral";
		this.valueColor = opts.valueColor || "primary";
		this.className = opts.className || "";
		this.render();
	}

	render() {
		let colorStyle = "color: #0f172a;";
		if (this.valueColor === "success") colorStyle = "color: #16a34a;";
		else if (this.valueColor === "warning") colorStyle = "color: #ea580c;";
		else if (this.valueColor === "danger") colorStyle = "color: #dc2626;";
		else if (this.valueColor === "primary") colorStyle = "color: #2563eb;";

		let deltaHtml = "";
		if (this.delta) {
			const deltaColor = this.deltaType === "positive" ? "text-success" : (this.deltaType === "negative" ? "text-danger" : "text-muted");
			deltaHtml = `<span class="${deltaColor} font-weight-bold ml-1">${this.delta}</span>`;
		}

		this.$el = $(`
			<div class="lotus-metric-card ${this.className}">
				<div class="lotus-metric-label">${this.label}</div>
				<div class="lotus-metric-value" style="${colorStyle}">${this.value}</div>
				<div class="lotus-metric-meta">
					<span>${this.subtext}</span>
					${deltaHtml}
				</div>
			</div>
		`);
	}

	set_value(val) {
		this.value = val;
		this.$el.find(".lotus-metric-value").text(val);
		return this;
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};

lotus_fin.ui.Table = class Table {
	constructor(opts = {}) {
		this.columns = opts.columns || [];
		this.data = opts.data || [];
		this.emptyMessage = opts.emptyMessage || "Không có dữ liệu hiển thị";
		this.render();
	}

	render() {
		let thHtml = "";
		this.columns.forEach(col => {
			const alignClass = col.align ? `text-${col.align}` : "text-left";
			thHtml += `<th class="${alignClass}">${col.label}</th>`;
		});

		this.$el = $(`
			<div class="lotus-table-container">
				<table class="lotus-table">
					<thead>
						<tr>${thHtml}</tr>
					</thead>
					<tbody class="lotus-table-tbody"></tbody>
				</table>
			</div>
		`);

		this.$tbody = this.$el.find(".lotus-table-tbody");
		this.render_rows(this.data);
	}

	render_rows(data) {
		this.data = data || [];
		this.$tbody.empty();

		if (!this.data.length) {
			this.$tbody.append(`
				<tr>
					<td colspan="${this.columns.length}" class="text-center py-4 text-muted">
						${this.emptyMessage}
					</td>
				</tr>
			`);
			return;
		}

		this.data.forEach((row, rowIdx) => {
			let tdHtml = "";
			this.columns.forEach(col => {
				const alignClass = col.align ? `text-${col.align}` : "text-left";
				let val = row[col.key];
				if (typeof col.format === "function") {
					val = col.format(val, row, rowIdx);
				} else if (val === null || val === undefined) {
					val = "—";
				}
				tdHtml += `<td class="${alignClass}">${val}</td>`;
			});
			this.$tbody.append(`<tr>${tdHtml}</tr>`);
		});
	}

	set_data(data) {
		this.render_rows(data);
		return this;
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};

// ============================================================================
// Component 1: ChatCopilot (Lotus Fin AI Natural Language Copilot)
// ============================================================================
lotus_fin.components.ChatCopilot = class ChatCopilot {
	constructor(opts) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"));
		this.title = opts.title || __("Lotus Fin AI Copilot — Đối thoại & Điều phối Nghiệp vụ");
		this.badge = opts.badge || __("Deterministic Tool Calling • Real-time Accounting Data");
		this.min_height = opts.min_height || "480px";
		this.show_quick_pills = opts.show_quick_pills !== false;
		this.chat_history = [];
		this.render();
		this.bind_events();
		this.init_chat();
	}

	render() {
		const quickPillsHtml = this.show_quick_pills ? `
			<div class="mb-3">
				<span class="text-muted" style="font-size: 11px; font-weight: 600;">💡 Gợi ý câu hỏi nhanh (AI001 - AI007):</span>
				<div class="mt-1 d-flex flex-wrap gap-1">
					<span class="lotus-quick-pill" data-query="Sức khỏe tài chính năm nay của công ty thế nào?">📊 Sức khỏe tài chính (F001)</span>
					<span class="lotus-quick-pill" data-query="Dự báo dòng tiền 30 ngày tới và các mốc thâm hụt">💧 Dự báo dòng tiền (F002)</span>
					<span class="lotus-quick-pill" data-query="Kiểm tra tín hiệu rủi ro nợ quá hạn AR spike và AP cluster">⚠️ Tín hiệu rủi ro (F003)</span>
					<span class="lotus-quick-pill" data-query="Nếu doanh thu giảm 20% và khách nợ trễ 15 ngày thì dòng tiền thế nào?">🔮 What-If: Doanh thu -20%, nợ trễ 15 ngày (F004)</span>
					<span class="lotus-quick-pill" data-query="Tư vấn vay 1 tỷ vốn lưu động 12 tháng có gói nào phù hợp?">🏦 Tư vấn gói vay 1 tỷ (F005)</span>
					<span class="lotus-quick-pill" data-query="Lập lịch trả nợ vay 1 tỷ lãi 8.5% trong 12 tháng và sốc lãi suất tăng 200 bps">📑 Lập lịch trả nợ & Sốc lãi suất (F006)</span>
				</div>
			</div>
		` : "";

		this.$el = $(`
			<div class="lotus-section-card lotus-copilot-card">
				<div class="d-flex justify-content-between align-items-center mb-2">
					<div class="lotus-section-title mb-0">
						<span style="font-size: 16px;">🤖 <b>${this.title}</b></span>
						<span class="lotus-ai-badge">${this.badge}</span>
					</div>
					<button class="lotus-btn-secondary btn-clear-chat" style="font-size: 11px; padding: 4px 12px;" title="${__("Xóa lịch sử trò chuyện")}">
						🗑️ ${__("Làm mới chat")}
					</button>
				</div>
				<p class="text-muted" style="font-size: 13px; margin-bottom: 14px; line-height: 1.5;">
					${__("Hỏi đáp bằng ngôn ngữ tự nhiên. AI hoạt động theo cơ chế <b>Agentic Tool Calling</b>: hiểu ngữ cảnh, gọi các công cụ tài chính chuyên sâu (F001 Sức khỏe, F002 Dòng tiền, F003 Rủi ro, F004 What-If, F005 Vay vốn, F006 Trả nợ) để tính toán chính xác và giải thích minh bạch.")}
				</p>
				${quickPillsHtml}
				<div class="lotus-chat-container">
					<div class="lotus-chat-thread" style="min-height: ${this.min_height}; max-height: 520px; overflow-y: auto;">
						<!-- Messages dynamically rendered here -->
					</div>
					<div class="lotus-chat-input-bar">
						<input type="text" class="lotus-copilot-input input-copilot-query" placeholder="${__("Nhập câu hỏi tài chính bằng ngôn ngữ tự nhiên (Ví dụ: Doanh thu năm nay bao nhiêu? Tư vấn gói vay 1 tỷ?)...")}" />
						<button class="lotus-chat-send-btn btn-ask-copilot">
							<span>🚀 ${__("Gửi")}</span>
						</button>
					</div>
				</div>
			</div>
		`);

		this.parent.append(this.$el);
		this.$thread = this.$el.find(".lotus-chat-thread");
		this.$input = this.$el.find(".input-copilot-query");
		this.$sendBtn = this.$el.find(".btn-ask-copilot");
	}

	bind_events() {
		const me = this;
		this.$el.on("click", ".lotus-quick-pill", function () {
			const q = $(this).attr("data-query");
			me.$input.val(q);
			me.send_message(q);
		});

		this.$sendBtn.on("click", function () {
			const q = me.$input.val();
			if (q && q.trim()) {
				me.send_message(q.trim());
			}
		});

		this.$input.on("keypress", function (e) {
			if (e.which === 13) {
				const q = $(this).val();
				if (q && q.trim()) {
					me.send_message(q.trim());
				}
			}
		});

		this.$el.on("click", ".btn-clear-chat", function () {
			me.init_chat(true);
		});
	}

	init_chat(reset = false) {
		if (reset || !this.chat_history || this.chat_history.length === 0) {
			this.chat_history = [];
			this.$thread.empty();
			const welcome = `
				<div class="lotus-chat-msg copilot">
					<div class="lotus-msg-bubble">
						<div class="d-flex align-items-center mb-1">
							<span style="font-size: 16px; margin-right: 6px;">🤖</span>
							<b style="color: #0369a1;">Lotus Fin AI Copilot</b>
						</div>
						<div>
							Xin chào! Tôi là trợ lý tài chính thông minh của bạn. Tôi hoạt động theo cơ chế <b>Agentic Tool Calling</b>: Tôi hiểu câu hỏi bằng ngôn ngữ tự nhiên và tự động điều phối các công cụ kế toán chuyên sâu (không tự bịa số liệu):
							<ul class="mb-0 mt-2 pl-3" style="line-height: 1.6;">
								<li><b>F001 Sức khỏe tài chính:</b> Doanh thu, giá vốn, lãi gộp, số dư tiền mặt, công nợ AR/AP.</li>
								<li><b>F002 Dự báo dòng tiền:</b> Quỹ đạo tiền mặt 30 ngày và nguy cơ thiếu hụt.</li>
								<li><b>F003 Tín hiệu rủi ro:</b> Giám sát đột biến nợ quá hạn và áp lực thanh toán dồn ứ.</li>
								<li><b>F004 Mô phỏng What-If:</b> Stress-test khi doanh số biến động hoặc khách hàng trả chậm.</li>
								<li><b>F005 Tư vấn giải pháp vay:</b> Đối chiếu gói tín dụng ngân hàng theo điều kiện doanh nghiệp.</li>
								<li><b>F006 Lập lịch trả nợ:</b> Tính toán lịch trả gốc lãi và kiểm tra khả năng chịu đựng khi sốc lãi suất (+bps).</li>
							</ul>
						</div>
					</div>
				</div>
			`;
			this.$thread.append(welcome);
		}
	}

	send_message(query) {
		const me = this;
		const company = this.get_company();
		if (!company) {
			frappe.msgprint(__("Vui lòng chọn công ty trước khi trò chuyện với AI Copilot."));
			return;
		}
		if (!query || !query.trim()) return;

		const q = query.trim();
		const userMsgHtml = `
			<div class="lotus-chat-msg user">
				<div class="lotus-msg-bubble">${frappe.utils.escape_html(q)}</div>
			</div>
		`;
		this.$thread.append(userMsgHtml);
		this.$input.val("");
		this.$sendBtn.prop("disabled", true);

		const loadingHtml = `
			<div id="lotus-chat-loading" class="lotus-chat-msg copilot">
				<div class="lotus-msg-bubble">
					<span class="lotus-chat-loading-dots">
						<i class="octicon octicon-sync"></i> 
						<span>Đang phân tích ý định và kích hoạt công cụ kế toán...</span>
					</span>
				</div>
			</div>
		`;
		this.$thread.append(loadingHtml);
		this.$thread.scrollTop(this.$thread[0].scrollHeight);

		frappe.call({
			method: "lotus_fin.api.ai_insights.chat_copilot",
			args: {
				query: q,
				company: company,
				as_of_date: frappe.datetime.get_today() || "2026-12-31"
			},
			callback(r) {
				me.$thread.find("#lotus-chat-loading").remove();
				me.$sendBtn.prop("disabled", false);

				if (r.exc || !r.message) {
					me.append_copilot_msg({
						reply: "Rất tiếc, máy chủ phản hồi lỗi khi xử lý câu hỏi. Vui lòng thử lại sau.",
						tool_called: null
					});
					return;
				}

				const res = r.message;
				me.append_copilot_msg(res);
				me.$thread.scrollTop(me.$thread[0].scrollHeight);
			},
			error() {
				me.$thread.find("#lotus-chat-loading").remove();
				me.$sendBtn.prop("disabled", false);
				me.append_copilot_msg({
					reply: "Không thể kết nối tới dịch vụ AI Copilot. Vui lòng kiểm tra kết nối mạng.",
					tool_called: null
				});
				me.$thread.scrollTop(me.$thread[0].scrollHeight);
			}
		});
	}

	append_copilot_msg(res) {
		const toolCalled = res.tool_called;
		const toolLabel = res.tool_label || toolCalled;
		const replyText = res.reply || "";

		let toolBadgeHtml = "";
		if (toolCalled) {
			toolBadgeHtml = `
				<div class="lotus-chat-tool-badge">
					<span>⚙️</span>
					<span>Đã chạy công cụ: <b>${frappe.utils.escape_html(toolLabel)}</b> (<code>${frappe.utils.escape_html(toolCalled)}</code>)</span>
				</div>
			`;
		}

		let widgetHtml = "";
		if (res.tool_output && toolCalled) {
			widgetHtml = this.render_tool_output_widget(toolCalled, res.tool_output);
		}

		const formattedReply = this.format_markdown(replyText);

		const msgHtml = `
			<div class="lotus-chat-msg copilot">
				<div class="lotus-msg-bubble">
					${toolBadgeHtml}
					<div>${formattedReply}</div>
					${widgetHtml}
				</div>
			</div>
		`;
		this.$thread.append(msgHtml);
	}

	render_tool_output_widget(toolName, output) {
		// F006: Repayment Schedule Widget
		if (toolName === "calculate_repayment_schedule" && output.monthly_payment) {
			const pmtStr = frappe.format(output.monthly_payment, { fieldtype: "Currency", currency: "VND" });
			const intStr = frappe.format(output.total_interest, { fieldtype: "Currency", currency: "VND" });
			const shockHtml = output.shock_bps > 0 ? `
				<div class="mt-1 text-danger font-weight-bold" style="font-size: 11px;">
					⚠️ Sốc lãi (+${output.shock_bps} bps): Chi phí lãi tăng thêm +${frappe.format(output.shock_added_interest, { fieldtype: "Currency", currency: "VND" })}
				</div>
			` : "";

			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center">
						<b>📑 Tóm tắt Kế hoạch Trả nợ:</b>
						<a href="/desk/repayment-schedule" class="badge badge-light" style="border: 1px solid #cbd5e1;">Mở Studio &rarr;</a>
					</div>
					<div class="row mt-2" style="font-size: 12px;">
						<div class="col-6">Trả hàng tháng: <b class="text-primary">${pmtStr}</b></div>
						<div class="col-6">Tổng tiền lãi: <b class="text-warning">${intStr}</b></div>
					</div>
					${shockHtml}
				</div>
			`;
		}

		// F005: Financing Products Widget
		if (toolName === "match_financing_products" && output.matched_products) {
			const prods = output.matched_products.slice(0, 3);
			if (!prods.length) return "";
			let cards = "";
			prods.forEach((p, idx) => {
				const rate = (p.nominal_rate_annual * 100).toFixed(1);
				const interest = frappe.format(p.estimated_monthly_interest, { fieldtype: "Currency", currency: "VND" });
				cards += `
					<div class="lotus-product-card ${idx === 0 ? 'top-recommended' : ''} mb-2 p-2" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px;">
						<div class="d-flex justify-content-between align-items-center">
							<b>${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
							<span class="badge badge-success">${p.match_score}/100</span>
						</div>
						<div class="mt-1 text-muted" style="font-size: 11px;">
							Lãi suất: <b class="text-success">${rate}%/năm</b> &bull; Lãi tạm tính: <b>~${interest}/tháng</b> &bull; Giải ngân: <b>${p.disbursement_speed_days} ngày</b>
						</div>
					</div>
				`;
			});
			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b>🏆 Thẻ tóm tắt gói vay phù hợp:</b>
						<a href="/desk/financing-copilot" class="badge badge-light" style="border: 1px solid #cbd5e1;">Xem toàn bộ &rarr;</a>
					</div>
					<div>${cards}</div>
				</div>
			`;
		}

		// F003: Risk Signal Widget
		if (toolName === "evaluate_risk_signal") {
			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center">
						<b>⚠️ Trạng thái Tín hiệu Rủi ro:</b>
						<a href="/desk/risk-signal" class="badge badge-light" style="border: 1px solid #cbd5e1;">Mở Risk Agent &rarr;</a>
					</div>
					<div class="mt-1" style="font-size: 12px;">
						Tín hiệu: <code>${frappe.utils.escape_html(output.signal_id)}</code> &bull; Mức độ: <b class="text-warning">${output.severity}</b> &bull; Status: <b>${output.status}</b>
					</div>
				</div>
			`;
		}

		// F001: Financial Snapshot Widget
		if (toolName === "get_financial_snapshot" && output.metrics) {
			const metrics = output.metrics || [];
			let pills = "";
			metrics.slice(0, 5).forEach(m => {
				if (m.status === "AVAILABLE" && m.value !== null) {
					pills += `<span class="badge badge-light mr-2 mb-1 p-2" style="border: 1px solid #cbd5e1; font-size:11px;">${m.metric_id}: <b>${frappe.format(m.value, { fieldtype: "Currency", currency: "VND" })}</b></span>`;
				}
			});
			if (pills) {
				return `
					<div class="lotus-chat-widget">
						<div class="d-flex justify-content-between align-items-center mb-2">
							<b>📋 Chỉ số tài chính trích xuất:</b>
							<a href="/desk/financial-health" class="badge badge-light" style="border: 1px solid #cbd5e1;">Xem Báo cáo &rarr;</a>
						</div>
						<div class="d-flex flex-wrap">${pills}</div>
					</div>
				`;
			}
		}

		// F004: What-If Simulation Widget
		if (toolName === "simulate_what_if_scenario" && output.kpis) {
			const kpis = output.kpis || [];
			let rows = "";
			kpis.slice(0, 4).forEach(k => {
				const deltaSign = (k.delta_percent !== null && k.delta_percent > 0) ? "+" : "";
				const deltaStr = k.delta_percent !== null ? ` (${deltaSign}${k.delta_percent.toFixed(1)}%)` : "";
				rows += `
					<div class="d-flex justify-content-between py-1" style="border-bottom: 1px dashed #e2e8f0; font-size: 11px;">
						<span>${frappe.utils.escape_html(k.name)}:</span>
						<span><b>${frappe.format(k.scenario_value, { fieldtype: "Currency", currency: "VND" })}</b> <span class="text-muted">${deltaStr}</span></span>
					</div>
				`;
			});
			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b>🔮 Kết quả mô phỏng 9-KPI:</b>
						<a href="/desk/what-if-studio" class="badge badge-light" style="border: 1px solid #cbd5e1;">Mở Studio &rarr;</a>
					</div>
					<div>${rows}</div>
				</div>
			`;
		}

		return "";
	}

	format_markdown(text) {
		if (!text) return "";
		let html = frappe.utils.escape_html(text);
		html = html.replace(/^### (.*$)/gim, '<h4 style="font-size: 13px; font-weight: 700; margin: 10px 0 4px 0; color: #0f172a;">$1</h4>');
		html = html.replace(/^## (.*$)/gim, '<h3 style="font-size: 14px; font-weight: 700; margin: 12px 0 6px 0; color: #0f172a;">$1</h3>');
		html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
		html = html.replace(/^\* (.*$)/gim, '<li style="margin-left: 15px;">$1</li>');
		html = html.replace(/\n/g, '<br>');
		return html;
	}
};

// ============================================================================
// Component 2: WhatIfStudio (Multi-Variable Stress Testing Studio)
// ============================================================================
lotus_fin.components.WhatIfStudio = class WhatIfStudio {
	constructor(opts) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"));
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

// ============================================================================
// Sales Invoice Extension (AI Credit Risk Evaluation)
// ============================================================================
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('🤖 AI Đánh giá rủi ro'), function() {
				frappe.call({
					method: "lotus_fin.api.ai_insights.analyze_invoice_risk",
					args: { invoice_name: frm.doc.name },
					freeze: true,
					freeze_message: __("AI đang phân tích lịch sử khách hàng và đánh giá rủi ro..."),
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							const res = r.message;
							let indicator = "green";
							if (res.risk_level === "MEDIUM") indicator = "orange";
							if (res.risk_level === "HIGH") indicator = "red";
							frappe.msgprint({
								title: __("Kết quả Phân tích AI"),
								indicator: indicator,
								message: `<div style="font-size: 13px; line-height: 1.6;">
									<b>Mức độ rủi ro:</b> <span class="badge badge-${indicator}">${res.risk_level}</span><br>
									<b>Nhận định:</b> ${res.analysis}
								</div>`
							});
						}
					}
				});
			}, __("Lotus Fin AI"));
		}
	}
});

console.log("[Lotus Fin] Unified Client bundle & AI components initialized successfully.");
