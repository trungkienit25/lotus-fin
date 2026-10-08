// Lotus Fin — Promise-based API Client Wrapper
frappe.provide("lotus_fin.core.api");

lotus_fin.core.api.call = function (method, args = {}) {
	return new Promise((resolve, reject) => {
		frappe.call({
			method: method,
			args: args,
			callback: function (r) {
				if (r.exc) {
					reject(new Error(r.exc));
				} else {
					resolve(r.message);
				}
			},
			error: function (err) {
				reject(err);
			}
		});
	});
};
