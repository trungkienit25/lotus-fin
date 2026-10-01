"""
Lotus Fin AI005 - Financing Decision Support Matching Engine.
Strictly deterministic 3-tier matching and scoring engine.
Policy invariant: R4/R5 bank-write = OFF (Read-only matching and simulation).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from .models import (
    FinancingProduct,
    CompanyFinancialProfile,
    FundingRequest,
    FundingPurpose,
    ScoreBreakdown,
    MatchedOption,
    DisqualifiedOption,
    FinancingDecisionResult
)
from .catalog import get_active_catalog


class FinancingDecisionEngine:
    """Deterministic 3-tier matching and ranking engine for SME financing."""

    def __init__(self, catalog: Optional[List[FinancingProduct]] = None):
        self.catalog = catalog if catalog is not None else get_active_catalog()

    def evaluate(
        self,
        profile: CompanyFinancialProfile,
        request: FundingRequest
    ) -> FinancingDecisionResult:
        active_rates = [p.nominal_rate_annual for p in self.catalog if p.status == "ACTIVE"]
        min_rate = min(active_rates) if active_rates else Decimal("0.075")
        max_rate = max(active_rates) if active_rates else Decimal("0.135")
        rate_range = max_rate - min_rate if max_rate > min_rate else Decimal("0.01")

        matched_list: List[MatchedOption] = []
        disqualified_list: List[DisqualifiedOption] = []

        for product in self.catalog:
            rejections = self._check_eligibility(product, profile, request)
            if rejections:
                disqualified_list.append(DisqualifiedOption(
                    product_id=product.product_id,
                    provider=product.provider,
                    product_name=product.product_name,
                    reasons=rejections
                ))
            else:
                matched_opt = self._score_product(product, profile, request, min_rate, rate_range)
                matched_list.append(matched_opt)

        matched_list.sort(key=lambda x: x.match_score, reverse=True)

        return FinancingDecisionResult(
            status="SUCCESS" if matched_list else "NO_MATCH",
            request_summary={
                "amount": float(request.amount),
                "term_months": request.term_months,
                "purpose": request.purpose.value,
                "currency": request.currency
            },
            matched_options_count=len(matched_list),
            matched_products=[self._matched_to_dict(m) for m in matched_list],
            disqualified_products_count=len(disqualified_list),
            disqualified_summary=[
                {"product_id": d.product_id, "provider": d.provider, "name": d.product_name, "reasons": d.reasons}
                for d in disqualified_list
            ],
            policy_declaration={
                "policy": "R4/R5 Strict Read-Only Matching",
                "bank_submission_active": False,
                "bank_submission_allowed": False,
                "data_mode": "simulation",
                "underwriting_guarantee": False
            }
        )

    def _check_eligibility(
        self,
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest
    ) -> List[str]:
        rejections = []
        if request.amount < product.amount_min:
            rejections.append(f"Nhu cầu vốn ({request.amount:,.0f} VND) thấp hơn hạn mức tối thiểu ({product.amount_min:,.0f} VND).")
        elif request.amount > product.amount_max:
            rejections.append(f"Nhu cầu vốn ({request.amount:,.0f} VND) vượt quá hạn mức tối đa ({product.amount_max:,.0f} VND).")

        if request.term_months < product.term_min_months or request.term_months > product.term_max_months:
            rejections.append(f"Kỳ hạn yêu cầu ({request.term_months} tháng) ngoài khung ({product.term_min_months} - {product.term_max_months} tháng).")

        if profile.annual_revenue < product.min_annual_revenue:
            rejections.append(f"Doanh thu ({profile.annual_revenue:,.0f} VND) chưa đạt tối thiểu ({product.min_annual_revenue:,.0f} VND).")

        if profile.operating_months < product.min_operating_months:
            rejections.append(f"Thời gian hoạt động ({profile.operating_months} tháng) chưa đủ ({product.min_operating_months} tháng).")

        if product.requires_collateral and not profile.has_collateral:
            rejections.append("Sản phẩm yêu cầu tài sản thế chấp nhưng doanh nghiệp chưa cung cấp.")

        if product.requires_audited_financials and not profile.has_audited_financials:
            rejections.append("Yêu cầu báo cáo tài chính kiểm toán.")

        if product.min_dscr_threshold and profile.current_dscr < product.min_dscr_threshold:
            rejections.append(f"DSCR hiện tại ({profile.current_dscr:.2f}) thấp hơn ngưỡng ({product.min_dscr_threshold:.2f}).")

        return rejections

    def _score_product(
        self,
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest,
        min_rate: Decimal,
        rate_range: Decimal
    ) -> MatchedOption:
        cost_ratio = (product.nominal_rate_annual - min_rate) / rate_range
        cost_score = (Decimal("45.0") * (Decimal("1.0") - min(max(cost_ratio, Decimal("0")), Decimal("1.0")))).quantize(Decimal("0.1"))

        fit = Decimal("30.0")
        if request.purpose in [FundingPurpose.WORKING_CAPITAL, FundingPurpose.INVOICE_RECOVERY] and product.product_type in ["UNSECURED_LOAN", "OVERDRAFT", "INVOICE_DISCOUNT"]:
            fit += Decimal("5.0")
        elif request.purpose == FundingPurpose.EQUIPMENT and product.product_type == "SECURED_LOAN":
            fit += Decimal("5.0")
        capacity_score = fit.quantize(Decimal("0.1"))

        speed = Decimal("15.0")
        if profile.projected_shortfall_days <= 15 and product.disbursement_speed_days <= 3:
            speed = Decimal("20.0")
        elif product.disbursement_speed_days > 7:
            speed = Decimal("10.0")
        speed_score = speed.quantize(Decimal("0.1"))

        total_score = float(cost_score + capacity_score + speed_score)
        est_interest = float((request.amount * product.nominal_rate_annual / Decimal("12.0")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP))

        matched_reasons = [f"Đáp ứng toàn bộ điều kiện tín dụng của {product.provider}"]
        if not product.requires_collateral:
            matched_reasons.append("Tín chấp hoàn toàn, không yêu cầu thế chấp BĐS")

        return MatchedOption(
            product_id=product.product_id,
            provider=product.provider,
            product_name=product.product_name,
            product_type=product.product_type.value,
            match_score=total_score,
            score_breakdown={
                "cost_score": float(cost_score),
                "capacity_fit_score": float(capacity_score),
                "speed_score": float(speed_score),
                "total_score": total_score
            },
            nominal_rate_annual=float(product.nominal_rate_annual),
            estimated_monthly_interest=est_interest,
            disbursement_speed_days=product.disbursement_speed_days,
            requires_collateral=product.requires_collateral,
            source_ref=product.source_ref,
            source_as_of=product.source_as_of,
            is_stale=product.status != "ACTIVE",
            matched_reasons=matched_reasons,
            missing_criteria=[]
        )

    def _matched_to_dict(self, m: MatchedOption) -> Dict[str, Any]:
        return {
            "product_id": m.product_id,
            "provider": m.provider,
            "product_name": m.product_name,
            "product_type": m.product_type,
            "match_score": m.match_score,
            "score_breakdown": m.score_breakdown,
            "nominal_rate_annual": m.nominal_rate_annual,
            "estimated_monthly_interest": m.estimated_monthly_interest,
            "disbursement_speed_days": m.disbursement_speed_days,
            "requires_collateral": m.requires_collateral,
            "source_ref": m.source_ref,
            "source_as_of": m.source_as_of,
            "is_stale": m.is_stale,
            "matched_reasons": m.matched_reasons,
            "missing_criteria": m.missing_criteria
        }
