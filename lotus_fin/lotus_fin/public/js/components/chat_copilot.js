// Lotus Fin — Reusable Chat Copilot Component
frappe.provide("lotus_fin.components");

lotus_fin.components.ChatCopilot = class ChatCopilot {
	constructor(opts) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company"));
		this.title = opts.title || __("Lotus Fin AI Copilot — Trợ lý Thông minh & Điều phối");
		this.badge = opts.badge || __("Agentic AI • Tool Calling • Grounded Accounting");
		this.min_height = opts.min_height || "420px";
		this.show_quick_pills = opts.show_quick_pills !== false;
		this.chat_history = [];
		this.render();
		this.bind_events();
		this.init_chat();
	}

	render() {
		const quickPillsHtml = this.show_quick_pills ? `
			<div class="mb-3">
				<span class="text-muted" style="font-size: 11px; font-weight: 600;">💡 Gợi ý câu hỏi nhanh:</span>
				<div class="mt-1 d-flex flex-wrap gap-1">
					<span class="lotus-quick-pill" data-query="Kiểm tra tổng quan sức khỏe tài chính và doanh thu năm nay của công ty">📊 Sức khỏe tài chính năm nay</span>
					<span class="lotus-quick-pill" data-query="Dự báo quỹ đạo dòng tiền 30 ngày tới và các mốc thiếu hụt thanh khoản">📈 Dự báo dòng tiền 30 ngày</span>
					<span class="lotus-quick-pill" data-query="Nếu doanh thu giảm 20% và khách hàng thanh toán trễ 15 ngày thì dòng tiền thế nào?">⚡ What-If: Doanh thu -20%, nợ trễ 15 ngày</span>
					<span class="lotus-quick-pill" data-query="Doanh nghiệp cần vay 500 triệu bổ sung vốn lưu động 12 tháng thì có gói nào phù hợp?">💰 Tư vấn vay 500tr vốn lưu động 12T</span>
					<span class="lotus-quick-pill" data-query="Tình hình công nợ phải thu hiện tại và tỷ lệ quá hạn là bao nhiêu?">🔍 Công nợ phải thu & nợ quá hạn</span>
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
					${__("Hỏi đáp bằng ngôn ngữ tự nhiên. AI hoạt động theo cơ chế <b>Agentic Tool Calling</b>: hiểu ngữ cảnh, gọi các công cụ kế toán chuyên sâu (F001 Sức khỏe, F002 Dòng tiền, F004 What-If, F005 Vay vốn) để tính toán chính xác và giải thích minh bạch.")}
				</p>
				${quickPillsHtml}
				<div class="lotus-chat-container">
					<div class="lotus-chat-thread" style="min-height: ${this.min_height}; max-height: 520px; overflow-y: auto;">
						<!-- Messages dynamically rendered here -->
					</div>
					<div class="lotus-chat-input-bar">
						<input type="text" class="lotus-copilot-input input-copilot-query" placeholder="${__("Nhập câu hỏi tài chính bằng ngôn ngữ tự nhiên (Ví dụ: Doanh thu năm nay bao nhiêu? Dòng tiền tháng tới thế nào?)...")}" />
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
								<li><b>F004 Mô phỏng What-If:</b> Stress-test khi doanh số giảm hoặc khách trả chậm.</li>
								<li><b>F005 Tư vấn giải pháp vay:</b> Đối chiếu gói tín dụng ngân hàng theo điều kiện doanh nghiệp.</li>
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
		if (toolName === "match_financing_products" && output.matched_products) {
			const prods = output.matched_products.slice(0, 3);
			if (!prods.length) return "";
			let cards = "";
			prods.forEach((p, idx) => {
				const rate = (p.nominal_rate_annual * 100).toFixed(1);
				const interest = frappe.format(p.estimated_monthly_interest, { fieldtype: "Currency", currency: "VND" });
				cards += `
					<div class="lotus-product-card ${idx === 0 ? 'top-recommended' : ''} mb-2 p-2">
						<div class="d-flex justify-content-between align-items-center">
							<b>${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
							<span class="lotus-score-badge">${p.match_score}/100</span>
						</div>
						<div class="mt-1" style="font-size: 11px;">
							Lãi suất: <b class="text-success">${rate}%/năm</b> &bull; Lãi ước tính: <b>~${interest}/tháng</b> &bull; Giải ngân: <b>${p.disbursement_speed_days} ngày</b>
						</div>
					</div>
				`;
			});
			return `<div class="lotus-chat-widget"><b>🏆 Thẻ tóm tắt gói vay phù hợp:</b><div class="mt-2">${cards}</div></div>`;
		}

		if (toolName === "get_financial_snapshot" && output.metrics) {
			const metrics = output.metrics || [];
			let pills = "";
			metrics.slice(0, 5).forEach(m => {
				if (m.status === "AVAILABLE" && m.value !== null) {
					pills += `<span class="badge badge-light mr-2 mb-1 p-2" style="border: 1px solid #cbd5e1;">${m.metric_id}: <b>${frappe.format(m.value, { fieldtype: "Currency", currency: "VND" })}</b></span>`;
				}
			});
			if (pills) {
				return `<div class="lotus-chat-widget"><b>📋 Chỉ số tài chính trích xuất:</b><div class="mt-2 d-flex flex-wrap">${pills}</div></div>`;
			}
		}

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
			return `<div class="lotus-chat-widget"><b>🔮 Kết quả mô phỏng 9-KPI:</b><div class="mt-2">${rows}</div></div>`;
		}

		return "";
	}

	format_markdown(text) {
		if (!text) return "";
		if (typeof frappe.markdown === "function") {
			try {
				return frappe.markdown(text);
			} catch (e) {}
		}
		let html = frappe.utils.escape_html(text);
		html = html.replace(/^### (.*$)/gim, '<h4 style="font-size: 13px; font-weight: 700; margin: 10px 0 4px 0; color: #0f172a;">$1</h4>');
		html = html.replace(/^## (.*$)/gim, '<h3 style="font-size: 14px; font-weight: 700; margin: 12px 0 6px 0; color: #0f172a;">$1</h3>');
		html = html.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
		html = html.replace(/^\* (.*$)/gim, '<li style="margin-left: 15px;">$1</li>');
		html = html.replace(/\n\n/g, '<br><br>');
		return html;
	}
};
