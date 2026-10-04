// Lotus Fin — UI Primitive: MetricCard (KPI Visualizer, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.MetricCard = class MetricCard {
	/**
	 * @param {Object} opts
	 * @param {string} opts.label
	 * @param {string|number} opts.value
	 * @param {string} [opts.subtext]
	 * @param {string} [opts.delta]
	 * @param {string} [opts.deltaType] - 'positive' | 'negative' | 'neutral'
	 * @param {string} [opts.valueColor] - 'primary' | 'success' | 'warning' | 'danger'
	 * @param {string} [opts.className]
	 */
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
