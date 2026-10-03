"""
Lotus Fin AI005 - Financing Service Layer.
Coordinates matching, 9-KPI scenario simulation, and grounded AI advisory.
"""

from decimal import Decimal
import logging
from typing import Any, Dict, Optional
from .models import (
    CompanyFinancialProfile,
    FundingRequest,
    FundingPurpose,
    ScenarioParameters,
    FinancingDecisionResult,
    ScenarioSimulationResult
)
from .catalog import get_active_catalog
from .matcher import FinancingDecisionEngine
from .scenario_engine import WhatIfScenarioEngine
from .advisor import FinancingIntentParser, FinancingAIAdvisor, sanitize_input

_logger = logging.getLogger("lotus_fin.f005_financing.service")


class FinancingService:
    """Business coordinator for Module F005 Financing Copilot."""

    def __init__(self, ai_provider: Optional[str] = None):
        import os
        chosen_provider = ai_provider or os.environ.get("LOTUS_AI_PROVIDER") or ("gemini" if os.environ.get("GEMINI_API_KEY") else "mock")
        self.matcher = FinancingDecisionEngine(catalog=get_active_catalog())
        self.scenario_engine = WhatIfScenarioEngine()
        self.ai_advisor = FinancingAIAdvisor(provider=chosen_provider)
        self.intent_parser = FinancingIntentParser()

    def ask_financing_copilot(
        self,
        company: str,
        user_query: str,
        custom_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        sanitized_query = sanitize_input(user_query)
        funding_request = self.intent_parser.parse_user_query(sanitized_query)

        if custom_profile:
            profile = self._build_profile(company, custom_profile)
        else:
            profile = self._extract_company_profile_from_core(company)

        match_result = self.matcher.evaluate(profile, funding_request)
        advice = self.ai_advisor.synthesize_financing_advice(profile, funding_request, match_result)

        intent_dict = {
            "amount": float(funding_request.amount),
            "term_months": funding_request.term_months,
            "purpose": funding_request.purpose.value,
            "currency": funding_request.currency
        }
        matching_dict = {
            "status": match_result.status,
            "matched_count": match_result.matched_options_count,
            "matched_products": match_result.matched_products,
            "disqualified_count": match_result.disqualified_products_count,
            "disqualified_summary": match_result.disqualified_summary
        }
        return {
            "status": "SUCCESS",
            "company": company,
            "user_query": sanitized_query,
            "parsed_intent": intent_dict,
            "parsed_funding_request": intent_dict,
            "deterministic_matching_result": matching_dict,
            "matching_result": matching_dict,
            "ai_advice": advice,
            "ai_advisor_synthesis": advice,
            "policy_declaration": match_result.policy_declaration
        }


    def match_financing_for_company(
        self,
        company: str,
        amount: float,
        term_months: int,
        purpose: str = "WORKING_CAPITAL",
        custom_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        purpose_enum = getattr(FundingPurpose, purpose, FundingPurpose.WORKING_CAPITAL)
        request = FundingRequest(amount=Decimal(str(amount)), term_months=term_months, purpose=purpose_enum)
        profile = self._build_profile(company, custom_profile) if custom_profile else self._extract_company_profile_from_core(company)
        result = self.matcher.evaluate(profile, request)

        return {
            "company": company,
            "status": result.status,
            "matched_options_count": result.matched_options_count,
            "matched_products": result.matched_products,
            "disqualified_products_count": result.disqualified_products_count,
            "disqualified_summary": result.disqualified_summary,
            "policy_declaration": result.policy_declaration
        }

    def run_scenario_with_9kpis(
        self,
        company: str,
        base_snapshot: Optional[Dict[str, Any]] = None,
        sales_change_pct: float = 0.0,
        collection_delay_days: int = 0,
        supplier_due_shift_days: int = 0,
        payroll_change_pct: float = 0.0,
        opex_change_pct: float = 0.0,
        one_off_expense: float = 0.0,
        financing_amount: float = 0.0,
        financing_term_months: int = 0,
        financing_rate_annual: float = 0.0
    ) -> Dict[str, Any]:
        if not base_snapshot:
            base_snapshot = self._extract_default_base_snapshot(company)

        params = ScenarioParameters(
            sales_change_pct=Decimal(str(sales_change_pct)),
            collection_delay_days=int(collection_delay_days),
            supplier_due_shift_days=int(supplier_due_shift_days),
            payroll_change_pct=Decimal(str(payroll_change_pct)),
            opex_change_pct=Decimal(str(opex_change_pct)),
            one_off_expense=Decimal(str(one_off_expense)),
            financing_amount=Decimal(str(financing_amount)),
            financing_term_months=int(financing_term_months),
            financing_rate_annual=Decimal(str(financing_rate_annual))
        )

        sim_result = self.scenario_engine.simulate(
            base_snapshot=base_snapshot,
            params=params,
            scenario_id=f"scen_{company}_9kpis",
            company=company
        )

        return {
            "scenario_id": sim_result.scenario_id,
            "company": sim_result.company,
            "base_snapshot_id": sim_result.base_snapshot_id,
            "data_mode": sim_result.data_mode,
            "parameters": sim_result.parameters,
            "kpis_9_layer": {
                k: self._kpi_to_dict(getattr(sim_result, k))
                for k in ["revenue", "gross_profit", "gross_margin", "ar_outstanding", "dso", "net_cash_flow", "ending_cash", "ccc", "cash_shortfall"]
            },
            "shortfall_events": sim_result.shortfall_events,
            "limitations": sim_result.limitations
        }

    def _kpi_to_dict(self, kpi) -> Dict[str, Any]:
        return {
            "metric_id": kpi.metric_id, "metric_name": kpi.metric_name,
            "baseline": kpi.baseline, "simulation": kpi.simulation,
            "absolute_change": kpi.absolute_change, "relative_change": kpi.relative_change,
            "unit": kpi.unit, "status": kpi.status, "limitations": kpi.limitations
        }

    def _build_profile(self, company: str, data: Dict[str, Any]) -> CompanyFinancialProfile:
        return CompanyFinancialProfile(
            company_name=company,
            operating_months=int(data.get("operating_months", 24)),
            annual_revenue=Decimal(str(data.get("annual_revenue", "2000000000"))),
            current_cash_balance=Decimal(str(data.get("current_cash_balance", "300000000"))),
            current_dscr=Decimal(str(data.get("current_dscr", "1.35"))),
            has_collateral=bool(data.get("has_collateral", False)),
            collateral_types=data.get("collateral_types", []),
            projected_shortfall_days=int(data.get("projected_shortfall_days", 999)),
            has_audited_financials=bool(data.get("has_audited_financials", False))
        )

    def _extract_company_profile_from_core(self, company: str) -> CompanyFinancialProfile:
        return CompanyFinancialProfile(
            company_name=company, operating_months=24,
            annual_revenue=Decimal("2400000000"), current_cash_balance=Decimal("350000000"),
            current_dscr=Decimal("1.40"), has_collateral=False, collateral_types=[],
            projected_shortfall_days=20, has_audited_financials=False
        )

    def _extract_default_base_snapshot(self, company: str) -> Dict[str, Any]:
        return {
            "snapshot_id": f"snap_{company}_latest",
            "revenue": 1000000000.0, "cogs": 600000000.0,
            "ar_outstanding": 250000000.0, "ap_outstanding": 150000000.0,
            "inventory_value": 200000000.0, "opening_cash": 300000000.0,
            "payroll_expense": 120000000.0, "opex_expense": 80000000.0
        }

