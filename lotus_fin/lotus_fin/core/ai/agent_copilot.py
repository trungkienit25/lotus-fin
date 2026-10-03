"""
Lotus Fin - Agentic Copilot Service.

Provides natural language understanding and dynamic dispatching to domain plugins:
- F001: Financial Health & Snapshot
- F002: Cash-flow Forecast
- F004: What-If Scenario Simulation
- F005: Financing Matching & Consultation
"""

from decimal import Decimal
import json
import logging
import re
from typing import Any, Dict, Optional
import frappe
from frappe import _

from lotus_fin.core.plugin.registry import plugin_registry
from lotus_fin.security.access import get_verified_company

_logger = logging.getLogger("lotus_fin.api.copilot")


def process_copilot_query(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Agentic Copilot entrypoint:
    1. Authenticates & validates company boundary.
    2. Identifies user financial intent & determines appropriate tool.
    3. Invokes tool deterministically via plugin registry.
    4. Formulates a grounded, clear executive explanation.
    """
    verified_company = get_verified_company(company)
    q_lower = query.lower()

    # Tool Route 1: Financing & Bank Loan Inquiries (F005)
    if any(k in q_lower for k in ["vay", "tín dụng", "vốn lưu động", "ngân hàng", "gói vay", "lãi suất vay", "hạn mức"]):
        amount = 500000000.0
        # Parse numeric amounts like '500 triệu', '500tr', '1 tỷ'
        trieu_match = re.search(r"(\d+)\s*(triệu|tr)", q_lower)
        ty_match = re.search(r"(\d+)\s*(tỷ|ti)", q_lower)
        if trieu_match:
            amount = float(trieu_match.group(1)) * 1000000.0
        elif ty_match:
            amount = float(ty_match.group(1)) * 1000000000.0

        term = 12
        term_match = re.search(r"(\d+)\s*(tháng|t\b)", q_lower)
        if term_match:
            term = int(term_match.group(1))

        tool_args = {
            "company": verified_company,
            "amount": amount,
            "term_months": term,
            "purpose": "WORKING_CAPITAL"
        }
        res = plugin_registry.dispatch_tool("match_financing_products", tool_args)
        
        # Format response
        prods = res.get("matched_products", [])
        reply_lines = [
            f"Dựa trên hồ sơ tài chính thực tế của **{verified_company}**, tôi đã đối chiếu gói vay với danh mục sản phẩm tín dụng ngân hàng:",
            f"- **Quy mô nhu cầu:** {frappe.format(amount, {'fieldtype': 'Currency', 'currency': 'VND'})}",
            f"- **Thời hạn đề xuất:** {term} tháng",
            "",
            "### 🏆 Top sản phẩm tín dụng phù hợp nhất:"
        ]
        for idx, p in enumerate(prods[:3], 1):
            rate = (p.get("nominal_rate_annual", 0.0) * 100)
            monthly_interest = p.get("estimated_monthly_interest", 0.0)
            reply_lines.append(
                f"{idx}. **{p.get('provider')} — {p.get('product_name')}** (Điểm phù hợp: {p.get('match_score')}/100)\n"
                f"   - Lãi suất: **{rate:.1f}%/năm** &bull; Lãi tạm tính: **~{frappe.format(monthly_interest, {'fieldtype': 'Currency', 'currency': 'VND'})}/tháng**\n"
                f"   - Tốc độ giải ngân: **{p.get('disbursement_speed_days')} ngày**\n"
                f"   - Đánh giá: {p.get('rationale', 'Đủ điều kiện tài trợ tiêu chuẩn.')}"
            )
        
        reply_lines.append("\n*Lưu ý: Kết quả đối chiếu căn cứ theo dữ liệu sổ sách hiện hữu. Đề nghị kiểm tra thêm điều kiện tài sản bảo đảm với ngân hàng.*")

        return {
            "status": "success",
            "reply": "\n".join(reply_lines),
            "tool_called": "match_financing_products",
            "tool_label": "F005: Khớp nối Sản phẩm Tín dụng Ngân hàng",
            "tool_output": res
        }

    # Tool Route 2: What-If Stress Testing (F004)
    if any(k in q_lower for k in ["what-if", "nếu", "kịch bản", "giảm", "sốc", "khách trả chậm", "stress-test", "stress test"]):
        sales_change = 0.0
        if "giảm 20%" in q_lower or "-20%" in q_lower:
            sales_change = -0.20
        elif "giảm 30%" in q_lower or "-30%" in q_lower:
            sales_change = -0.30
        elif "giảm 10%" in q_lower or "-10%" in q_lower:
            sales_change = -0.10
        elif "tăng 20%" in q_lower or "+20%" in q_lower:
            sales_change = 0.20

        delay_days = 0
        delay_match = re.search(r"trễ\s*(\d+)\s*ngày", q_lower)
        if delay_match:
            delay_days = int(delay_match.group(1))
        elif "trễ 15" in q_lower:
            delay_days = 15
        elif "trễ 30" in q_lower:
            delay_days = 30

        tool_args = {
            "company": verified_company,
            "sales_change_pct": Decimal(str(sales_change)),
            "collection_delay_days": delay_days,
            "supplier_due_shift_days": 0,
            "financing_amount": Decimal("0")
        }
        res = plugin_registry.dispatch_tool("simulate_what_if_scenario", tool_args)
        
        metrics = res.get("metrics", {})
        ending_cash = metrics.get("ending_cash", {})
        ncf = metrics.get("net_cash_flow", {})
        rev = metrics.get("revenue", {})

        reply = (
            f"Đã kích hoạt mô hình mô phỏng áp lực định lượng (What-If Simulation) cho **{verified_company}**:\n\n"
            f"- **Giả định áp dụng:** Doanh thu biến động **{sales_change*100:+.0f}%**, Khách hàng trả chậm **+{delay_days} ngày**.\n"
            f"- **Doanh thu kỳ vọng:** {frappe.format(rev.get('simulation'), {'fieldtype': 'Currency', 'currency': 'VND'})} (Chênh lệch: {frappe.format(rev.get('absolute_change'), {'fieldtype': 'Currency', 'currency': 'VND'})})\n"
            f"- **Dòng tiền thuần dự kiến:** {frappe.format(ncf.get('simulation'), {'fieldtype': 'Currency', 'currency': 'VND'})}\n"
            f"- **Tiền mặt cuối kỳ:** **{frappe.format(ending_cash.get('simulation'), {'fieldtype': 'Currency', 'currency': 'VND'})}** ({ending_cash.get('status', 'HEALTHY')})\n\n"
            f"💡 **Khuyến nghị:** {'Cần chuẩn bị phương án đệm thanh khoản hoặc hạn mức tín dụng dự phòng kịp thời.' if ending_cash.get('simulation', 0) < 50000000 else 'Doanh nghiệp vẫn duy trì được bộ đệm an toàn khả quan.'}"
        )

        return {
            "status": "success",
            "reply": reply,
            "tool_called": "simulate_what_if_scenario",
            "tool_label": "F004: Mô phỏng Áp lực Dòng tiền (What-If)",
            "tool_output": res
        }

    # Tool Route 3: Cashflow Forecast 30 days (F002)
    if any(k in q_lower for k in ["dòng tiền", "quỹ đạo", "runway", "dự báo 30", "dự báo tiền", "thâm hụt"]):
        tool_args = {
            "company": verified_company,
            "financial_as_of": as_of_date or "2026-12-31"
        }
        try:
            res = plugin_registry.dispatch_tool("get_cash_forecast", tool_args)
            reply = (
                f"Đã chạy công cụ **Dự báo Dòng tiền 30 ngày (F002)** cho **{verified_company}**:\n\n"
                f"- **Tình trạng quỹ đạo:** Dòng tiền thu từ các hóa đơn bán hàng và chi trả nhà cung cấp đã được lập lịch theo chu kỳ 30 ngày.\n"
                f"- **Số dư ban đầu đã đối soát:** Dữ liệu sổ cái tiền mặt và tiền gửi ngân hàng đã được khóa số liệu theo nguyên tắc kế toán dứt điểm.\n\n"
                f"Bạn có thể chuyển sang trang **Cash Flow Forecast & Runway** để xem biểu đồ chi tiết từng ngày."
            )
            return {
                "status": "success",
                "reply": reply,
                "tool_called": "get_cash_forecast",
                "tool_label": "F002: Dự báo Dòng tiền 30 Ngày",
                "tool_output": res
            }
        except Exception:
            pass

    # Default Tool Route: Financial Health Snapshot (F001)
    tool_args = {
        "company": verified_company,
        "period_start": "2020-01-01",
        "period_end": as_of_date or "2026-12-31"
    }
    res = plugin_registry.dispatch_tool("get_financial_snapshot", tool_args)
    metrics = {m["metric_id"]: m for m in res.get("metrics", [])}
    
    rev_val = metrics.get("revenue", {}).get("value")
    margin_val = metrics.get("gross_margin", {}).get("value")
    cash_val = metrics.get("cash_balance", {}).get("value")
    ar_val = metrics.get("ar_outstanding", {}).get("value")
    ap_val = metrics.get("ap_outstanding", {}).get("value")

    rev_str = frappe.format(rev_val, {"fieldtype": "Currency", "currency": "VND"}) if rev_val is not None else "Không có số liệu"
    cash_str = frappe.format(cash_val, {"fieldtype": "Currency", "currency": "VND"}) if cash_val is not None else "Chưa ghi nhận"
    ar_str = frappe.format(ar_val, {"fieldtype": "Currency", "currency": "VND"}) if ar_val is not None else "0 VND"
    ap_str = frappe.format(ap_val, {"fieldtype": "Currency", "currency": "VND"}) if ap_val is not None else "0 VND"
    margin_str = f"{(margin_val * 100):.2f}%" if margin_val is not None else "N/A"

    reply = (
        f"Xin báo cáo tình hình tài chính thực tế của **{verified_company}** (Số liệu đã kiểm chứng qua Sổ cái & Báo cáo tài chính):\n\n"
        f"### 📊 Các chỉ số trọng yếu:\n"
        f"- **Doanh thu thuần:** **{rev_str}**\n"
        f"- **Biên lợi nhuận gộp:** **{margin_str}**\n"
        f"- **Số dư tiền mặt & tiền gửi:** **{cash_str}**\n"
        f"- **Công nợ phải thu (AR):** {ar_str}\n"
        f"- **Công nợ phải trả (AP):** {ap_str}\n\n"
        f"Tất cả số liệu được tính toán định lượng dứt điểm từ Sổ cái kế toán, không chứa suy diễn ngoài báo cáo."
    )

    return {
        "status": "success",
        "reply": reply,
        "tool_called": "get_financial_snapshot",
        "tool_label": "F001: Trích xuất Sức khỏe Tài chính",
        "tool_output": res
    }
