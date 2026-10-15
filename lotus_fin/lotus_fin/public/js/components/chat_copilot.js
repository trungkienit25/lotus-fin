// Lotus Fin — Reusable Chat Copilot Component across All 7 Modules
frappe.provide("lotus_fin.components");

lotus_fin.components.ChatCopilot = class ChatCopilot {
	constructor(opts) {
		this.parent = $(opts.parent);
		this.get_company = opts.get_company || (() => frappe.defaults.get_user_default("Company"));
		this.title = opts.title || __("Lotus Fin AI Copilot — Financial Dialogue & Action Orchestrator");
		this.badge = opts.badge || __("Deterministic Tool Calling • Real-time Accounting Data");
		this.min_height = opts.min_height || "480px";
		this.show_quick_pills = opts.show_quick_pills !== false;
		this.chat_history = [];
		
		// Manage stable persistent session ID across page reloads
		this.storage_key = `lotus_copilot_session_${frappe.session ? frappe.session.user : "guest"}`;
		this.session_id = localStorage.getItem(this.storage_key);
		if (!this.session_id) {
			this.session_id = `sess_${(frappe.session && frappe.session.user) ? frappe.session.user.replace(/[^a-zA-Z0-9]/g, "_") : "admin"}_${Math.random().toString(36).substring(2, 10)}`;
			localStorage.setItem(this.storage_key, this.session_id);
		}

		this.render();
		this.bind_events();
		this.init_chat();
	}

	render() {
		const quickPillsHtml = this.show_quick_pills ? `
			<div class="mb-3">
				<span class="text-muted" style="font-size: 11px; font-weight: 600;">💡 Quick Question Prompts (F001 - F006):</span>
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
				<div class="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
					<div class="lotus-section-title mb-0">
						<span style="font-size: 16px;">🤖 <b>${this.title}</b></span>
						<span class="lotus-ai-badge">${this.badge}</span>
					</div>
					<div class="d-flex align-items-center gap-1">
						<button class="lotus-btn-secondary btn-view-audit" style="font-size: 11px; padding: 4px 10px;" title="${__("View AI Sandbox Operational Audit Log")}">
							📋 ${__("Audit Log")}
						</button>
						<button class="lotus-btn-secondary btn-export-audit" style="font-size: 11px; padding: 4px 10px;" title="${__("Export Evidence JSON Lines (.jsonl)")}">
							📥 ${__("Evidence")}
						</button>
						<button class="lotus-btn-secondary btn-clear-chat" style="font-size: 11px; padding: 4px 10px;" title="${__("Clear conversation history")}">
							🗑️ ${__("Reset")}
						</button>
					</div>
				</div>
				<p class="text-muted" style="font-size: 13px; margin-bottom: 14px; line-height: 1.5;">
					${__("Natural language financial copilot powered by <b>Agentic Tool Calling</b>: understands financial context and orchestrates accounting tools (F001 Health, F002 Cashflow, F003 Risk Signals, F004 What-If, F005 Financing, F006 Repayment) to compute verified facts and transparent explanations.")}
				</p>
				${quickPillsHtml}
				<div class="lotus-chat-container">
					<div class="lotus-chat-thread" style="min-height: ${this.min_height}; max-height: 520px; overflow-y: auto;">
						<!-- Messages dynamically rendered here -->
					</div>
					<div class="lotus-chat-input-bar">
						<input type="text" class="lotus-copilot-input input-copilot-query" placeholder="${__("Ask a financial question in natural language (e.g., What is our net revenue? Recommend a 1B loan?)...")}" />
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

		this.$el.on("click", ".btn-view-audit", function () {
			me.show_audit_modal();
		});

		this.$el.on("click", ".btn-export-audit", function () {
			me.export_evidence_jsonl();
		});
	}

	init_chat(reset = false) {
		const me = this;
		const company = this.get_company();

		if (reset) {
			frappe.call({
				method: "lotus_fin.api.ai_insights.reset_chat_session",
				args: {
					session_id: me.session_id,
					company: company
				},
				callback() {
					// Allocate fresh session ID
					me.session_id = `sess_${(frappe.session && frappe.session.user) ? frappe.session.user.replace(/[^a-zA-Z0-9]/g, "_") : "admin"}_${Math.random().toString(36).substring(2, 10)}`;
					localStorage.setItem(me.storage_key, me.session_id);
					me.$thread.empty();
					me.render_welcome();
					frappe.show_alert({ message: __("Chat session reset successfully."), indicator: "green" });
				}
			});
			return;
		}

		// Restore conversation from database / cache
		frappe.call({
			method: "lotus_fin.api.ai_insights.get_chat_history",
			args: {
				session_id: me.session_id,
				company: company
			},
			callback(r) {
				me.$thread.empty();
				if (r.message && r.message.messages && r.message.messages.length > 0) {
					r.message.messages.forEach(msg => {
						if (msg.role === "user") {
							me.append_user_msg(msg.content);
						} else if (msg.role === "assistant") {
							me.append_copilot_msg({
								reply: msg.content,
								tool_called: null
							});
						}
					});
					me.$thread.scrollTop(me.$thread[0].scrollHeight);
				} else {
					me.render_welcome();
				}
			},
			error() {
				me.$thread.empty();
				me.render_welcome();
			}
		});
	}

	render_welcome() {
		const welcome = `
			<div class="lotus-chat-msg copilot">
				<div class="lotus-msg-bubble">
					<div class="d-flex align-items-center mb-1">
						<span style="font-size: 16px; margin-right: 6px;">🤖</span>
						<b style="color: #0369a1;">Lotus Fin AI Copilot</b>
					</div>
					<div>
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

	append_user_msg(query) {
		const userMsgHtml = `
			<div class="lotus-chat-msg user">
				<div class="lotus-msg-bubble">${frappe.utils.escape_html(query)}</div>
			</div>
		`;
		this.$thread.append(userMsgHtml);
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
		this.append_user_msg(q);
		this.$input.val("");
		this.$sendBtn.prop("disabled", true);

		const loadingHtml = `
			<div id="lotus-chat-loading" class="lotus-chat-msg copilot">
				<div class="lotus-msg-bubble">
					<span class="lotus-chat-loading-dots">
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
				as_of_date: (frappe.datetime && frappe.datetime.get_today) ? frappe.datetime.get_today() : "2026-12-31",
				session_id: me.session_id
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
				<div class="lotus-chat-tool-badge">
					<span>⚙️</span>
					<span>Tool executed: <b>${frappe.utils.escape_html(toolLabel)}</b> (<code>${frappe.utils.escape_html(toolCalled)}</code>)</span>
				</div>
			`;
		}

		let widgetHtml = "";
		if (res.tool_output && toolCalled) {
			widgetHtml = this.render_tool_output_widget(toolCalled, res.tool_output);
		}

		let traceFooterHtml = "";
		if (res.trace_id || res.latency_ms) {
			traceFooterHtml = `
				<div class="text-muted mt-2 d-flex justify-content-between align-items-center" style="font-size: 11px; border-top: 1px dashed #e2e8f0; padding-top: 4px;">
					<span>⚡ Latency: <b>${res.latency_ms || 0}ms</b></span>
					${res.trace_id ? `<span>Trace: <code>${frappe.utils.escape_html(res.trace_id)}</code></span>` : ""}
				</div>
			`;
		}

		const formattedReply = this.format_markdown(replyText);

		const msgHtml = `
			<div class="lotus-chat-msg copilot">
				<div class="lotus-msg-bubble">
					${toolBadgeHtml}
					<div>${formattedReply}</div>
					${widgetHtml}
					${traceFooterHtml}
				</div>
			</div>
		`;
		this.$thread.append(msgHtml);
	}

	render_tool_output_widget(toolName, output) {
		if (!output) return "";

		// F006: Repayment Schedule Widget
		if (toolName === "calculate_repayment_schedule" && output.monthly_payment) {
			const pmtStr = lotus_fin.core.format_currency(output.monthly_payment, "VND");
			const intStr = lotus_fin.core.format_currency(output.total_interest, "VND");
			const shockHtml = output.shock_bps > 0 ? `
				<div class="mt-1 text-danger font-weight-bold" style="font-size: 11px;">
					⚠️ Rate Shock (+${output.shock_bps} bps): Additional interest cost +${lotus_fin.core.format_currency(output.shock_added_interest, "VND")}
				</div>
			` : "";

			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center">
						<b>📑 Loan Repayment Summary:</b>
						<a href="/desk/repayment-schedule" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Studio &rarr;</a>
					</div>
					<div class="row mt-2" style="font-size: 12px;">
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
						<b>🏆 Matched Financing Products:</b>
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
						<b>⚠️ Risk Signal Evaluation:</b>
						<a href="/desk/risk-signal" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Risk Agent &rarr;</a>
					</div>
					<div class="mt-1" style="font-size: 12px;">
						Signal: <code>${frappe.utils.escape_html(output.signal_id || "SIGNAL")}</code> &bull; Severity: <b class="text-warning">${output.severity || "NORMAL"}</b> &bull; Status: <b>${output.status || "COMPLETED"}</b>
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
					pills += `<span class="badge badge-light mr-2 mb-1 p-2" style="border: 1px solid #cbd5e1; font-size:11px;">${m.metric_id}: <b>${lotus_fin.core.format_currency(m.value, "VND")}</b></span>`;
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
						<span><b>${lotus_fin.core.format_currency(k.scenario_value, "VND")}</b> <span class="text-muted">${deltaStr}</span></span>
					</div>
				`;
			});
			return `
				<div class="lotus-chat-widget">
					<div class="d-flex justify-content-between align-items-center mb-2">
						<b>🔮 9-KPI Stress Simulation Result:</b>
						<a href="/desk/what-if-studio" class="badge badge-light" style="border: 1px solid #cbd5e1;">Open Studio &rarr;</a>
					</div>
					<div>${rows}</div>
				</div>
			`;
		}

		return "";
	}

	show_audit_modal() {
		const company = this.get_company();
		const d = new frappe.ui.Dialog({
			title: __("📋 AI Sandbox Operational Audit Log (FinTechathon Track E)"),
			size: "large",
			fields: [
				{
					fieldname: "log_table",
					fieldtype: "HTML"
				}
			],
			primary_action_label: __("Close"),
			primary_action() {
				d.hide();
			}
		});

		d.fields_dict.log_table.$wrapper.html(`
			<div class="text-center p-4 text-muted">
				<i class="octicon octicon-sync"></i> Loading sandbox audit logs...
			</div>
		`);

		d.show();

		frappe.call({
			method: "lotus_fin.api.ai_insights.get_operation_logs",
			args: {
				company: company,
				limit: 25
			},
			callback(r) {
				const logs = r.message || [];
				if (!logs.length) {
					d.fields_dict.log_table.$wrapper.html(`
						<div class="alert alert-info mt-2">
							No operations recorded yet in this environment session.
						</div>
					`);
					return;
				}

				let rows = "";
				logs.forEach(l => {
					const timeStr = l.timestamp ? l.timestamp.substring(11, 19) : "";
					const ledgers = (l.accounting_ledger_accessed || []).join(", ");
					rows += `
						<tr style="font-size: 11px;">
							<td><b>${timeStr}</b></td>
							<td><span class="badge badge-primary">${frappe.utils.escape_html(l.agent_intent || "QA")}</span></td>
							<td><code>${frappe.utils.escape_html(l.tool_called || "NONE")}</code></td>
							<td><span class="text-muted">${frappe.utils.escape_html(ledgers)}</span></td>
							<td><span class="badge badge-${l.execution_status === 'SUCCESS' ? 'success' : 'danger'}">${l.execution_status}</span></td>
							<td><b>${l.latency_ms}ms</b></td>
							<td><small class="text-muted">${frappe.utils.escape_html(l.log_id || "")}</small></td>
						</tr>
					`;
				});

				const tableHtml = `
					<div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
						<table class="table table-bordered table-hover mb-0">
							<thead class="thead-light" style="font-size: 11px;">
								<tr>
									<th>Time</th>
									<th>Intent</th>
									<th>Tool Invoked</th>
									<th>Ledgers Accessed</th>
									<th>Status</th>
									<th>Latency</th>
									<th>Log ID</th>
								</tr>
							</thead>
							<tbody>
								${rows}
							</tbody>
						</table>
					</div>
					<div class="mt-2 text-right">
						<small class="text-muted">Standards: OpenTelemetry GenAI Conventions &bull; FinTechathon 2026 Item 06 Execution Evidence</small>
					</div>
				`;

				d.fields_dict.log_table.$wrapper.html(tableHtml);
			}
		});
	}

	export_evidence_jsonl() {
		const company = this.get_company();
		frappe.show_alert({ message: __("Preparing sandbox operation evidence..."), indicator: "blue" });

		frappe.call({
			method: "lotus_fin.api.ai_insights.export_operation_logs",
			args: { company: company },
			callback(r) {
				const res = r.message || {};
				const logs = res.logs || [];
				if (!logs.length) {
					frappe.msgprint(__("No operation logs recorded to export."));
					return;
				}

				const jsonlLines = logs.map(e => JSON.stringify(e)).join("\n");
				const blob = new Blob([jsonlLines], { type: "application/x-ndjson" });
				const url = URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.href = url;
				a.download = `sandbox_operation_logs_${company || "lotus_fin"}_${frappe.datetime.get_today()}.jsonl`;
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				URL.revokeObjectURL(url);
				frappe.show_alert({ message: __("Downloaded operation audit logs (.jsonl)."), indicator: "green" });
			}
		});
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
