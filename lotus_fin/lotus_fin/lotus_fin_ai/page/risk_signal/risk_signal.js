// AI003 Risk Signal Page Controller & UI (contract V2.2, DEMO_ONLY)
// Data is never interpolated into HTML: every dynamic value is set with
// textContent (text-node-only rendering; server output is escaped by design).
frappe.provide("lotus_fin.risk_signal");

frappe.pages["risk-signal"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Risk Signal"),
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
		this.init();
	}

	init() {
		this.setup_breadcrumbs();
		this.setup_filters();
		this.setup_dom();
		this.setup_events();
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
				me.clear_result(__("Company changed — the previous result was cleared."));
			}
		});

		this.signal_field = this.page.add_field({
			fieldname: "signal_id",
			label: __("Signal"),
			fieldtype: "Select",
			options: [
				{ label: __("AR Overdue Spike"), value: "AR_OVERDUE_SPIKE" },
				{ label: __("AP Due Cluster"), value: "AP_DUE_CLUSTER" }
			],
			default: "AR_OVERDUE_SPIKE",
			change() {
				me.clear_result(__("Signal changed — the previous result was cleared."));
			}
		});

		this.as_of_field = this.page.add_field({
			fieldname: "as_of_date",
			label: __("As-of Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			change() {
				me.clear_result(__("Date changed — the previous result was cleared."));
			}
		});

		this.explanation_field = this.page.add_field({
			fieldname: "include_explanation",
			label: __("AI Explanation"),
			fieldtype: "Check",
			default: 1
		});

		this.page.set_primary_action(__("Evaluate Signal"), function () {
			me.evaluate();
		}, "octicon octicon-pulse");
	}

	setup_dom() {
		const me = this;
		this.main = $(this.wrapper).find(".layout-main-section");
		this.main.empty();

		// Persistent scope disclosures (packet §15: must be visibly disclosed).
		const banner = this.el("div", "rs-banner rs-banner-demo");
		const bannerText = this.el("div");
		const bannerTitle = this.el("b", null, __("DEMO_ONLY — NOT APPROVED FOR PRODUCTION"));
		const bannerBody = this.el(
			"div",
			null,
			__("This signal runs under demo policy AI003_DEMO_POLICY_V1. It is NOT production calibrated; thresholds, floors and windows are demo values only and there is no promotion path.")
		);
		bannerText.append(bannerTitle, bannerBody);
		banner.append(bannerText);

		const glossary = this.el("div", "rs-glossary text-muted");
		glossary.append(this.el("span", null,
			__("How to read a result: ") ));
		glossary.append(this.el("span", null,
			__("BENIGN = no threshold breach. WATCH = review recommended. HIGH = review with higher priority. Inconclusive or failed states never mean BENIGN — they mean the evaluation could not complete.")));

		this.state_box = this.el("div", "rs-state");

		this.result_box = this.el("div", "rs-result");

		this.main.append(banner, glossary, this.state_box, this.result_box);
		this.show_empty();
	}

	setup_events() {
		// Keyboard: the primary action stays reachable via standard focus order.
		this.main.attr("tabindex", "-1");
	}

	// ---------- DOM helpers (text nodes only) ----------
	el(tag, className, text) {
		const node = document.createElement(tag);
		if (className) node.className = className;
		if (text !== undefined && text !== null) node.textContent = __(String(text));
		return node;
	}

	kv_row(label, value, className) {
		const row = this.el("div", "rs-kv " + (className || ""));
		row.append(this.el("span", "rs-kv-label", label), this.el("span", "rs-kv-value", value));
		return row;
	}

	// ---------- states ----------
	set_state(node) {
		this.state_box.empty();
		if (node) this.state_box.append(node);
	}

	show_empty() {
		const box = this.el("div", "rs-panel rs-panel-muted");
		box.append(this.el("div", "rs-panel-title", __("No evaluation yet")));
		box.append(this.el("div", null,
			__("Pick a company, a signal and an as-of date, then run Evaluate Signal. You will see what happened, why, the evidence behind it, and what to inspect next.")));
		this.set_state(box);
	}

	show_loading() {
		const box = this.el("div", "rs-panel rs-panel-muted");
		box.append(this.el("div", "rs-panel-title", __("Evaluating…")));
		box.append(this.el("div", null, __("Running the deterministic pipeline. This does not modify any data.")));
		this.set_state(box);
		this.result_box.empty();
	}

	clear_result(message) {
		this.result_box.empty();
		if (message) {
			const note = this.el("div", "rs-banner rs-banner-info");
			note.append(this.el("div", null, message));
			this.result_box.append(note);
		} else {
			this.show_empty();
		}
	}

	// ---------- reason copy ----------
	reason_text(code) {
		const map = {
			ACCESS_DENIED: __("You do not have access to the requested company or report. Re-check the company picker, or ask an administrator for the Accounts User role and company permission."),
			UNAUTHORIZED_ACCESS: __("You are not signed in with an authorized account. Sign in and try again."),
			INVALID_REQUEST: __("The request was not understood. Check the company, signal and date values."),
			FUTURE_AS_OF: __("The as-of date cannot be in the future: this signal compares against a historical baseline, so a past accounting date is required."),
			UNSUPPORTED_CURRENCY: __("Only VND is supported in this demo version."),
			UNSUPPORTED_COMPANY_CURRENCY: __("The company's accounting currency is not VND; this demo version evaluates VND companies only."),
			FINANCE_BOOK_NOT_SUPPORTED: __("Finance Book scoping is not supported in this version."),
			HISTORY_INSUFFICIENT: __("No valid prior-month observation exists for this company, so a baseline comparison is not possible. Nothing was fabricated."),
			BASELINE_DENOMINATOR_INVALID: __("The prior month has a verified zero receivables balance, so the ratio baseline is undefined."),
			CURRENT_DENOMINATOR_INVALID: __("The current cutoff has a verified zero receivables balance, so the ratio is undefined."),
			ZERO_DENOMINATOR: __("There is no positive future payables balance at this cutoff, so a due-share cannot be computed."),
			INVALID_DENOMINATOR: __("The denominator for this evaluation is invalid; the evaluation stopped fail-closed."),
			INCOMPLETE_DUE_DATE_COVERAGE: __("A positive invoice is missing a usable due date, so the due window cannot be evaluated completely."),
			UNSUPPORTED_ALLOCATION_SCOPE: __("This purchase invoice's payable spread across multiple accounts without proven allocation; this demo version cannot evaluate it deterministically."),
			UNSUPPORTED_MULTI_SCHEDULE: __("This purchase invoice has multiple installment rows; this demo version cannot evaluate it deterministically."),
			CONFLICTING_OBSERVATION: __("The source returned contradictory rows for the same invoice; the evaluation stopped fail-closed."),
			INCONSISTENT_DATA: __("Source data is internally inconsistent; the evaluation stopped fail-closed."),
			SOURCE_UNAVAILABLE: __("The financial source is temporarily unavailable. Retry later; nothing was fabricated."),
			SOURCE_TIMEOUT: __("The financial source took too long to respond. Retry later."),
			SOURCE_INVALID: __("The source returned malformed data; the evaluation stopped fail-closed."),
			UNSUPPORTED_SOURCE_VERSION: __("The source contract version is not the pinned version required by this method."),
			POLICY_NOT_APPROVED: __("The deterministic inputs are valid, but the applicable policy is not approved, so no finding or severity can be produced."),
			POLICY_UNAVAILABLE: __("The applicable policy could not be resolved; no finding or severity can be produced."),
			INVALID_POLICY_CONFIG: __("The active policy configuration is invalid; the evaluation stopped fail-closed.")
		};
		return map[code] || __("The evaluation stopped for the reason code shown.");
	}

	status_label(status) {
		const map = {
			OK: __("Evaluation completed"),
			INCONCLUSIVE: __("Inconclusive"),
			FORBIDDEN: __("Access denied"),
			VALIDATION_ERROR: __("Needs attention"),
			SOURCE_ERROR: __("Source error"),
			POLICY_PENDING: __("Policy pending")
		};
		return map[status] || status;
	}

	// ---------- evaluation ----------
	evaluate() {
		const me = this;
		if (this.in_flight) return; // no double-submit
		const company = this.company_field.get_value();
		const signal_id = this.signal_field.get_value();
		const as_of_date = this.as_of_field.get_value();
		if (!company) {
			this.clear_result(__("Select a company to evaluate."));
			return;
		}
		if (!as_of_date) {
			this.clear_result(__("Select an as-of date to evaluate."));
			return;
		}
		this.current_company = company;
		this.in_flight = true;
		this.page.set_primary_action(__("Evaluating…"), function () {}, "octicon octicon-sync");
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
				me.in_flight = false;
				me.restore_primary_action();
				me.render_result(r.message || r);
			})
			.fail(function () {
				me.in_flight = false;
				me.restore_primary_action();
				me.render_transport_error();
			});
	}

	restore_primary_action() {
		const me = this;
		this.page.set_primary_action(__("Evaluate Signal"), function () {
			me.evaluate();
		}, "octicon octicon-pulse");
	}

	render_transport_error() {
		const box = this.el("div", "rs-panel rs-panel-error");
		box.append(this.el("div", "rs-panel-title", __("Request failed")));
		box.append(this.el("div", null,
			__("The evaluation request could not be delivered (transport error). No result was produced; nothing was fabricated.")));
		this.set_state(box);
	}

	// ---------- rendering ----------
	render_result(wire) {
		this.set_state(null);
		this.result_box.empty();
		if (!wire || !wire.status) {
			this.render_transport_error();
			return;
		}
		const panel = this.el("div", "rs-panel");
		panel.append(this.render_status_header(wire));
		panel.append(this.render_reason(wire));
		if (wire.status === "FORBIDDEN") {
			this.result_box.append(panel);
			return; // generic denial: nothing else on the wire
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
		const header = this.el("div", "rs-header");
		const chipClass = {
			OK: "rs-chip-ok",
			INCONCLUSIVE: "rs-chip-inconclusive",
			FORBIDDEN: "rs-chip-denied",
			VALIDATION_ERROR: "rs-chip-warn",
			SOURCE_ERROR: "rs-chip-error",
			POLICY_PENDING: "rs-chip-pending"
		}[wire.status] || "rs-chip-inconclusive";
		header.append(this.el("span", "rs-chip " + chipClass, this.status_label(wire.status)));
		if (wire.status === "OK" && wire.finding === "TRIGGERED" && wire.severity) {
			header.append(this.el("span", "rs-chip " + (wire.severity === "HIGH" ? "rs-chip-high" : "rs-chip-watch"), wire.severity === "HIGH" ? __("HIGH") : __("WATCH")));
		}
		if (wire.status === "OK" && wire.finding === "BENIGN") {
			header.append(this.el("span", "rs-chip rs-chip-benign", __("BENIGN — no threshold breach")));
		}
		if (wire.as_of_date) {
			header.append(this.el("span", "rs-meta", __("as of {0}", [wire.as_of_date])));
		}
		if (wire.signal_id) {
			header.append(this.el("span", "rs-meta", wire.signal_id === "AR_OVERDUE_SPIKE" ? __("AR Overdue Spike") : __("AP Due Cluster")));
		}
		return header;
	}

	render_reason(wire) {
		const box = this.el("div", "rs-reason");
		box.append(this.el("div", "rs-panel-title", __("Why")));
		box.append(this.el("div", "rs-reason-text", this.reason_text(wire.reason_code)));
		return box;
	}

	render_evaluation(wire) {
		const box = this.el("div", "rs-section");
		box.append(this.el("div", "rs-panel-title", __("What happened")));
		if (wire.signal_id === "AR_OVERDUE_SPIKE") {
			box.append(this.kv_row(__("Current overdue ratio"), wire.observed ? wire.observed.value : null, "rs-num"));
			box.append(this.kv_row(__("Baseline ratio ({0})", [wire.baseline ? wire.baseline.cutoff : ""]), wire.baseline ? wire.baseline.value : null, "rs-num"));
			box.append(this.kv_row(__("Change"), wire.delta_pp !== null && wire.delta_pp !== undefined ? wire.delta_pp + " pp" : null, "rs-num"));
			box.append(this.kv_row(__("Current net AR total"), wire.observed ? wire.observed.supporting_amount : null, "rs-num"));
			box.append(this.kv_row(__("Thresholds (approved demo policy)"),
				wire.rule ? wire.rule.threshold + " / " + wire.rule.high_threshold + " pp (WATCH / HIGH, breach at ≥)" : null));
		} else {
			// Presentation-only percentage from the server-owned 4dp ratio string.
			let pct = null;
			if (wire.observed && wire.observed.value !== null && wire.observed.value !== undefined) {
				pct = (parseFloat(wire.observed.value) * 100).toFixed(2) + "%";
			}
			box.append(this.kv_row(__("Share of future payables due in window"), pct, "rs-num"));
			box.append(this.kv_row(__("Due amount in window (N)"), wire.observed ? wire.observed.supporting_amount : null, "rs-num"));
			box.append(this.kv_row(__("Positive future payables (D)"), wire.numerator_denominator_detail || null));
			box.append(this.kv_row(__("Thresholds (approved demo policy)"),
				wire.rule ? (parseFloat(wire.rule.threshold) * 100).toFixed(1) + "% / " + (parseFloat(wire.rule.high_threshold) * 100).toFixed(1) + "% (WATCH / HIGH, breach at ≥)" : null));
			if (wire.rule && wire.rule.window_start && wire.rule.window_end) {
				box.append(this.kv_row(__("Due window"), wire.rule.window_start + " → " + wire.rule.window_end));
			}
		}
		return box;
	}

	render_counts(wire) {
		if (wire.count_positive_vouchers === null || wire.count_positive_vouchers === undefined) return document.createDocumentFragment();
		const box = this.el("div", "rs-section");
		box.append(this.kv_row(__("Distinct vouchers (all positive future)"), String(wire.count_positive_vouchers)));
		if (wire.count_due_vouchers !== null && wire.count_due_vouchers !== undefined) {
			box.append(this.kv_row(__("Distinct vouchers (in due window)"), String(wire.count_due_vouchers)));
		}
		return box;
	}

	render_materiality(wire) {
		if (!wire.rule || wire.rule.floor === null || wire.rule.floor === undefined) return document.createDocumentFragment();
		const box = this.el("div", "rs-section");
		const definitionLabel = wire.rule.materiality_definition === "CURRENT_NET_AR_TOTAL"
			? __("current net AR total")
			: __("due-window amount (N)");
		const floorText = parseFloat(wire.rule.floor) === 0
			? __("0.00 VND (demo floor: no materiality filtering is applied)")
			: wire.rule.floor + " VND";
		box.append(this.kv_row(__("Materiality floor"), floorText));
		box.append(this.el("div", "rs-note text-muted",
			__("The floor gates the {0}, not the overdue money itself.", [definitionLabel])));
		return box;
	}

	render_evidence(wire) {
		const me = this;
		const box = this.el("div", "rs-section");
		box.append(this.el("div", "rs-panel-title", __("Evidence")));
		const refs = wire.evidence || [];
		if (!refs.length) {
			box.append(this.el("div", "rs-note text-muted",
				__("No evidence snapshot is attached to this outcome.")));
			return box;
		}
		const note = this.el("div", "rs-note text-muted",
			__("Opening evidence re-verifies your access on the server every time; a reference is never an access token."));
		box.append(note);
		refs.forEach(function (ref) {
			const btn = me.el("button", "btn btn-xs btn-secondary rs-evidence-btn");
			btn.type = "button";
			btn.setAttribute("aria-label", __("Open evidence snapshot"));
			btn.textContent = __("Open evidence snapshot");
			btn.addEventListener("click", function () {
				me.open_evidence(ref.ref);
			});
			const row = me.el("div", "rs-evidence-row");
			row.append(btn, me.el("span", "rs-meta", ref.kind + " · " + (ref.as_of_date || "")));
			box.append(row);
		});
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
				const box = me.el("div", "rs-banner " + (res.status === "MATCH" ? "rs-banner-ok" : res.status === "FORBIDDEN" ? "rs-banner-warning" : "rs-banner-info"));
				const label = {
					MATCH: __("Evidence replayed and verified: the source is unchanged since capture (MATCH)."),
					RESTATED: __("The source has changed since the snapshot was captured (RESTATED). The current source values are shown; the original evaluation is unchanged."),
					UNAVAILABLE: __("The source could not be replayed right now (UNAVAILABLE). The original evaluation is unchanged."),
					FORBIDDEN: __("Evidence access was denied (FORBIDDEN). The original evaluation is unchanged.")
				}[res.status] || res.status;
				box.append(me.el("div", null, label));
				if (res.payload) {
					const keys = Object.keys(res.payload);
					keys.forEach(function (key) {
						box.append(me.kv_row(key, String(res.payload[key])));
					});
				}
				me.result_box.find(".rs-evidence-live").remove();
				me.result_box.append(box.addClass("rs-evidence-live"));
			})
			.fail(function () {
				frappe.msgprint(__("Evidence replay failed (transport error). The original evaluation is unchanged."));
			});
	}

	render_explanation(wire) {
		const box = this.el("div", "rs-section");
		const exp = wire.explanation || {};
		if (exp.status === "AVAILABLE" && exp.text) {
			box.append(this.el("div", "rs-panel-title", __("AI explanation")));
			box.append(this.el("div", "rs-explanation", exp.text));
		} else if (exp.status === "UNAVAILABLE") {
			box.append(this.el("div", "rs-banner rs-banner-warning",
				this.el("div", null, __("AI explanation is unavailable. The deterministic result above remains final and valid; only the narrative is missing."))));
		}
		return box;
	}

	render_limitations(wire) {
		const lims = wire.limitations || [];
		if (!lims.length) return document.createDocumentFragment();
		const box = this.el("div", "rs-section");
		box.append(this.el("div", "rs-panel-title", __("Limitations")));
		lims.forEach((lim, i) => {
			box.append(this.el("div", "rs-note", "· " + lim));
			void i;
		});
		return box;
	}

	render_next_actions(wire) {
		const actions = wire.next_check_actions || [];
		if (!actions.length) return document.createDocumentFragment();
		const box = this.el("div", "rs-section");
		box.append(this.el("div", "rs-panel-title", __("What to inspect next")));
		actions.forEach(function (action) {
			const item = document.createElement("div");
			item.className = "rs-next";
			const bullet = document.createElement("span");
			bullet.textContent = "→ ";
			const text = document.createElement("span");
			text.textContent = __(action);
			item.append(bullet, text);
			box.append(item);
		});
		return box;
	}

	render_debug(wire) {
		const trace = wire.stage_trace || [];
		if (!trace.length) return document.createDocumentFragment();
		const box = this.el("div", "rs-debug text-muted");
		box.append(this.el("span", null,
			__("Pipeline stages entered: {0} · policy {1} · method {2}", [trace.join(" → "), wire.policy_version || "—", wire.method_version || "—"])));
		return box;
	}
};
