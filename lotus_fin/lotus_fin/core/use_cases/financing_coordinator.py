from decimal import Decimal
from typing import Any, Dict, List, Optional
from lotus_fin.core.domain.entities.loan_product import (
    FinancingProduct,
    CompanyFinancialProfile,
    FundingRequest,
    FundingPurpose,
    FinancingDecisionResult
)
from lotus_fin.core.domain.calculators.credit_scorer import CreditScorer
from lotus_fin.core.dto.financing_dto import FinancingMatchRequestDTO
from lotus_fin.modules.f005_financing.catalog import get_active_catalog


class FinancingCoordinator:
    """Coordinates deterministic credit matching and AI Copilot advisory synthesis."""

    def __init__(self, catalog: Optional[List[FinancingProduct]] = None):
        self.catalog = catalog or get_active_catalog()

    def match_financing(
        self,
        request_dto: FinancingMatchRequestDTO,
        profile: Optional[CompanyFinancialProfile] = None
    ) -> FinancingDecisionResult:
        req = FundingRequest(
            amount=Decimal(str(request_dto.amount)),
            term_months=request_dto.term_months,
            purpose=FundingPurpose(request_dto.purpose) if request_dto.purpose in [p.value for p in FundingPurpose] else FundingPurpose.WORKING_CAPITAL
        )

        prof = profile or CompanyFinancialProfile(
            company_name=request_dto.company,
            operating_months=24,
            annual_revenue=Decimal("2500000000"),
            current_cash_balance=Decimal("350000000"),
            current_dscr=Decimal("1.45"),
            has_collateral=request_dto.has_collateral,
            collateral_types=request_dto.collateral_types
        )

        active_rates = [p.nominal_rate_annual for p in self.catalog if p.status == "ACTIVE"]
        min_rate = min(active_rates) if active_rates else Decimal("0.075")
        max_rate = max(active_rates) if active_rates else Decimal("0.135")

        matched, disqualified = [], []
        for prod in self.catalog:
            m_opt, d_opt = CreditScorer.evaluate_option(prod, prof, req, min_rate, max_rate)
            if m_opt:
                matched.append(m_opt)
            elif d_opt:
                disqualified.append(d_opt)

        matched.sort(key=lambda x: x.match_score, reverse=True)
        status = "SUCCESS" if matched else "NO_MATCH"

        return FinancingDecisionResult(
            status=status,
            request_summary={
                "company": prof.company_name,
                "amount": float(req.amount),
                "term_months": req.term_months,
                "purpose": req.purpose.value
            },
            matched_options_count=len(matched),
            matched_products=[self._opt_to_dict(m) for m in matched],
            disqualified_products_count=len(disqualified),
            disqualified_summary=[{"product_id": d.product_id, "provider": d.provider, "reasons": d.reasons} for d in disqualified],
            policy_declaration={"bank_write_status": "OFF", "underwriting_promise": "NONE"}
        )

    def _opt_to_dict(self, opt) -> Dict[str, Any]:
        return {
            "product_id": opt.product_id,
            "provider": opt.provider,
            "product_name": opt.product_name,
            "product_type": opt.product_type,
            "match_score": opt.match_score,
            "score_breakdown": opt.score_breakdown,
            "nominal_rate_annual": opt.nominal_rate_annual,
            "estimated_monthly_interest": opt.estimated_monthly_interest,
            "disbursement_speed_days": opt.disbursement_speed_days,
            "requires_collateral": opt.requires_collateral,
            "source_ref": opt.source_ref,
            "source_as_of": opt.source_as_of,
            "is_stale": opt.is_stale,
            "matched_reasons": list(opt.matched_reasons),
            "missing_criteria": list(opt.missing_criteria)
        }
