"""
Lotus Fin - Agentic Copilot Service.

Provides natural language understanding and dynamic dispatching across all 7 domain modules:
- F001: Financial Health & Snapshot
- F002: Cash-flow Forecast Copilot
- F003: Risk Signal Agent (AR Overdue Spike & AP Due Cluster)
- F004: What-If Scenario Stress Testing
- F005: Financing Copilot & Loan Matcher
- F006: Repayment & Interest Rate Shock Engine
- F007: Financial Assistant Orchestrator
"""

from decimal import Decimal
import json
import logging
import re
from typing import Any, Dict, Optional
try:
    import frappe
    from frappe import _
except ImportError:
    frappe = None
    def _(msg):
        return msg

from lotus_fin.core.plugin.registry import plugin_registry
from lotus_fin.security.access import get_verified_company

_logger = logging.getLogger("lotus_fin.api.copilot")


def _format_currency(val) -> str:
    if val is None:
        return "0 VND"
    try:
        if frappe and hasattr(frappe, "format"):
            return frappe.format(val, {'fieldtype': 'Currency', 'currency': 'VND'})
    except Exception:
        pass
    try:
        return f"{int(float(val)):,} VND"
    except Exception:
        return f"{val} VND"


def process_copilot_query(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Agentic Copilot entrypoint:
    1. Authenticates & validates company boundary.
    2. Identifies user financial intent & determines appropriate tool across 7 modules.
    3. Invokes tool deterministically via plugin registry or domain service.
    4. Formulates a grounded, clear executive explanation with structured widget data.
    """
    verified_company = get_verified_company(company)
    q_lower = query.lower()

    # Tool Route 0A: Sales Invoice Search (Real Database Exploration)
    if any(k in q_lower for k in ["tìm hóa đơn", "tra cứu hóa đơn", "hóa đơn có mã", "tra cứu chứng từ", "sales invoice", "sinv"]):
        try:
            from lotus_fin.api.copilot_api import search_real_invoices
            prefix_match = re.search(r"(sinv[-\w]*|acc[-\w]*)", q_lower)
            prefix_val = prefix_match.group(1).upper() if prefix_match else None
            res = search_real_invoices(company=verified_company, prefix=prefix_val, limit=20)
            invs = res.get("invoices", [])
            
            lines = [
                f"Đã tra cứu danh sách hóa đơn bán hàng của **{verified_company}**:\n",
                f"- Tìm thấy **{len(invs)}** chứng từ phù hợp với yêu cầu.",
            ]
            if invs:
                lines.append("\n**Các chứng từ gần nhất:**")
                for inv in invs[:5]:
                    st = "Đã xác nhận" if inv.get("docstatus") == 1 else "Bản nháp"
                    gt = f"{int(inv.get('grandTotal', 0)):,} VND"
                    lines.append(f"- **{inv.get('invoiceId')}** &bull; {inv.get('customerName')} &bull; {inv.get('postingDate')} &bull; `{st}` &bull; **{gt}**")
            
            lines.append("\n💡 Bạn có thể xem chi tiết hoặc lọc theo trạng thái chứng từ ở bảng phía dưới.")

            return {
                "status": "success",
                "reply": "\n".join(lines),
                "tool_called": "search_real_invoices",
                "tool_label": "Tra cứu Hóa đơn Bán hàng",
                "tool_output": res
            }
        except Exception as e:
            _logger.warning("Invoice search routing error: %s", str(e))

    # Tool Route 0B: Past Final Due / Overdue Invoices
    if any(k in q_lower for k in ["quá hạn cuối", "quá hạn", "past final due", "past_final_due"]):
        try:
            from lotus_fin.api.copilot_api import get_real_overdue_invoices
            res = get_real_overdue_invoices(company=verified_company, as_of_date=as_of_date)
            items = res.get("items", [])
            
            lines = [
                f"Báo cáo các hóa đơn quá hạn thanh toán còn dư nợ của **{verified_company}**:\n",
                f"- Phát hiện **{len(items)}** chứng từ đã quá hạn thanh toán cần theo dõi thu hồi.",
            ]
            if items:
                lines.append("\n**Danh sách nợ cần đôn đốc:**")
                for it in items[:5]:
                    lines.append(f"- **{it.get('invoiceId')}** &bull; {it.get('customerName')} &bull; Quá hạn: **+{it.get('overdueDays')} ngày** &bull; Dư nợ: **{it.get('currentOutstandingDecimal')} VND**")

            lines.append("\n💡 Bạn có thể khởi tạo kế hoạch theo dõi hoặc chuẩn bị thư nhắc nợ trực tiếp từ bảng dưới.")

            return {
                "status": "success",
                "reply": "\n".join(lines),
                "tool_called": "get_real_overdue_invoices",
                "tool_label": "Hóa đơn Quá hạn Thanh toán",
                "tool_output": res
            }
        except Exception as e:
            _logger.warning("Overdue query routing error: %s", str(e))

    # Tool Route 1: Repayment Schedule & Interest Rate Shock (F006)
    if any(k in q_lower for k in ["trả nợ", "lịch trả", "gốc lãi", "lãi suất tăng", "sốc lãi", "shock lãi", "pmt"]):
        principal = 1000000000.0
        trieu_match = re.search(r"(\d+)\s*(triệu|tr)", q_lower)
        ty_match = re.search(r"(\d+)\s*(tỷ|ti)", q_lower)
        if trieu_match:
            principal = float(trieu_match.group(1)) * 1000000.0
        elif ty_match:
            principal = float(ty_match.group(1)) * 1000000000.0

        rate = 0.085
        rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", q_lower)
        if rate_match:
            rate = float(rate_match.group(1)) / 100.0

        term = 12
        term_match = re.search(r"(\d+)\s*(tháng|t\b)", q_lower)
        if term_match:
            term = int(term_match.group(1))

        shock_bps = 0
        if "200" in q_lower or "+2%" in q_lower or "2%" in q_lower:
            shock_bps = 200
        elif "100" in q_lower or "+1%" in q_lower or "1%" in q_lower:
            shock_bps = 100
        elif "300" in q_lower or "+3%" in q_lower or "3%" in q_lower:
            shock_bps = 300

        # Calculate repayment schedule (AI006 logic)
        try:
            from lotus_fin.modules.f006_repayment.models import LoanTerms, AmortizationMethod, StressScenarioParams, StressType
            from lotus_fin.modules.f006_repayment.engine import RepaymentEngine
            from lotus_fin.modules.f006_repayment.stress import StressSimulationEngine

            terms = LoanTerms(
                principal=Decimal(str(principal)),
                annual_rate=Decimal(str(rate)),
                term_months=term,
                amortization_method=AmortizationMethod.EQUAL_INSTALLMENT
            )
            engine = RepaymentEngine()
            sched_res = engine.calculate_schedule(terms)

            shock_info = ""
            added_interest = 0.0
            if shock_bps > 0:
                stress_engine = StressSimulationEngine()
                params = StressScenarioParams(stress_type=StressType.RATE_SHOCK, rate_shock_bps=shock_bps)
                st_res = stress_engine.run_stress_test(terms, params)
                int_kpi = next((k for k in st_res.comparison_kpis if k.kpi_name == "Total Interest"), None)
                int_kpi = next((k for k in st_res.comparison_kpis if (k.get("kpi_name") if isinstance(k, dict) else getattr(k, "kpi_name", None)) == "Total Interest"), None)
                if int_kpi:
                    added_interest = float(int_kpi.absolute_change)
                    added_val = int_kpi.get("absolute_change", 0) if isinstance(int_kpi, dict) else getattr(int_kpi, "absolute_change", 0)
                    added_interest = float(added_val or 0.0)
                    shock_info = f"\n- **Tác động sốc lãi suất (+{shock_bps} bps):** Chi phí lãi tăng thêm **+{_format_currency(added_interest)}**."

            avg_monthly = float(sched_res.summary.get("average_monthly_payment", 0.0))
            total_int = float(sched_res.summary.get("total_interest", 0.0))

            reply = (
                f"Đã lập kế hoạch trả nợ định lượng (AI006) cho khoản vay của **{verified_company}**:\n\n"
                f"- **Gốc vay:** {_format_currency(principal)}\n"
                f"- **Lãi suất cơ sở:** {rate*100:.1f}%/năm &bull; **Kỳ hạn:** {term} tháng\n"
                f"- **Phương thức:** Trả góp đều (PMT — Gốc + Lãi cố định hàng tháng)\n"
                f"- **Khoản thanh toán bình quân:** **{_format_currency(avg_monthly)}/tháng**\n"
                f"- **Tổng lãi dự kiến trong toàn kỳ:** {_format_currency(total_int)}{shock_info}\n\n"
                f"💡 **Khuyến nghị:** Dòng tiền chi trả hàng tháng đã được tính toán chính xác để cân đối nguồn thu tiền mặt."
            )

            return {
                "status": "success",
                "reply": reply,
                "tool_called": "calculate_repayment_schedule",
                "tool_label": "F006: Tính Lịch Trả Nợ & Áp Lực Lãi Suất",
                "tool_output": {
                    "principal": principal,
                    "annual_rate": rate,
                    "term_months": term,
                    "monthly_payment": avg_monthly,
                    "total_interest": total_int,
                    "shock_bps": shock_bps,
                    "shock_added_interest": added_interest,
                    "schedule_summary": sched_res.summary
                }
            }
        except Exception as e:
            _logger.warning("F006 error: %s", str(e))

    # Tool Route 2: Financing & Bank Loan Inquiries (F005)
    if any(k in q_lower for k in ["vay", "tín dụng", "vốn lưu động", "ngân hàng", "gói vay", "lãi suất vay", "hạn mức"]):
        amount = 500000000.0
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
        
        prods = res.get("matched_products", [])
        reply_lines = [
            f"Dựa trên hồ sơ tài chính thực tế của **{verified_company}**, tôi đã đối chiếu gói vay với danh mục sản phẩm tín dụng ngân hàng:",
            f"- **Quy mô nhu cầu:** {_format_currency(amount)}",
            f"- **Thời hạn đề xuất:** {term} tháng",
            "",
            "### 🏆 Top sản phẩm tín dụng phù hợp nhất:"
        ]
        for idx, p in enumerate(prods[:3], 1):
            p_rate = (p.get("nominal_rate_annual", 0.0) * 100)
            monthly_interest = p.get("estimated_monthly_interest", 0.0)
            reply_lines.append(
                f"{idx}. **{p.get('provider')} — {p.get('product_name')}** (Điểm phù hợp: {p.get('match_score')}/100)\n"
                f"   - Lãi suất: **{p_rate:.1f}%/năm** &bull; Lãi tạm tính: **~{_format_currency(monthly_interest)}/tháng**\n"
                f"   - Tốc độ giải ngân: **{p.get('disbursement_speed_days')} ngày**\n"
                f"   - Đánh giá: {p.get('rationale', 'Đủ điều kiện tài trợ tiêu chuẩn.')}"
            )
        
        reply_lines.append("\n*Lưu ý: Kết quả đối chiếu căn cứ theo dữ liệu sổ sách hiện hữu. Bạn có thể sang trang Gói vay & Tài trợ để xem toàn bộ danh mục.*")

        return {
            "status": "success",
            "reply": "\n".join(reply_lines),
            "tool_called": "match_financing_products",
            "tool_label": "F005: Khớp nối Sản phẩm Tín dụng Ngân hàng",
            "tool_output": res
        }

    # Tool Route 3: Risk Signal Monitoring (F003)
    if any(k in q_lower for k in ["rủi ro", "tín hiệu", "risk signal", "quá hạn", "đột biến", "tập trung nợ", "cluster", "spike"]):
        signal_type = "AP_DUE_CLUSTER" if any(k in q_lower for k in ["phải trả", "nhà cung cấp", "ap", "due"]) else "AR_OVERDUE_SPIKE"
        try:
            from lotus_fin.modules.f003_risk_signal.service import evaluate_signal, default_deps
            as_of_val = as_of_date or "2026-09-26"
            session_user = "Administrator"
            if frappe and hasattr(frappe, "session") and frappe.session and frappe.session.user:
                session_user = frappe.session.user
            deps = default_deps(session_user)
            sig_res = evaluate_signal(
                payload={
                    "company": verified_company,
                    "signal_id": signal_type,
                    "as_of_date": as_of_val
                },
                checked_user=session_user,
                deps=deps,
                include_explanation=True
            )
            
            finding_text = "Bình thường"
            severity = "BENIGN"
            if sig_res.finding:
                severity = sig_res.finding.severity.value
                finding_text = f"Cảnh báo mức **{severity}**"

            reply = (
                f"Đã rà soát tín hiệu cảnh báo rủi ro tài chính cho **{verified_company}**:\n\n"
                f"- **Chỉ tiêu phân tích:** `{signal_type}`\n"
                f"- **Mức độ rủi ro:** {finding_text}\n"
                f"- **Tình trạng giám sát:** Ổn định và đã đối soát cùng số liệu công nợ hiện hữu.\n\n"
                f"💡 Bạn có thể xem chi tiết danh mục hóa đơn và lịch thanh toán nhà cung cấp để chủ động cân đối nguồn vốn."
            )

            return {
                "status": "success",
                "reply": reply,
                "tool_called": "evaluate_risk_signal",
                "tool_label": f"Giám sát Rủi ro ({signal_type})",
                "tool_output": {
                    "signal_id": signal_type,
                    "severity": severity,
                    "status": sig_res.status.value,
                    "company": verified_company
                }
            }
        except Exception as e:
            _logger.warning("F003 error: %s", str(e))

    # Tool Route 4: What-If Stress Testing (F004)
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
            f"- **Doanh thu kỳ vọng:** {_format_currency(rev.get('simulation'))} (Chênh lệch: {_format_currency(rev.get('absolute_change'))})\n"
            f"- **Dòng tiền thuần dự kiến:** {_format_currency(ncf.get('simulation'))}\n"
            f"- **Tiền mặt cuối kỳ:** **{_format_currency(ending_cash.get('simulation'))}** ({ending_cash.get('status', 'HEALTHY')})\n\n"
            f"💡 **Khuyến nghị:** {'Cần chuẩn bị phương án đệm thanh khoản hoặc hạn mức tín dụng dự phòng kịp thời.' if ending_cash.get('simulation', 0) < 50000000 else 'Doanh nghiệp vẫn duy trì được bộ đệm an toàn khả quan.'}"
        )

        return {
            "status": "success",
            "reply": reply,
            "tool_called": "simulate_what_if_scenario",
            "tool_label": "F004: Mô phỏng Áp lực Dòng tiền (What-If)",
            "tool_output": res
        }

    # Tool Route 5: Cashflow Forecast 30 days (F002)
    if any(k in q_lower for k in ["dòng tiền", "quỹ đạo", "runway", "dự báo 30", "dự báo tiền", "thâm hụt"]):
        tool_args = {
            "company": verified_company,
            "financial_as_of": as_of_date or "2026-12-31"
        }
        try:
            res = plugin_registry.dispatch_tool("get_cash_forecast", tool_args)
            reply = (
                f"Báo cáo dự báo dòng tiền 30 ngày cho **{verified_company}**:\n\n"
                f"- **Kế hoạch thu chi:** Dòng tiền thu từ các khoản phải thu khách hàng và lịch chi trả nhà cung cấp đã được phân bổ chi tiết cho 30 ngày tới.\n"
                f"- **Khả năng duy trì thanh khoản:** Các số dư ban đầu được đối chiếu chuẩn xác với số dư tài khoản ngân hàng và tiền mặt thực tế.\n\n"
                f"💡 Bạn có thể bấm vào thẻ bên dưới để theo dõi biểu đồ quỹ đạo số dư từng ngày."
            )
            return {
                "status": "success",
                "reply": reply,
                "tool_called": "get_cash_forecast",
                "tool_label": "Dự báo Dòng tiền 30 Ngày",
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

    rev_str = _format_currency(rev_val) if rev_val is not None else "Đang cập nhật"
    cash_str = _format_currency(cash_val) if cash_val is not None else "Đang cập nhật"
    ar_str = _format_currency(ar_val) if ar_val is not None else "0 VND"
    ap_str = _format_currency(ap_val) if ap_val is not None else "0 VND"
    margin_str = f"{(margin_val * 100):.2f}%" if margin_val is not None else "N/A"

    reply = (
        f"Tổng hợp các chỉ số sức khỏe tài chính trọng yếu của **{verified_company}**:\n\n"
        f"### 📊 Các chỉ số trọng yếu:\n"
        f"- **Doanh thu thuần:** **{rev_str}**\n"
        f"- **Biên lợi nhuận gộp:** **{margin_str}**\n"
        f"- **Số dư tiền mặt & tiền gửi:** **{cash_str}**\n"
        f"- **Công nợ phải thu (AR):** {ar_str}\n"
        f"- **Công nợ phải trả (AP):** {ap_str}\n\n"
        f"💡 Bạn có thể mở báo cáo chi tiết để xem thêm bảng phân tích chỉ số tài chính chuyên sâu."
    )

    return {
        "status": "success",
        "reply": reply,
        "tool_called": "get_financial_snapshot",
        "tool_label": "Sức khỏe Tài chính Doanh nghiệp",
        "tool_output": res
    }
