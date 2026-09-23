// Lotus Fin Desk Client Script Extension

frappe.provide("lotus_fin");

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		// Chỉ hiển thị nút AI khi hóa đơn đã có dữ liệu hoặc đã lưu
		if (!frm.is_new()) {
			frm.add_custom_button(__('🤖 AI Đánh giá rủi ro'), function() {
				frappe.call({
					method: "lotus_fin.api.ai_insights.analyze_invoice_risk",
					args: {
						invoice_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("AI đang phân tích lịch sử khách hàng và đánh giá rủi ro..."),
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							const res = r.message;
							let indicator = "green";
							if (res.risk_level === "MEDIUM") indicator = "orange";
							if (res.risk_level === "HIGH") indicator = "red";

							frappe.msgprint({
								title: __("Kết quả Phân tích AI"),
								indicator: indicator,
								message: `<div style="font-size: 13px; line-height: 1.6;">
									<b>Mức độ rủi ro tín dụng:</b> <span class="badge badge-${indicator}">${res.risk_level}</span><br>
									<b>Nhận định:</b> ${res.analysis}
								</div>`
							});
						}
					}
				});
			}, __("Lotus Fin AI"));
		}
	}
});

console.log("[Lotus Fin] Client extensions initialized successfully.");

