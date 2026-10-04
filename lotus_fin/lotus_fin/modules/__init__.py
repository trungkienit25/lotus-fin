"""
Lotus Fin - Domain Modules.
Self-contained business modules implementing the BaseLotusPlugin specification:
- f001_health: Financial Health Inspection & Snapshot
- f002_cashflow: Cash-flow Forecast Copilot
- f003_risk_signal: Risk Signal Agent & P0 Allowlist Monitoring
- f004_what_if: What-If Cashflow & Scenario Simulation
- f005_financing: Financing Copilot & Loan Decision Support
- f006_repayment: Repayment & Stress Simulation Module
- f007_copilot: Financial Copilot Orchestrator Module

Plugin classes are exposed lazily (PEP 562) so that importing one domain
module never eagerly imports the others: a broken or in-progress sibling
module must not break imports.
"""

_PLUGINS = {
    "HealthPlugin": "lotus_fin.modules.f001_health.plugin",
    "CashflowPlugin": "lotus_fin.modules.f002_cashflow.plugin",
    "WhatIfPlugin": "lotus_fin.modules.f004_what_if.plugin",
    "FinancingPlugin": "lotus_fin.modules.f005_financing.plugin",
}

__all__ = list(_PLUGINS)


def __getattr__(name):
    if name in _PLUGINS:
        import importlib

        module = importlib.import_module(_PLUGINS[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
