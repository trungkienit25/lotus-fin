// Lotus Fin — UI Primitive: Card (Surface Container, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.Card = class Card {
	/**
	 * @param {Object} opts
	 * @param {string} [opts.title]
	 * @param {string} [opts.subtitle]
	 * @param {string} [opts.badge]
	 * @param {string} [opts.className]
	 * @param {string|jQuery} [opts.content]
	 */
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
