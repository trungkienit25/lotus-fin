from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from lotus_fin.core.domain.entities.loan_product import (
    FinancingProduct,
    CompanyFinancialProfile,
    FundingRequest,
    FundingPurpose,
    ScoreBreakdown,
    MatchedOption,
    DisqualifiedOption
)

ZERO = Decimal("0.0")
HUNDRED = Decimal("100.0")
ROUND_SCORE = Decimal("0.1")
ROUND_CURRENCY = Decimal("1.0")


class CreditScorer:
    """
    3-Tier deterministic financing evaluation and 100-point scoring calculator.
    Free of LLM hallucination and side-effects.
    """

    @staticmethod
    def evaluate_eligibility(
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest
    ) -> List[str]:
        """Tier 1: Evaluates hard constraints. Returns list of rejection reasons if any."""
        rejections: List[str] = []

        if request.amount < product.amount_min:
            rejections.append(f"Nhu cầu vốn ({request.amount:,.0f} VND) thấp hơn hạn mức tối thiểu ({product.amount_min:,.0f} VND).")
        elif request.amount > product.amount_max:
            rejections.append(f"Nhu cầu vốn ({request.amount:,.0f} VND) vượt quá hạn mức tối đa ({product.amount_max:,.0f} VND).")

        if request.term_months < product.term_min_months or request.term_months > product.term_max_months:
            rejections.append(f"Kỳ hạn yêu cầu ({request.term_months} tháng) ngoài khung ({product.term_min_months} - {product.term_max_months} tháng).")

        if profile.annual_revenue < product.min_annual_revenue:
            rejections.append(f"Doanh thu năm ({profile.annual_revenue:,.0f} VND) chưa đạt ngưỡng tối thiểu ({product.min_annual_revenue:,.0f} VND).")

        if profile.operating_months < product.min_operating_months:
            rejections.append(f"Thời gian hoạt động ({profile.operating_months} tháng) chưa đủ tối thiểu ({product.min_operating_months} tháng).")

        if product.requires_collateral and not profile.has_collateral:
            rejections.append("Sản phẩm yêu cầu tài sản bảo đảm nhưng doanh nghiệp chưa đăng ký TSĐB.")

        if product.requires_audited_financials and not profile.has_audited_financials:
            rejections.append("Sản phẩm yêu cầu BCTC năm gần nhất phải có kiểm toán độc lập.")

        if product.min_dscr_threshold and profile.current_dscr < product.min_dscr_threshold:
            rejections.append(f"Hệ số chi trả nợ hiện tại (DSCR = {profile.current_dscr:.2f}) thấp hơn mức yêu cầu ({product.min_dscr_threshold:.2f}).")

        return rejections

    @staticmethod
    def calculate_score(
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest,
        min_rate: Decimal,
        max_rate: Decimal
    ) -> ScoreBreakdown:
        """Tier 2: Calculates weighted 100-point compatibility score."""
        rate_range = max_rate - min_rate if max_rate > min_rate else Decimal("0.01")
        cost_norm = (product.nominal_rate_annual - min_rate) / rate_range
        score_cost = max(ZERO, (Decimal("1") - cost_norm) * HUNDRED)

        score_fit = Decimal("75.0")
        if request.purpose == FundingPurpose.INVOICE_RECOVERY and product.product_type in ["FACTORING", "INVOICE_DISCOUNT"]:
            score_fit += Decimal("25.0")
        elif request.purpose == FundingPurpose.WORKING_CAPITAL and product.product_type in ["UNSECURED_LOAN", "OVERDRAFT", "SCF"]:
            score_fit += Decimal("20.0")
        elif request.purpose == FundingPurpose.EQUIPMENT and product.product_type == "SECURED_LOAN":
            score_fit += Decimal("20.0")

        if profile.current_dscr >= Decimal("1.50"):
            score_fit = min(HUNDRED, score_fit + Decimal("5.0"))
        score_fit = min(HUNDRED, score_fit)

        if profile.projected_shortfall_days <= 15:
            if product.disbursement_speed_days <= 2:
                score_speed = HUNDRED
            elif product.disbursement_speed_days <= 4:
                score_speed = Decimal("70.0")
            else:
                score_speed = Decimal("40.0")
        else:
            score_speed = Decimal("85.0") if product.disbursement_speed_days <= 5 else Decimal("65.0")

        total = (score_cost * Decimal("0.45") + score_fit * Decimal("0.35") + score_speed * Decimal("0.20")).quantize(
            ROUND_SCORE, rounding=ROUND_HALF_UP
        )
        return ScoreBreakdown(
            cost_score=score_cost.quantize(ROUND_SCORE, rounding=ROUND_HALF_UP),
            capacity_fit_score=score_fit.quantize(ROUND_SCORE, rounding=ROUND_HALF_UP),
            speed_score=score_speed.quantize(ROUND_SCORE, rounding=ROUND_HALF_UP),
            total_score=total
        )

    @classmethod
    def evaluate_option(
        cls,
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest,
        min_rate: Decimal,
        max_rate: Decimal
    ) -> Tuple[Optional[MatchedOption], Optional[DisqualifiedOption]]:
        """Evaluates single product returning either MatchedOption or DisqualifiedOption."""
        rejections = cls.evaluate_eligibility(product, profile, request)
        if rejections:
            return None, DisqualifiedOption(
                product_id=product.product_id,
                provider=product.provider,
                product_name=product.product_name,
                reasons=rejections
            )

        breakdown = cls.calculate_score(product, profile, request, min_rate, max_rate)
        
        as_of_dt = datetime.strptime(product.source_as_of, "%Y-%m-%d").date()
        is_stale = (date.today() - as_of_dt).days > product.ttl_days

        matched_reasons = [
            f"Hạn mức {request.amount:,.0f} VND nằm trong khoảng duyệt [{product.amount_min:,.0f} - {product.amount_max:,.0f} VND].",
            f"Thời gian hoạt động ({profile.operating_months} tháng) thỏa mãn tiêu chuẩn ({product.min_operating_months} tháng).",
            f"Doanh thu năm ({profile.annual_revenue:,.0f} VND) đáp ứng quy mô tối thiểu {product.min_annual_revenue:,.0f} VND.",
            f"Tốc độ giải ngân ước tính: ~{product.disbursement_speed_days} ngày làm việc."
        ]

        missing_criteria = []
        if not product.requires_collateral and product.nominal_rate_annual >= Decimal("0.11"):
            missing_criteria.append("Gói vay tín chấp có biên lãi suất cao; doanh nghiệp có thể bổ sung TSĐB để hạ chi phí.")
        if product.product_type == "OVERDRAFT":
            missing_criteria.append("Cần duy trì tài khoản thanh toán và phát sinh dòng tiền định kỳ tại ngân hàng.")

        est_interest = (request.amount * (product.nominal_rate_annual / Decimal("12"))).quantize(
            ROUND_CURRENCY, rounding=ROUND_HALF_UP
        )

        matched = MatchedOption(
            product_id=product.product_id,
            provider=product.provider,
            product_name=product.product_name,
            product_type=str(product.product_type.value if hasattr(product.product_type, "value") else product.product_type),
            match_score=float(breakdown.total_score),
            score_breakdown={
                "cost_score": float(breakdown.cost_score),
                "capacity_fit_score": float(breakdown.capacity_fit_score),
                "speed_score": float(breakdown.speed_score)
            },
            nominal_rate_annual=float(product.nominal_rate_annual),
            estimated_monthly_interest=float(est_interest),
            disbursement_speed_days=product.disbursement_speed_days,
            requires_collateral=product.requires_collateral,
            source_ref=product.source_ref,
            source_as_of=product.source_as_of,
            is_stale=is_stale,
            matched_reasons=matched_reasons,
            missing_criteria=missing_criteria
        )
        return matched, None
