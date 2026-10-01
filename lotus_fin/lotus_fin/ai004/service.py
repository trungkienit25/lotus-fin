"""
Lotus Fin AI004 - Service Facade.
Re-exports ScenarioService from lotus_fin.modules.f004_what_if.service.
"""

from lotus_fin.modules.f004_what_if.service import ScenarioService

__all__ = ["ScenarioService"]
