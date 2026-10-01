from datetime import date
from typing import Any, Callable, Dict, Optional, Tuple


class SourceGatherer:
    """Gathers and isolates raw ERPNext report sources with effective date boundaries."""

    @staticmethod
    def gather(
        company: str,
        period_start: str,
        period_end: str,
        effective_end_date: str,
        raw_sources: Optional[Dict[str, Any]] = None,
        source_fetcher: Optional[Callable[..., Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, Any]]:
        sources: Dict[str, Any] = dict(raw_sources or {})
        fetch_errors: Dict[str, str] = {}
        actual_filters_used: Dict[str, Any] = {}

        if source_fetcher and not raw_sources:
            start_year = int(period_start[:4])
            end_year = int(effective_end_date[:4])

            # 1. P&L
            flt_pnl = {
                "company": company,
                "from_fiscal_year": start_year,
                "to_fiscal_year": end_year,
                "period_start_date": period_start,
                "period_end_date": effective_end_date,
                "periodicity": "Yearly"
            }
            actual_filters_used["profit_and_loss"] = flt_pnl
            try:
                res_pnl = source_fetcher("profit_and_loss", flt_pnl, company)
                if isinstance(res_pnl, dict) and res_pnl.get("status") == "error":
                    fetch_errors["profit_and_loss"] = res_pnl.get("message", "P&L error")
                else:
                    sources["profit_and_loss"] = res_pnl
            except Exception as e:
                fetch_errors["profit_and_loss"] = str(e)

            # 2. AR
            flt_ar = {"company": company, "report_date": effective_end_date}
            actual_filters_used["accounts_receivable"] = flt_ar
            try:
                res_ar = source_fetcher("accounts_receivable", flt_ar, company)
                if isinstance(res_ar, dict) and res_ar.get("status") == "error":
                    fetch_errors["accounts_receivable"] = res_ar.get("message", "AR error")
                else:
                    sources["accounts_receivable"] = res_ar
            except Exception as e:
                fetch_errors["accounts_receivable"] = str(e)

            # 3. AP
            flt_ap = {"company": company, "report_date": effective_end_date}
            actual_filters_used["accounts_payable"] = flt_ap
            try:
                res_ap = source_fetcher("accounts_payable", flt_ap, company)
                if isinstance(res_ap, dict) and res_ap.get("status") == "error":
                    fetch_errors["accounts_payable"] = res_ap.get("message", "AP error")
                else:
                    sources["accounts_payable"] = res_ap
            except Exception as e:
                fetch_errors["accounts_payable"] = str(e)

            # 4. Trial Balance
            flt_tb = {
                "company": company,
                "fiscal_year": end_year,
                "from_date": period_start,
                "to_date": effective_end_date
            }
            actual_filters_used["trial_balance"] = flt_tb
            try:
                res_tb = source_fetcher("trial_balance", flt_tb, company)
                if isinstance(res_tb, dict) and res_tb.get("status") == "error":
                    fetch_errors["trial_balance"] = res_tb.get("message", "Trial Balance error")
                else:
                    sources["trial_balance"] = res_tb
            except Exception as e:
                fetch_errors["trial_balance"] = str(e)

        return sources, fetch_errors, actual_filters_used
