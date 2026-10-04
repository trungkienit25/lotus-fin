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
	return Math.round(Number(value)).toLocaleString("vi-VN") + " " + currency;
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

	set_loading(loading = true, loadingText = "Processing...") {
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
		this.emptyMessage = opts.emptyMessage || "No data available";
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
		this.title = opts.title || __("Lotus Fin AI Copilot — Financial Intelligence & Action Coordination");
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
				<span class="text-muted" style="font-size: 11px; font-weight: 600;">💡 Quick Suggestions (AI001 - AI007):</span>
				<div class="mt-1 d-flex flex-wrap gap-1">
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
			<div class="lotus-section-card lotus-copilot-card">
				<div class="d-flex justify-content-between align-items-center mb-2">
					<div class="lotus-section-title mb-0">
						<span style="font-size: 16px;">🤖 <b>${this.title}</b></span>
						<span class="lotus-ai-badge">${this.badge}</span>
					</div>
					<button class="lotus-btn-secondary btn-clear-chat" style="font-size: 11px; padding: 4px 12px;" title="${__("Clear conversation history")}">
						🗑️ ${__("Reset Chat")}
					</button>
				</div>
				<p class="text-muted" style="font-size: 13px; margin-bottom: 14px; line-height: 1.5;">
					${__("Natural language financial inquiry. AI operates via <b>Agentic Tool Calling</b>: understands context, orchestrates specialized financial tools (F001 Health, F002 Cash Flow, F003 Risk, F004 What-If, F005 Financing, F006 Repayment) to compute deterministic answers with transparent evidence.")}
				</p>
				${quickPillsHtml}
				<div class="lotus-chat-container">
					<div class="lotus-chat-thread" style="min-height: ${this.min_height}; max-height: 520px; overflow-y: auto;">
						<!-- Messages dynamically rendered here -->
					</div>
					<div class="lotus-chat-input-bar">
						<input type="text" class="lotus-copilot-input input-copilot-query" placeholder="${__("Enter financial inquiry (e.g., What is our revenue this year? Advise loan options for 1B VND?)...")}" />
						<button class="lotus-chat-send-btn btn-ask-copilot">
							<span>🚀 ${__("Send")}</span>
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
							Hello! I am your AI Financial Copilot. I operate via deterministic <b>Agentic Tool Calling</b>: I understand natural language inquiries and autonomously coordinate verified accounting tools (with zero hallucinations):
							<ul class="mb-0 mt-2 pl-3" style="line-height: 1.6;">
								<li><b>F001 Financial Health:</b> Revenue, COGS, gross margin, cash balance, and AR/AP aging.</li>
								<li><b>F002 Cash Flow Forecast:</b> 30-day cash trajectory and liquidity deficit detection.</li>
								<li><b>F003 Risk Signals:</b> Continuous monitoring of overdue AR spikes and AP payment clusters.</li>
								<li><b>F004 What-If Studio:</b> Multi-variable stress testing across 9 mission-critical financial KPIs.</li>
								<li><b>F005 Financing Advisor:</b> Deterministic SME loan package matching against bank criteria.</li>
								<li><b>F006 Repayment Schedule:</b> Principal and interest amortization simulation under rate shocks (+bps).</li>
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
						<span>Analyzing intent and activating accounting tools...</span>
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
						reply: "Server encountered an error processing inquiry. Please try again later.",
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
					reply: "Unable to connect to AI Copilot service. Please verify your network connection.",
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
					<span>Executed Tool: <b>${frappe.utils.escape_html(toolLabel)}</b> (<code>${frappe.utils.escape_html(toolCalled)}</code>)</span>
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
					⚠️ Rate Shock (+${output.shock_bps} bps): Additional interest cost +${frappe.format(output.shock_added_interest, { fieldtype: "Currency", currency: "VND" })}
				</div>
			` : "";

			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center">
						<b>📑 Repayment Schedule Summary:</b>
						<a href="/desk/repayment-schedule" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Studio &rarr;</a>
					</div>
					<div class="row mt-2" style="font-size: 12px;">
						<div class="col-6">Monthly Payment: <b class="text-primary">${pmtStr}</b></div>
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
				const interest = frappe.format(p.estimated_monthly_interest, { fieldtype: "Currency", currency: "VND" });
				cards += `
					<div class="lotus-product-card ${idx === 0 ? 'top-recommended' : ''} mb-2 p-2" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px;">
						<div class="d-flex justify-content-between align-items-center">
							<b>${idx + 1}. ${frappe.utils.escape_html(p.provider)} — ${frappe.utils.escape_html(p.product_name)}</b>
							<span class="badge badge-success">${p.match_score}/100</span>
						</div>
						<div class="mt-1 text-muted" style="font-size: 11px;">
							Interest Rate: <b class="text-success">${rate}%/yr</b> &bull; Est. Interest: <b>~${interest}/month</b> &bull; Disbursement: <b>${p.disbursement_speed_days} Days</b>
						</div>
					</div>
				`;
			});
			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b>🏆 Matched Financing Packages:</b>
						<a href="/desk/financing-copilot" class="badge badge-light" style="border: 1px solid #cbd5e1;">View All &rarr;</a>
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
						<b>⚠️ Risk Signal Status:</b>
						<a href="/desk/risk-signal" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Risk Agent &rarr;</a>
					</div>
					<div class="mt-1" style="font-size: 12px;">
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
					pills += `<span class="badge badge-light mr-2 mb-1 p-2" style="border: 1px solid #cbd5e1; font-size:11px;">${m.metric_id}: <b>${frappe.format(m.value, { fieldtype: "Currency", currency: "VND" })}</b></span>`;
				}
			});
			if (pills) {
				return `
					<div class="lotus-chat-widget">
						<div class="d-flex justify-content-between align-items-center mb-2">
							<b>📋 Extracted Financial Metrics:</b>
							<a href="/desk/financial-health" class="badge badge-light" style="border: 1px solid #cbd5e1;">View Report &rarr;</a>
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
						<b>🔮 What-If 9-KPI Simulation:</b>
						<a href="/desk/what-if-studio" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Studio &rarr;</a>
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
						<button class="lotus-btn-secondary btn-reset-sim-defaults" style="font-size: 11px; padding: 4px 12px;" title="${__("Reset to default scenario")}">
							↺ ${__("Default")}
						</button>
					</div>
				</div>
				<p class="text-muted" style="font-size: 12px; margin-bottom: 14px;">
					${__("Multi-variable quantitative stress-testing simulation. Evaluate the simultaneous impact of sales shocks, AR/AP payment delays, fixed OPEX changes, and capital financing injections across 9 mission-critical business KPIs.")}
				</p>

				<!-- Preconfigured stress presets -->
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

				<!-- Parameter block 1: Market & Revenue & Receivables -->
				<div class="lotus-sim-group-title">
					<span>📊 Group 1: Revenue & Working Capital Cycles (AR / AP)</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Net Revenue Change")}</span>
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
							<span>-30 Days (Tight Credit)</span>
							<span>0 Days</span>
							<span>+60 Days (Capital Optimization)</span>
						</div>
						<div class="lotus-sim-subhint">${__("Postpones AP disbursements to conserve cash buffer.")}</div>
					</div>
				</div>

				<!-- Parameter block 2: Operating Expenses & Shocks -->
				<div class="lotus-sim-group-title">
					<span>🏢 Group 2: Operating Expenses (OPEX), Payroll & One-Off Shocks</span>
				</div>
				<div class="lotus-sim-grid-section">
					<div class="lotus-sim-box">
						<div class="lotus-sim-box-title">
							<span>${__("Operating Expenses Change (OPEX)")}</span>
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
							<span>${__("Payroll & Compensation Change")}</span>
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

				<!-- Parameter block 3: Debt Financing & Capital Injection -->
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
			badge.text(frappe.format(val, { fieldtype: "Currency", currency: "VND" }));
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
					Projected cash balance drops to <b>${frappe.format(e.projected_cash, { fieldtype: "Currency", currency: "VND" })}</b>, 
					resulting in a cash deficit of <b>${frappe.format(e.deficit_amount, { fieldtype: "Currency", currency: "VND" })}</b>.
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
							<th style="width: 11%;">${__("Ratio %")}</th>
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
		return frappe.format(val, { fieldtype: "Currency", currency: "VND" });
	}
};

// ============================================================================
// Sales Invoice Extension (AI Credit Risk Evaluation)
// ============================================================================
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('🤖 AI Invoice Risk Assessment'), function() {
				frappe.call({
					method: "lotus_fin.api.ai_insights.analyze_invoice_risk",
					args: { invoice_name: frm.doc.name },
					freeze: true,
					freeze_message: __("AI is analyzing customer history and assessing risk..."),
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							const res = r.message;
							let indicator = "green";
							if (res.risk_level === "MEDIUM") indicator = "orange";
							if (res.risk_level === "HIGH") indicator = "red";
							frappe.msgprint({
								title: __("AI Risk Assessment Result"),
								indicator: indicator,
								message: `<div style="font-size: 13px; line-height: 1.6;">
									<b>Risk Level:</b> <span class="badge badge-${indicator}">${res.risk_level}</span><br>
									<b>Analysis:</b> ${res.analysis}
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
