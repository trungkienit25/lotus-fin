// Lotus Fin — UI Primitive: Badge (Pill-shaped Status & Tag, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.Badge = class Badge {
	/**
	 * @param {Object} opts
	 * @param {string} opts.text
	 * @param {string} [opts.variant] - 'primary' | 'success' | 'warning' | 'danger' | 'ai'
	 * @param {string} [opts.icon]
	 */
	constructor(opts = {}) {
		this.text = opts.text || "";
		this.variant = opts.variant || "primary";
		this.icon = opts.icon || "";
		this.render();
	}

	render() {
		const iconHtml = this.icon ? `<span>${this.icon}</span>` : "";
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
