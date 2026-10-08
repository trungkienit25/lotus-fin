// Lotus Fin — UI Primitive: Button (Pill-shaped, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.Button = class Button {
	/**
	 * @param {Object} opts
	 * @param {string} [opts.label]
	 * @param {string} [opts.variant] - 'primary' | 'secondary' | 'ai' | 'outline'
	 * @param {string} [opts.size] - 'sm' | 'md' | 'lg'
	 * @param {string} [opts.icon] - Icon name or emoji
	 * @param {Function} [opts.onClick]
	 * @param {string} [opts.className]
	 */
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
		const iconHtml = this.icon ? `<span class="lotus-btn-icon">${this.icon}</span>` : "";

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
