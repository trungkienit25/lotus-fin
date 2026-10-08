"""
Lotus Fin AI007 — Financial Copilot Orchestrator.
Core Engine routing natural language requests to specific deterministic modules.
"""

from typing import Dict, Any, Tuple
from decimal import Decimal

from .models import (
    CopilotRequest,
    CopilotResponse,
    CopilotAction,
    IntentType,
    ConversationContext
)

# Import các module tài chính tất định từ hệ thống Lotus Fin
# Dùng try-except để mock khi chạy test độc lập
try:
    from lotus_fin.modules.f005_financing.models import FinancingProduct as FinancingProductParams
    from lotus_fin.modules.f005_financing.matcher import FinancingDecisionEngine as FinancingMatcher
    
    from lotus_fin.modules.f006_repayment.models import LoanTerms, AmortizationMethod, StressScenarioParams, StressType
    from lotus_fin.modules.f006_repayment.engine import RepaymentEngine
    from lotus_fin.modules.f006_repayment.stress import StressSimulationEngine
except ImportError:
    try:
        from lotus_fin.AI005.models import FinancingProductParams
        from lotus_fin.AI005.matcher import FinancingMatcher
        
        from lotus_fin.AI006.models import LoanTerms, AmortizationMethod, StressScenarioParams, StressType
        from lotus_fin.AI006.engine import RepaymentEngine
        from lotus_fin.AI006.stress import StressSimulationEngine
    except ImportError:
        pass


class CopilotOrchestrator:
    """
    Điều phối viên trung tâm (Copilot Orchestrator).
    Nhận tin nhắn của user, phân tích ý định (NLU/Intent), 
    gọi các module con (AI005, AI006) và tổng hợp kết quả trả về.
    """

    def __init__(self):
        # Thông thường ở đây sẽ khởi tạo model NLP hoặc LLM client (ví dụ: OpenAI, Gemini)
        # Trong bản MVP này, ta giả lập logic Rule-based NLU để minh họa luồng orchestrator.
        pass

    def process_request(self, request: CopilotRequest) -> CopilotResponse:
        """Điểm vào chính của Copilot."""
        
        # 1. Phân tích ý định (Intent Extraction)
        intent, entities = self._extract_intent(request.message)
        
        actions_taken = []
        ui_widgets = []
        reply_msg = ""
        suggested_steps = []

        # 2. Định tuyến (Routing) tới các module chức năng
        if intent == IntentType.FINANCING_SUPPORT:
            reply_msg, act, widget = self._handle_financing(entities)
            if act: actions_taken.append(act)
            if widget: ui_widgets.append(widget)
            suggested_steps = ["Xem chi tiết các gói vay", "Mô phỏng lịch trả nợ cho gói vay này"]

        elif intent == IntentType.REPAYMENT_STRESS:
            reply_msg, act, widget = self._handle_stress_test(entities)
            if act: actions_taken.append(act)
            if widget: ui_widgets.append(widget)
            suggested_steps = ["Điều chỉnh lãi suất stress test", "Xem biểu đồ dòng tiền"]

        else:
            # Fallback
            reply_msg = "Tôi là Trợ lý Tài chính Lotus Fin. Tôi có thể giúp bạn tìm kiếm gói vay doanh nghiệp (AI005) hoặc mô phỏng lịch trả nợ và kiểm tra rủi ro lãi suất (AI006). Bạn cần hỗ trợ gì?"
            suggested_steps = ["Tìm gói vay 1 tỷ", "Mô phỏng trả nợ vay 500 triệu lãi 10%"]

        # 3. Đóng gói kết quả (Response Formatting)
        return CopilotResponse(
            session_id=request.session_id,
            intent=intent,
            reply_message=reply_msg,
            actions_taken=actions_taken,
            suggested_next_steps=suggested_steps,
            ui_widgets=ui_widgets,
            data_mode="simulation"
        )

    # ------------------------------------------------------------------
    # INTERNAL METHODS
    # ------------------------------------------------------------------

    def _extract_intent(self, message: str) -> Tuple[IntentType, Dict[str, Any]]:
        """
        Mock NLU: Trích xuất ý định và thực thể (entities) từ tin nhắn.
        Thực tế: Dùng LLM prompt để extract structured JSON.
        """
        msg_lower = message.lower()
        
        if "vay" in msg_lower and "tìm" in msg_lower or "gói vay" in msg_lower:
            # Trích xuất số tiền vay (mock)
            amount = 1000000000  # Default 1 Tỷ
            if "500 triệu" in msg_lower: amount = 500000000
            if "2 tỷ" in msg_lower: amount = 2000000000
            
            return IntentType.FINANCING_SUPPORT, {"requested_amount": amount, "currency": "VND"}
            
        elif "trả nợ" in msg_lower or "lịch" in msg_lower or "stress" in msg_lower or "lãi suất tăng" in msg_lower:
            # Trích xuất thông số (mock)
            amount = 1000000000
            rate = 0.10
            term = 12
            if "lãi suất tăng" in msg_lower:
                return IntentType.REPAYMENT_STRESS, {"principal": amount, "rate": rate, "term": term, "stress_bps": 200}
            return IntentType.REPAYMENT_STRESS, {"principal": amount, "rate": rate, "term": term, "stress_bps": 0}
            
        return IntentType.GENERAL_QA, {}

    def _handle_financing(self, entities: Dict[str, Any]) -> Tuple[str, CopilotAction, Dict[str, Any]]:
        """Điều phối module AI005 - Financing."""
        try:
            # Khởi tạo Matcher của AI005
            matcher = FinancingMatcher()
            params = FinancingProductParams(
                requested_amount=Decimal(str(entities.get("requested_amount", 1000000000))),
                currency=entities.get("currency", "VND")
            )
            
            # Tính toán
            matches = matcher.match_products(params)
            
            if not matches:
                return "Không tìm thấy gói vay phù hợp.", None, None

            best_match = matches[0]
            
            action = CopilotAction(
                module_called="AI005",
                action_type="match_financing",
                parameters={"requested_amount": float(params.requested_amount)},
                result_summary=f"Found {len(matches)} matches. Best match: {best_match.product_id}"
            )
            
            widget = {
                "widget_type": "FINANCING_TABLE",
                "data": [{"product_id": m.product_id, "score": float(m.match_score), "max_amount": float(m.max_amount)} for m in matches[:3]]
            }
            
            reply = f"Tôi đã tìm thấy {len(matches)} gói vay phù hợp. Gói tốt nhất là **{best_match.product_id}** với điểm phù hợp {float(best_match.match_score)*100:.1f}%. Hạn mức tối đa: {float(best_match.max_amount):,.0f} VND."
            
            return reply, action, widget
            
        except Exception as e:
            return f"Lỗi khi gọi module AI005: {str(e)}", None, None

    def _handle_stress_test(self, entities: Dict[str, Any]) -> Tuple[str, CopilotAction, Dict[str, Any]]:
        """Điều phối module AI006 - Repayment / Stress."""
        try:
            principal = Decimal(str(entities.get("principal", 1000000000)))
            rate = Decimal(str(entities.get("rate", 0.10)))
            term = entities.get("term", 12)
            stress_bps = entities.get("stress_bps", 0)
            
            terms = LoanTerms(
                principal=principal,
                annual_rate=rate,
                term_months=term,
                amortization_method=AmortizationMethod.EQUAL_INSTALLMENT
            )
            
            if stress_bps > 0:
                # Gọi Stress Engine
                stress_engine = StressSimulationEngine()
                params = StressScenarioParams(stress_type=StressType.RATE_SHOCK, rate_shock_bps=stress_bps)
                result = stress_engine.run_stress_test(terms, params)
                
                action = CopilotAction(
                    module_called="AI006",
                    action_type="stress_test",
                    parameters={"principal": float(principal), "stress_bps": stress_bps},
                    result_summary="Completed rate shock stress test"
                )
                widget = {
                    "widget_type": "STRESS_COMPARISON",
                    "data": [k for k in result.comparison_kpis]
                }
                
                # Trích xuất logic so sánh
                interest_kpi = next((k for k in result.comparison_kpis if k.kpi_name == "Total Interest"), None)
                added_cost = interest_kpi.absolute_change if interest_kpi else 0
                
                reply = f"Tôi đã chạy kịch bản Stress Test (Tăng {stress_bps} bps lãi suất). Tổng lãi phải trả của bạn sẽ tăng thêm **{added_cost:,.0f} VND** so với kịch bản gốc."
                
            else:
                # Gọi Repayment Engine thông thường
                engine = RepaymentEngine()
                result = engine.calculate_schedule(terms)
                
                action = CopilotAction(
                    module_called="AI006",
                    action_type="repayment_schedule",
                    parameters={"principal": float(principal), "rate": float(rate)},
                    result_summary="Generated base schedule"
                )
                widget = {
                    "widget_type": "REPAYMENT_SCHEDULE",
                    "data": {"summary": result.summary, "periods": len(result.payment_schedule)}
                }
                
                reply = f"Tôi đã lập lịch trả nợ cho khoản vay {principal:,.0f} VND (lãi {float(rate)*100}%/năm, {term} tháng). Mỗi tháng bạn cần trả trung bình **{result.summary['average_monthly_payment']:,.0f} VND**."
            
            return reply, action, widget
            
        except Exception as e:
            return f"Lỗi khi gọi module AI006: {str(e)}", None, None
