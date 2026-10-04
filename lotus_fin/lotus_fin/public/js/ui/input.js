// Lotus Fin — UI Primitive: Input & Form Controls (Outlined, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.Input = class Input {
	/**
	 * @param {Object} opts
	 * @param {string} opts.label
	 * @param {string} [opts.type] - 'text' | 'number' | 'date'
	 * @param {any} [opts.value]
	 * @param {string} [opts.placeholder]
	 * @param {string} [opts.help]
	 * @param {Function} [opts.onChange]
	 */
	constructor(opts = {}) {
		this.label = opts.label || "";
		this.type = opts.type || "text";
		this.value = opts.value !== undefined ? opts.value : "";
		this.placeholder = opts.placeholder || "";
		this.help = opts.help || "";
		this.onChange = opts.onChange || null;
		this.render();
		this.bind_events();
	}

	render() {
		this.$el = $(`
			<div class="lotus-form-group mb-3">
				<label class="text-muted" style="font-size: 12px; font-weight: 600; margin-bottom: 4px; display: block;">
					${this.label}
				</label>
				<input type="${this.type}" class="lotus-input" placeholder="${this.placeholder}" value="${this.value}" />
				<small class="lotus-form-help text-muted" style="font-size: 11px; margin-top: 2px; display: block;">
					${this.help}
				</small>
			</div>
		`);
		this.$input = this.$el.find(".lotus-input");
	}

	bind_events() {
		if (this.onChange) {
			this.$input.on("input change", (e) => {
				this.onChange(this.$input.val(), e, this);
			});
		}
	}

	get_value() {
		return this.$input.val();
	}

	set_value(val) {
		this.$input.val(val);
		return this;
	}

	set_help(helpText) {
		this.$el.find(".lotus-form-help").text(helpText);
		return this;
	}

	appendTo(parent) {
		$(parent).append(this.$el);
		return this;
	}
};
