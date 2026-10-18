"""
Lotus Fin F005 - Eligibility Rules.
Discrete, single-responsibility predicate functions to evaluate bank credit criteria.
"""

from typing import List, Optional
from .models import FinancingProduct, CompanyFinancialProfile, FundingRequest


def check_amount_bounds(product: FinancingProduct, request: FundingRequest) -> Optional[str]:
    """Verifies that requested funding is within minimum and maximum product boundaries."""
    if request.amount < product.amount_min:
        return f"Nhu cầu vốn ({request.amount:,.0f} {product.currency}) thấp hơn hạn mức tối thiểu ({product.amount_min:,.0f} {product.currency})."
    if request.amount > product.amount_max:
        return f"Nhu cầu vốn ({request.amount:,.0f} {product.currency}) vượt quá hạn mức tối đa ({product.amount_max:,.0f} {product.currency})."
    return None


def check_tenure_bounds(product: FinancingProduct, request: FundingRequest) -> Optional[str]:
    """Verifies that requested term falls within allowable tenure envelope."""
    if request.term_months < product.term_min_months or request.term_months > product.term_max_months:
        return f"Kỳ hạn yêu cầu ({request.term_months} tháng) ngoài khung ({product.term_min_months} - {product.term_max_months} tháng)."
    return None


def check_revenue_threshold(product: FinancingProduct, profile: CompanyFinancialProfile) -> Optional[str]:
    """Verifies corporate annual turnover meets minimum underwriting floor."""
    if profile.annual_revenue < product.min_annual_revenue:
        return f"Doanh thu ({profile.annual_revenue:,.0f} {product.currency}) chưa đạt tối thiểu ({product.min_annual_revenue:,.0f} {product.currency})."
    return None


def check_operating_history(product: FinancingProduct, profile: CompanyFinancialProfile) -> Optional[str]:
    """Verifies operating track record tenure."""
    if profile.operating_months < product.min_operating_months:
        return f"Thời gian hoạt động ({profile.operating_months} tháng) chưa đủ ({product.min_operating_months} tháng)."
    return None


def check_collateral_requirement(product: FinancingProduct, profile: CompanyFinancialProfile) -> Optional[str]:
    """Verifies security collateral pledge if required by product tier."""
    if product.requires_collateral and not profile.has_collateral:
        return "Sản phẩm yêu cầu tài sản thế chấp nhưng doanh nghiệp chưa cung cấp."
    return None


def check_audit_requirement(product: FinancingProduct, profile: CompanyFinancialProfile) -> Optional[str]:
    """Verifies availability of audited financial statements."""
    if product.requires_audited_financials and not profile.has_audited_financials:
        return "Yêu cầu báo cáo tài chính kiểm toán."
    return None


def check_dscr_requirement(product: FinancingProduct, profile: CompanyFinancialProfile) -> Optional[str]:
    """Verifies debt service coverage ratio (DSCR)."""
    if product.min_dscr_threshold and profile.current_dscr < product.min_dscr_threshold:
        return f"DSCR hiện tại ({profile.current_dscr:.2f}) thấp hơn ngưỡng ({product.min_dscr_threshold:.2f})."
    return None


def evaluate_all_eligibility_rules(
    product: FinancingProduct,
    profile: CompanyFinancialProfile,
    request: FundingRequest
) -> List[str]:
    """
    Evaluates all criteria predicates sequentially.
    Returns list of rejection reasons (empty if fully eligible).
    """
    validators = [
        check_amount_bounds(product, request),
        check_tenure_bounds(product, request),
        check_revenue_threshold(product, profile),
        check_operating_history(product, profile),
        check_collateral_requirement(product, profile),
        check_audit_requirement(product, profile),
        check_dscr_requirement(product, profile)
    ]
    return [err for err in validators if err is not None]

