// Lotus Fin — UI Primitive: Table (Clean Modern Table, Material 3)
frappe.provide("lotus_fin.ui");

lotus_fin.ui.Table = class Table {
	/**
	 * @param {Object} opts
	 * @param {Array<{key: string, label: string, align?: string, format?: Function}>} opts.columns
	 * @param {Array<Object>} [opts.data]
	 * @param {string} [opts.emptyMessage]
	 */
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
