from typing import Any, List, Optional, Tuple

try:
    from lotus_fin.api.key_reports import normalize_frappe_report_footer
except ImportError:
    normalize_frappe_report_footer = None


# Allowed ERPNext report mappings for AI-F001
REPORT_ALLOWLIST = {
    "profit_and_loss": "Profit and Loss Statement",
    "general_ledger": "General Ledger",
    "accounts_receivable": "Accounts Receivable",
    "accounts_payable": "Accounts Payable",
    "trial_balance": "Trial Balance",
    "cash_flow": "Cash Flow"
}


def validate_source_payload(
    source_key: str,
    res: Any,
    expected_company: Optional[str] = None,
) -> Tuple[bool, Optional[List[Any]], Optional[str]]:
    """
    Bucket A & WV-01/WV-02 (AI003 foundation remediation): strict fail-closed
    envelope validation for ERPNext report responses.

    A verified zero is only permitted when:
      status == "success" AND data is a valid list (a legitimate empty result).

    Unknown report status, missing `data`, a non-list `data` payload, company
    mismatch, or report_name / report_key mismatch are typed failures — never
    defaulted to an empty list that reads as zero.
    A raw list is accepted only as a trusted raw_sources injection (test/mock
    path); live fetcher responses must always be envelopes.
    """
    if res is None:
        return False, None, f"Source '{source_key}' not provided"
    if isinstance(res, list):
        return True, res, None
    if isinstance(res, dict):
        status = res.get("status")
        if status == "error":
            return False, None, str(res.get("message") or f"Source '{source_key}' reported an error status")
        if status != "success":
            return False, None, f"Source '{source_key}' returned unknown report status: {status!r}"

        # Report identity mismatch verification
        rep_key = res.get("report_key")
        if rep_key and str(rep_key).strip().lower() != source_key.strip().lower():
            return False, None, f"Source '{source_key}' report_key mismatch: '{rep_key}' != '{source_key}'"

        rep_name = res.get("report_name")
        expected_report_name = REPORT_ALLOWLIST.get(source_key)
        if rep_name and expected_report_name and str(rep_name).strip().lower() != expected_report_name.strip().lower():
            return False, None, f"Source '{source_key}' report_name mismatch: '{rep_name}' != '{expected_report_name}'"

        # Company mismatch verification
        if expected_company:
            rep_comp = res.get("company")
            if rep_comp and rep_comp != expected_company:
                return False, None, f"Source '{source_key}' company mismatch: '{rep_comp}' != '{expected_company}'"

        if "data" not in res:
            return False, None, f"Source '{source_key}' response is missing the 'data' payload"
        data = res.get("data")
        if not isinstance(data, list):
            return False, None, f"Source '{source_key}' 'data' payload is not a list"

        # WV-01: Apply strict, verified Frappe query_report total footer normalization
        columns = res.get("columns")
        add_total_row = res.get("add_total_row")
        skip_total_row = res.get("skip_total_row", False)
        if columns and add_total_row and data and normalize_frappe_report_footer:
            clean_data, _, _ = normalize_frappe_report_footer(
                source_key, columns, data, add_total_row, skip_total_row
            )
            data = clean_data

        return True, data, None
    return False, None, f"Source '{source_key}' payload has an unsupported shape"
