"""
Domain interfaces and specs for RBAC and access policies.
Pure Python, free of framework globals.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class ModuleSecurityPolicy:
    """Security allowlist and constraints declared per module."""
    module_id: str
    permitted_reports: Set[str] = field(default_factory=set)
    permitted_evidence_doctypes: Set[str] = field(default_factory=set)


class IPermissionPolicy(ABC):
    """Abstract Port for ERP authorization and validation."""

    @abstractmethod
    def verify_company(self, company: Optional[str] = None, user: Optional[str] = None) -> str:
        """Verifies read access for the target company."""
        pass

    @abstractmethod
    def check_report_permission(
        self,
        report_name: str,
        user: Optional[str] = None,
        module_id: Optional[str] = None
    ) -> None:
        """Verifies report access against both module policy and ERPNext RBAC."""
        pass

    @abstractmethod
    def verify_evidence_access(
        self,
        evidence_ref: str,
        company: Optional[str] = None,
        user: Optional[str] = None,
        module_id: str = "f002"
    ) -> bool:
        """Verifies drilldown access for an evidence reference."""
        pass

    @abstractmethod
    def get_company_accounting_currency(self, company: Optional[str]) -> Optional[str]:
        """Retrieves default currency for company."""
        pass
