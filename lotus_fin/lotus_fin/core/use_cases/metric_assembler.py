from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple
from lotus_fin.core.domain.calculators.pnl_extractor import parse_pnl_data
from lotus_fin.core.domain.calculators.ar_extractor import parse_ar_data
from lotus_fin.core.domain.calculators.ap_cash_extractor import parse_ap_data, parse_cash_balance
from lotus_fin.core.domain.entities.evidence import EvidenceRef
from lotus_fin.core.domain.errors import FinancialSourceDataError
from lotus_fin.core.use_cases.source_validation import validate_source_payload

FORMULA_VERSION = "2026.1"


class MetricAssembler:
    """Assembles metrics, evidence refs, and limitations for a Financial Snapshot.

    Bucket A & WV-01/WR-02 contract (AI003 foundation remediation): every raw
    source passes strict fail-closed envelope validation before parsing, and a
    malformed row invalidates its whole source as a typed unavailable state —
    never an apparent verified zero.
    """

    @classmethod
    def assemble(cls, company, p_start, p_end, now_iso, curr, snap_id, p_obj, sources, errors, flts):
        metrics, ev_refs, lims, missing = [], [], [], []

        # 1. P&L (Revenue & COGS & Gross Margin)
        pnl_res = sources.get("profit_and_loss")
        pnl_ok, pnl_data, pnl_err = validate_source_payload("profit_and_loss", pnl_res, expected_company=company)
        if not pnl_ok or "profit_and_loss" in errors:
            err_msg = errors.get("profit_and_loss", pnl_err or "Source 'profit_and_loss' not provided")
            missing.append("profit_and_loss")
            lims.append(f"P&L Source unavailable: {err_msg}")
            for m in ["revenue", "cogs", "gross_margin"]:
                metrics.append(cls._m(m, None, curr if m != "gross_margin" else "ratio", p_obj, snap_id, [], [err_msg]))
        else:
            pnl_filters = flts.get("profit_and_loss") or {
                "company": company,
                "from_date": p_start,
                "to_date": p_end
            }
            ev_pnl = EvidenceRef.create("ERP_NEXT_REPORT", "Profit and Loss Statement", company, pnl_filters, now_iso, pnl_data)
            ev_refs.append(ev_pnl.to_dict())
            r_val, c_val, p_lims = parse_pnl_data(pnl_data)
            lims.extend(p_lims)
            metrics.append(cls._m("revenue", r_val, curr, p_obj, snap_id, [ev_pnl.checksum_or_version], [] if r_val is not None else ["Revenue row missing in P&L."]))
            metrics.append(cls._m("cogs", c_val, curr, p_obj, snap_id, [ev_pnl.checksum_or_version], [] if c_val is not None else ["COGS not isolated in P&L."]))
            # Gross Margin = (Revenue - COGS) / Revenue. Explicit None checks:
            # COGS == 0 is a verified zero (margin 1.0), not a missing value.
            if r_val is not None and c_val is not None:
                if r_val > Decimal("0"):
                    gm = ((r_val - c_val) / r_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                    gm_lims = []
                else:
                    gm = None
                    gm_lims = ["Revenue is zero or negative; gross margin ratio undefined."]
            else:
                gm = None
                gm_lims = ["Requires both Revenue and COGS to calculate gross margin."]
            metrics.append(cls._m("gross_margin", gm, "ratio", p_obj, snap_id, [ev_pnl.checksum_or_version], gm_lims))

        # 2. AR (Outstanding & Overdue Ratio)
        ar_res = sources.get("accounts_receivable")
        ar_ok, ar_data, ar_err = validate_source_payload("accounts_receivable", ar_res, expected_company=company)
        if not ar_ok or "accounts_receivable" in errors:
            err_msg = errors.get("accounts_receivable", ar_err or "Source 'accounts_receivable' not provided")
            missing.append("accounts_receivable")
            lims.append(f"AR Source unavailable: {err_msg}")
            for m in ["ar_outstanding", "overdue_ar_ratio"]:
                metrics.append(cls._m(m, None, curr if m == "ar_outstanding" else "ratio", p_obj, snap_id, [], [err_msg]))
        else:
            ar_filters = flts.get("accounts_receivable") or {
                "company": company,
                "report_date": p_end
            }
            ev_ar = EvidenceRef.create("ERP_NEXT_REPORT", "Accounts Receivable", company, ar_filters, now_iso, ar_data)
            ev_refs.append(ev_ar.to_dict())

            ar_tot = None
            ar_ratio = None
            ar_lims: List[str] = []
            try:
                ar_tot, _, ar_ratio, ar_lims = parse_ar_data(
                    ar_data,
                    as_of_date=datetime.strptime(p_end, "%Y-%m-%d").date(),
                    company=company,
                    currency=curr,
                )
            except FinancialSourceDataError as e:
                # Bucket A: malformed AR rows invalidate the whole source —
                # typed unavailable state, never an apparent verified zero.
                src_err = f"AR source data invalid: {str(e)}"
                missing.append("accounts_receivable")
                lims.append(src_err)
                for m in ["ar_outstanding", "overdue_ar_ratio"]:
                    metrics.append(cls._m(m, None, curr if m == "ar_outstanding" else "ratio", p_obj, snap_id, [ev_ar.checksum_or_version], [src_err]))
                ar_lims = []
                ar_tot = None
                ar_ratio = None

            if ar_tot is not None:
                lims.extend(ar_lims)
                metrics.append(cls._m("ar_outstanding", ar_tot, curr, p_obj, snap_id, [ev_ar.checksum_or_version], []))
                metrics.append(cls._m("overdue_ar_ratio", ar_ratio, "ratio", p_obj, snap_id, [ev_ar.checksum_or_version], ar_lims))

        # 3. AP (Outstanding)
        ap_res = sources.get("accounts_payable")
        ap_ok, ap_data, ap_err = validate_source_payload("accounts_payable", ap_res, expected_company=company)
        if not ap_ok or "accounts_payable" in errors:
            err_msg = errors.get("accounts_payable", ap_err or "Source 'accounts_payable' not provided")
            missing.append("accounts_payable")
            lims.append(f"AP Source unavailable: {err_msg}")
            metrics.append(cls._m("ap_outstanding", None, curr, p_obj, snap_id, [], [err_msg]))
        else:
            ap_filters = flts.get("accounts_payable") or {
                "company": company,
                "report_date": p_end
            }
            ev_ap = EvidenceRef.create("ERP_NEXT_REPORT", "Accounts Payable", company, ap_filters, now_iso, ap_data)
            ev_refs.append(ev_ap.to_dict())

            try:
                ap_tot, ap_lims = parse_ap_data(ap_data, company=company, currency=curr)
            except FinancialSourceDataError as e:
                # Bucket A: malformed AP rows invalidate the whole source —
                # typed unavailable state, never an apparent verified zero.
                ap_err_str = f"AP source data invalid: {str(e)}"
                missing.append("accounts_payable")
                lims.append(ap_err_str)
                metrics.append(cls._m("ap_outstanding", None, curr, p_obj, snap_id, [ev_ap.checksum_or_version], [ap_err_str]))
            else:
                lims.extend(ap_lims)
                metrics.append(cls._m("ap_outstanding", ap_tot, curr, p_obj, snap_id, [ev_ap.checksum_or_version], ap_lims))

        # 4. Near-Term AP (Freeze rule: UNAVAILABLE with limitation)
        metrics.append(cls._m("near_term_ap", None, curr, p_obj, snap_id, [], ["near-term AP horizon not yet frozen"]))

        # 5. Cash & Bank Balance
        cash_source_key = "trial_balance" if "trial_balance" in sources else "general_ledger"
        cash_source = sources.get(cash_source_key)
        cash_ok, c_data, cash_src_err = validate_source_payload(cash_source_key, cash_source, expected_company=company)
        if not cash_ok:
            missing.append("cash_balance")
            lims.append(f"Cash source unavailable: {cash_src_err}")
            metrics.append(cls._m("cash_balance", None, curr, p_obj, snap_id, [], [cash_src_err]))
        else:
            c_filters = flts.get("trial_balance") or {
                "company": company,
                "from_date": p_start,
                "to_date": p_end
            }
            ev_c = EvidenceRef.create("ERP_NEXT_REPORT", "Trial Balance", company, c_filters, now_iso, c_data)
            ev_refs.append(ev_c.to_dict())
            c_bal, c_lims = parse_cash_balance(c_data)
            lims.extend(c_lims)
            metrics.append(cls._m("cash_balance", c_bal, curr, p_obj, snap_id, [ev_c.checksum_or_version], c_lims))

        return metrics, ev_refs, lims, missing

    @staticmethod
    def _m(m_id, val, unit, p_obj, snap_id, evs, lims):
        return {
            "metric_id": m_id,
            "status": "AVAILABLE" if val is not None else "UNAVAILABLE",
            "value": float(val) if val is not None else None,
            "currency_or_unit": unit,
            "period": p_obj,
            "formula_version": FORMULA_VERSION,
            "snapshot_id": snap_id,
            "evidence_refs": evs,
            "limitations": lims
        }
