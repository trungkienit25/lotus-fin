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
        from .eligibility_rules import evaluate_all_eligibility_rules
        return evaluate_all_eligibility_rules(product, profile, request)

    def _score_product(
        self,
        product: FinancingProduct,
        profile: CompanyFinancialProfile,
        request: FundingRequest,
        min_rate: Decimal,
        rate_range: Decimal
    ) -> MatchedOption:
        from .scoring_rules import (
            compute_cost_score,
            compute_capacity_score,
            compute_speed_score,
            compute_estimated_monthly_interest
        )

        cost_score = compute_cost_score(product.nominal_rate_annual, min_rate, rate_range)
        capacity_score = compute_capacity_score(request.purpose, product.product_type)
        speed_score = compute_speed_score(profile.projected_shortfall_days, product.disbursement_speed_days)

        total_score = float(cost_score + capacity_score + speed_score)
        est_interest = compute_estimated_monthly_interest(request.amount, product.nominal_rate_annual)

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
