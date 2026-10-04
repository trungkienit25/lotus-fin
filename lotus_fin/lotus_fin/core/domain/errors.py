class FinancialSourceDataError(Exception):
    """
    Bucket A (AI003 foundation remediation): raised when a report payload is
    malformed and can never be trusted as a verified zero. The source becomes a
    typed unavailable/error state — a malformed row is never silently skipped
    and summed as 0.
    """
    pass
