// Lotus Fin — Business Widget: Chat Copilot (Material 3 Style)
frappe.provide("lotus_fin.widgets");

lotus_fin.widgets.ChatCopilot = class ChatCopilot {
	constructor(opts = {}) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company"));
		this.title = opts.title || __("Lotus Fin AI Copilot — Financial Dialogue & Action Orchestrator");
		this.badge = opts.badge || __("Deterministic Tool Calling • Real-time Accounting Data");
		this.min_height = opts.min_height || "520px";
		this.show_quick_pills = opts.show_quick_pills !== false;
		this.chat_history = [];
		this.render();
		this.bind_events();
		this.init_chat();
	}

	render() {
		const quickPillsHtml = this.show_quick_pills ? `
			<div class="mb-4">
				<div class="d-flex align-items-center gap-2 mb-2">
					<span style="font-size: 14px;">💡</span>
					<span class="text-muted" style="font-size: 12px; font-weight: 600;">Quick Suggestions (Supports all 7 AI Modules AI001 - AI007):</span>
				</div>
				<div class="d-flex flex-wrap gap-2">
					<span class="lotus-quick-pill" data-query="How is our company financial health this year?">📊 Financial Health (F001)</span>
					<span class="lotus-quick-pill" data-query="Forecast cash flow for the next 30 days and detect shortfalls">💧 Cash Flow Forecast (F002)</span>
					<span class="lotus-quick-pill" data-query="Check risk signals for overdue AR spikes and AP clusters">⚠️ Risk Signals (F003)</span>
					<span class="lotus-quick-pill" data-query="If revenue drops 20% and collections delay 15 days, how is cash flow impacted?">🔮 What-If: Sales -20%, AR Delay +15D (F004)</span>
					<span class="lotus-quick-pill" data-query="Advise loan options for 1B VND working capital in 12 months">🏦 Financing Advice 1B VND (F005)</span>
					<span class="lotus-quick-pill" data-query="Calculate 1B VND loan schedule at 8.5% for 12 months with +200 bps rate shock">📑 Repayment Schedule & Rate Shock (F006)</span>
				</div>
			</div>
		` : "";

		this.$el = $(`
			<div class="lotus-card lotus-copilot-card">
				<div class="lotus-card-header">
					<div>
						<h3 class="lotus-card-title">
							<span>🤖</span>
							<span>${this.title}</span>
						</h3>
						<p class="lotus-card-subtitle">
							${__("Natural language financial inquiry. AI operates via <b>Agentic Tool Calling</b>: understands context, orchestrates specialized financial tools to compute deterministic answers with transparent evidence.")}
						</p>
					</div>
					<div class="d-flex align-items-center gap-2">
						<span class="lotus-badge lotus-badge-ai">${this.badge}</span>
						<button class="lotus-btn lotus-btn-secondary lotus-btn-sm btn-clear-chat" title="${__("Clear conversation history")}">
							🗑️ ${__("Reset Chat")}
						</button>
					</div>
				</div>

				${quickPillsHtml}

				<div class="lotus-chat-m3">
					<div class="lotus-chat-thread-m3" style="min-height: ${this.min_height}; max-height: 560px;">
						<!-- Messages rendered dynamically -->
					</div>
					<div class="lotus-chat-input-bar-m3">
						<input type="text" class="lotus-input input-copilot-query" placeholder="${__("Ask a financial question in natural language (e.g., What is our net revenue? Recommend a 1B loan?)...")}" style="border-radius: 9999px;" />
						<button class="lotus-btn lotus-btn-primary btn-ask-copilot">
							<span>🚀 ${__("Send")}</span>
						</button>
					</div>
				</div>
			</div>
		`);

		this.parent.append(this.$el);
		this.$thread = this.$el.find(".lotus-chat-thread-m3");
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
				<div class="lotus-msg-m3 copilot">
					<div class="lotus-msg-bubble-m3">
						<div class="d-flex align-items-center gap-2 mb-2">
							<span style="font-size: 18px;">🤖</span>
							<b style="color: #2563eb; font-size: 14px;">Lotus Fin AI Copilot</b>
						</div>
						<div style="color: #334155; line-height: 1.6;">
							Hello! I am your AI Financial Copilot. Powered by deterministic <b>Agentic Tool Calling</b>, I analyze natural language inquiries and dispatch verified accounting engines:
							<ul class="mb-0 mt-2 pl-3" style="line-height: 1.6;">
								<li><b>F001 Financial Health:</b> Revenue, COGS, Gross Profit, Cash Balance, AR/AP metrics.</li>
								<li><b>F002 Cash Flow Forecast:</b> 30-day daily cash runway and shortfall detection.</li>
								<li><b>F003 Risk Signals:</b> Automated detection of AR overdue spikes and AP due clusters.</li>
								<li><b>F004 What-If Stress Studio:</b> Multi-variable simulations on sales, delays, and overhead.</li>
								<li><b>F005 Financing Copilot:</b> Real-time bank SME loan matching and eligibility screening.</li>
								<li><b>F006 Debt Amortization:</b> Schedule principal & interest and simulate interest rate shocks (+bps).</li>
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
			frappe.msgprint(__("Please select a company before chatting with AI Copilot."));
			return;
		}
		if (!query || !query.trim()) return;

		const q = query.trim();
		const userMsgHtml = `
			<div class="lotus-msg-m3 user">
				<div class="lotus-msg-bubble-m3">${frappe.utils.escape_html(q)}</div>
			</div>
		`;
		this.$thread.append(userMsgHtml);
		this.$input.val("");
		this.$sendBtn.prop("disabled", true);

		const loadingHtml = `
			<div id="lotus-chat-loading" class="lotus-msg-m3 copilot">
				<div class="lotus-msg-bubble-m3" style="background: #ffffff;">
					<span class="d-inline-flex align-items-center gap-2 text-muted" style="font-size: 13px;">
						<i class="octicon octicon-sync"></i> 
						<span>Analyzing financial intent and executing accounting tools...</span>
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
						reply: "An error occurred while processing your request. Please try again.",
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
					reply: "Unable to reach AI Copilot service. Please verify network connectivity.",
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
				<div class="d-inline-flex align-items-center gap-2 px-3 py-1 mb-2" style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 9999px; font-size: 11px; color: #1e40af;">
					<span>⚙️</span>
					<span>Tool executed: <b>${frappe.utils.escape_html(toolLabel)}</b> (<code>${frappe.utils.escape_html(toolCalled)}</code>)</span>
				</div>
			`;
		}

		let widgetHtml = "";
		if (res.tool_output && toolCalled) {
			widgetHtml = this.render_tool_output_widget(toolCalled, res.tool_output);
		}

		const formattedReply = this.format_markdown(replyText);

		const msgHtml = `
			<div class="lotus-msg-m3 copilot">
				<div class="lotus-msg-bubble-m3">
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
			const pmtStr = lotus_fin.core.format_currency(output.monthly_payment, "VND");
			const intStr = lotus_fin.core.format_currency(output.total_interest, "VND");
			const shockHtml = output.shock_bps > 0 ? `
				<div class="mt-2 text-danger font-weight-bold" style="font-size: 12px;">
					⚠️ Rate Shock (+${output.shock_bps} bps bps): Additional interest cost +${lotus_fin.core.format_currency(output.shock_added_interest, "VND")}
				</div>
			` : "";

			return `
				<div class="p-3 mt-3" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b style="font-size: 13px;">📑 Loan Repayment Summary:</b>
						<a href="/desk/repayment-schedule" class="lotus-badge lotus-badge-primary">Open Studio &rarr;</a>
					</div>
					<div class="row" style="font-size: 12px;">
						<div class="col-6">Monthly Pmt: <b class="text-primary">${pmtStr}</b></div>
						<div class="col-6">Total Interest: <b class="text-warning">${intStr}</b></div>
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
				const interest = lotus_fin.core.format_currency(p.estimated_monthly_interest, "VND");
				cards += `
					<div class="p-2 mb-2" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;">
						<div class="d-flex justify-content-between align-items-center">
							<b>${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
							<span class="lotus-badge lotus-badge-success">${p.match_score}/100</span>
						</div>
						<div class="mt-1 text-muted" style="font-size: 11px;">
							Interest Rate: <b class="text-success">${rate}%/yr</b> &bull; Est. Interest: <b>~${interest}/month</b> &bull; Disbursement: <b>${p.disbursement_speed_days} Days</b>
						</div>
					</div>
				`;
			});
			return `
				<div class="p-3 mt-3" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b style="font-size: 13px;">🏆 Matched Financing Products:</b>
						<a href="/desk/financing-copilot" class="lotus-badge lotus-badge-primary">View All &rarr;</a>
					</div>
					<div>${cards}</div>
				</div>
			`;
		}

		// F003: Risk Signal Widget
		if (toolName === "evaluate_risk_signal") {
			return `
				<div class="p-3 mt-3" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
					<div class="d-flex justify-content-between align-items-center">
						<b style="font-size: 13px;">⚠️ Risk Signal Evaluation:</b>
						<a href="/desk/risk-signal" class="lotus-badge lotus-badge-primary">Open Risk Agent &rarr;</a>
					</div>
					<div class="mt-2" style="font-size: 12px;">
						Signal: <code>${frappe.utils.escape_html(output.signal_id)}</code> &bull; Severity: <b class="text-warning">${output.severity}</b> &bull; Status: <b>${output.status}</b>
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
					pills += `<span class="lotus-badge lotus-badge-primary mr-2 mb-1">${m.metric_id}: <b>${lotus_fin.core.format_currency(m.value, "VND")}</b></span>`;
				}
			});
			if (pills) {
				return `
					<div class="p-3 mt-3" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
						<div class="d-flex justify-content-between align-items-center mb-2">
							<b style="font-size: 13px;">📋 Extracted Financial Metrics:</b>
							<a href="/desk/financial-health" class="lotus-badge lotus-badge-primary">View Report &rarr;</a>
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
					<div class="d-flex justify-content-between py-1" style="border-bottom: 1px dashed #e2e8f0; font-size: 12px;">
						<span>${frappe.utils.escape_html(k.name)}:</span>
						<span><b>${lotus_fin.core.format_currency(k.scenario_value, "VND")}</b> <span class="text-muted">${deltaStr}</span></span>
					</div>
				`;
			});
			return `
				<div class="p-3 mt-3" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b style="font-size: 13px;">🔮 9-KPI Stress Simulation Result:</b>
						<a href="/desk/what-if-studio" class="lotus-badge lotus-badge-primary">Open Studio &rarr;</a>
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
