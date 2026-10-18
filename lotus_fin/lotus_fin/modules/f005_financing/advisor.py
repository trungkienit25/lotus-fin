"""
Lotus Fin AI005 - Grounded AI Advisor & Intent Extractor for Financing Decision Support.
"""

from decimal import Decimal, ROUND_HALF_UP
import json
import logging
import re
from typing import Any, Dict, List, Optional
from .models import CompanyFinancialProfile, FundingRequest, FundingPurpose, FinancingDecisionResult
from lotus_fin.core.ai.providers.factory import ProviderFactory

_logger = logging.getLogger("lotus_fin.f005_financing.advisor")


def sanitize_input(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    cleaned = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


class FinancingIntentParser:
    """NLU intent & parameter parser for Vietnamese & English financing queries."""

    @staticmethod
    def parse_user_query(query_text: str) -> FundingRequest:
        clean_text = sanitize_input(query_text).lower()

        # 1. Extract Amount (USD standard, converting legacy VND if specified)
        amount = Decimal("50000")
        usd_explicit = bool(re.search(r'\$|\busd\b|\bdollar', clean_text))

        k_match = re.search(r'(\d+([.,]\d+)?)\s*(k|nghìn|ngàn|thousand)\b', clean_text)
        ty_match = re.search(r'(\d+([.,]\d+)?)\s*(tỷ|ty)\b', clean_text)
        tr_match = re.search(r'(\d+([.,]\d+)?)\s*(triệu|trieu|tr)\b', clean_text)
        raw_num_match = re.search(r'(?:\$|\busd\s*)?(\d{1,3}(?:[.,]\d{3})+|\d+)\s*(?:usd|\$)?', clean_text)

        if ty_match:
            val_str = ty_match.group(1).replace(',', '.')
            vnd_amount = Decimal(val_str) * Decimal("1000000000")
            amount = (vnd_amount / Decimal("25000.0")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)
        elif tr_match:
            val_str = tr_match.group(1).replace(',', '.')
            vnd_amount = Decimal(val_str) * Decimal("1000000")
            amount = (vnd_amount / Decimal("25000.0")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)
        elif k_match:
            val_str = k_match.group(1).replace(',', '.')
            amount = (Decimal(val_str) * Decimal("1000")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)
        elif raw_num_match:
            val_str = raw_num_match.group(1).replace('.', '').replace(',', '')
            raw_val = Decimal(val_str)
            if raw_val >= 1000000 and not usd_explicit:
                amount = (raw_val / Decimal("25000.0")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)
            elif raw_val > 0:
                amount = raw_val

        # 2. Extract Term Months
        term_months = 12
        year_match = re.search(r'(\d+)\s*(năm|nam|yr|year)', clean_text)
        month_match = re.search(r'(\d+)\s*(tháng|thang|m|month)', clean_text)
        if year_match:
            term_months = int(year_match.group(1)) * 12
        elif month_match:
            term_months = int(month_match.group(1))

        # 3. Extract Purpose
        purpose = FundingPurpose.WORKING_CAPITAL
        if any(w in clean_text for w in ["hóa đơn", "hoa don", "chậm thanh toán", "thu nợ", "invoice", "ar"]):
            purpose = FundingPurpose.INVOICE_RECOVERY
        elif any(w in clean_text for w in ["máy móc", "thiết bị", "xe", "nhà xưởng", "equipment"]):
            purpose = FundingPurpose.EQUIPMENT
        elif any(w in clean_text for w in ["mở rộng", "chi nhánh", "đầu tư", "expansion"]):
            purpose = FundingPurpose.EXPANSION

        return FundingRequest(amount=amount, term_months=term_months, purpose=purpose, currency="USD")


class FinancingAIAdvisor:
    """Grounded AI Advisor synthesizing financing recommendations without hallucination."""

    def __init__(self, provider: str = "mock"):
        self.provider = ProviderFactory.get_provider(provider)

    def generate_advice(
        self,
        profile: CompanyFinancialProfile,
        request: FundingRequest,
        match_result: FinancingDecisionResult,
        user_query: str = "",
        what_if_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        top_matches = match_result.matched_products[:2]

        if not top_matches:
            return {
                "status": "NO_MATCH",
                "executive_summary": "Hiện tại hồ sơ doanh nghiệp chưa đáp ứng điều kiện cứng của các sản phẩm tín dụng tiêu chuẩn.",
                "top_recommendation": None,
                "tradeoff_comparison": "Cần cải thiện DSCR hoặc bổ sung tài sản bảo đảm trước khi nộp hồ sơ.",
                "cashflow_impact_warning": "Cảnh báo thâm hụt tiền mặt nếu không có giải pháp tài trợ thay thế.",
                "actionable_next_steps": ["Kiểm tra lại báo cáo tài chính", "Cân nhắc huy động vốn cổ đông"],
                "policy_compliance": {"bank_write_status": "OFF (Read-only simulation)"},
                "data_provenance": "Rule-based Fallback (No Match)"
            }

        best = top_matches[0]
        summary = (
            f"Dựa trên hồ sơ tài chính của {profile.company_name}, sản phẩm phù hợp nhất là "
            f"{best['product_name']} từ {best['provider']} với điểm phù hợp {best['match_score']:.1f}/100."
        )

        trade_offs = []
        for m in top_matches:
            trade_offs.append(
                f"- {m['product_name']} ({m['provider']}): Lãi suất {m['nominal_rate_annual']*100:.1f}%/năm, "
                f"lãi ước tính ${m['estimated_monthly_interest']:,.2f}/tháng. "
                f"Giải ngân trong {m['disbursement_speed_days']} ngày."
            )

        warning = "Cần theo dõi sát dòng tiền hoạt động để đảm bảo nghĩa vụ trả lãi định kỳ."
        if profile.projected_shortfall_days <= 30:
            warning = (
                f"CẢNH BÁO DÒNG TIỀN: Dự báo có nguy cơ thâm hụt tiền mặt trong {profile.projected_shortfall_days} ngày tới. "
                "Cần ưu tiên sản phẩm có tốc độ giải ngân nhanh."
            )

        actions = [
            f"Chuẩn bị hồ sơ pháp lý và sao kê ngân hàng 6 tháng gần nhất cho {best['provider']}.",
            "Đảm bảo hệ số DSCR duy trì trên mức yêu cầu tối thiểu.",
            "Liên hệ cán bộ tín dụng để nhận biểu lãi suất ưu đãi cập nhật."
        ]

        return {
            "status": "SUCCESS",
            "executive_summary": summary,
            "top_recommendation": best,
            "tradeoff_comparison": "\n".join(trade_offs),
            "cashflow_impact_warning": warning,
            "actionable_next_steps": actions,
            "policy_compliance": {"bank_write_status": "OFF (Read-only simulation)"},
            "data_provenance": f"AI005 Grounded Rule-Engine ({best['provider']})"
        }

    synthesize_financing_advice = generate_advice

