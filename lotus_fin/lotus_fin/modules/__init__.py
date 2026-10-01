"""
Lotus Fin - Domain Modules.
Self-contained business modules implementing the BaseLotusPlugin specification:
- f001_health: Financial Health Inspection & Snapshot
- f004_what_if: What-If Cashflow & Scenario Simulation
- f005_financing: Financing Copilot & Loan Decision Support
"""

from lotus_fin.modules.f001_health.plugin import HealthPlugin
from lotus_fin.modules.f004_what_if.plugin import WhatIfPlugin
from lotus_fin.modules.f005_financing.plugin import FinancingPlugin

__all__ = ["HealthPlugin", "WhatIfPlugin", "FinancingPlugin"]
