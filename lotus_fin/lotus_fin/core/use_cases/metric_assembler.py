from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Tuple
from lotus_fin.core.domain.calculators.pnl_extractor import parse_pnl_data
from lotus_fin.core.domain.calculators.ar_extractor import parse_ar_data
from lotus_fin.core.domain.calculators.ap_cash_extractor import parse_ap_data, parse_cash_balance
from lotus_fin.core.domain.entities.evidence import EvidenceRef

FORMULA_VERSION = "2026.1"


class MetricAssembler:
    """Assembles metrics, evidence refs, and limitations for a Financial Snapshot."""

    @classmethod
    def assemble(cls, company, p_start, p_end, now_iso, curr, snap_id, p_obj, sources, errors, flts):
        metrics, ev_refs, lims, missing = [], [], [], []

        # 1. P&L
        pnl = sources.get("profit_and_loss")
        if pnl is None or "profit_and_loss" in errors:
            missing.append("profit_and_loss")
            err = errors.get("profit_and_loss", "Source 'profit_and_loss' not provided")
            for m in ["revenue", "cogs", "gross_margin"]:
                metrics.append(cls._m(m, None, curr if m != "gross_margin" else "ratio", p_obj, snap_id, [], [err]))
        else:
            p_data = pnl.get("data", []) if isinstance(pnl, dict) else pnl
            ev_pnl = EvidenceRef.create("ERP_NEXT_REPORT", "Profit and Loss Statement", company, flts.get("profit_and_loss", {}), now_iso, p_data)
            ev_refs.append(ev_pnl.to_dict())
            r_val, c_val, p_lims = parse_pnl_data(p_data)
            lims.extend(p_lims)
            metrics.append(cls._m("revenue", r_val, curr, p_obj, snap_id, [ev_pnl.checksum_or_version], [] if r_val is not None else ["Revenue row missing in P&L."]))
            metrics.append(cls._m("cogs", c_val, curr, p_obj, snap_id, [ev_pnl.checksum_or_version], [] if c_val is not None else ["COGS not isolated in P&L."]))
            gm = ((r_val - c_val) / r_val).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if r_val and c_val and r_val > Decimal("0") else None
            metrics.append(cls._m("gross_margin", gm, "ratio", p_obj, snap_id, [ev_pnl.checksum_or_version], [] if gm is not None else ["Requires both Revenue and COGS to calculate gross margin."]))

        # 2. AR
        ar = sources.get("accounts_receivable")
        if ar is None or "accounts_receivable" in errors:
            missing.append("accounts_receivable")
            err = errors.get("accounts_receivable", "Source 'accounts_receivable' not provided")
            metrics.append(cls._m("ar_outstanding", None, curr, p_obj, snap_id, [], [err]))
            metrics.append(cls._m("overdue_ar_ratio", None, "ratio", p_obj, snap_id, [], [err]))
        else:
            ar_data = ar.get("data", []) if isinstance(ar, dict) else ar
            ev_ar = EvidenceRef.create("ERP_NEXT_REPORT", "Accounts Receivable", company, flts.get("accounts_receivable", {}), now_iso, ar_data)
            ev_refs.append(ev_ar.to_dict())
            t_ar, _, o_ratio, ar_lims = parse_ar_data(ar_data, as_of_date=datetime.strptime(p_end, "%Y-%m-%d").date())
            lims.extend(ar_lims)
            metrics.append(cls._m("ar_outstanding", t_ar, curr, p_obj, snap_id, [ev_ar.checksum_or_version], ar_lims))
            metrics.append(cls._m("overdue_ar_ratio", o_ratio, "ratio", p_obj, snap_id, [ev_ar.checksum_or_version], ar_lims))

        # 3. AP & Cash
        ap = sources.get("accounts_payable")
        if ap is None or "accounts_payable" in errors:
            missing.append("accounts_payable")
            metrics.append(cls._m("ap_outstanding", None, curr, p_obj, snap_id, [], [errors.get("accounts_payable", "Source 'accounts_payable' not provided")]))
        else:
            ap_data = ap.get("data", []) if isinstance(ap, dict) else ap
            ev_ap = EvidenceRef.create("ERP_NEXT_REPORT", "Accounts Payable", company, flts.get("accounts_payable", {}), now_iso, ap_data)
            ev_refs.append(ev_ap.to_dict())
            t_ap, ap_lims = parse_ap_data(ap_data)
            lims.extend(ap_lims)
            metrics.append(cls._m("ap_outstanding", t_ap, curr, p_obj, snap_id, [ev_ap.checksum_or_version], ap_lims))
        metrics.append(cls._m("near_term_ap", None, curr, p_obj, snap_id, [], ["near-term AP horizon not yet frozen"]))

        c_src = sources.get("trial_balance") or sources.get("general_ledger")
        if c_src is None:
            missing.append("cash_balance")
            metrics.append(cls._m("cash_balance", None, curr, p_obj, snap_id, [], ["No cash/bank ledger provided."]))
        else:
            c_data = c_src.get("data", []) if isinstance(c_src, dict) else c_src
            ev_c = EvidenceRef.create("ERP_NEXT_REPORT", "Trial Balance", company, flts.get("trial_balance", {}), now_iso, c_data)
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
