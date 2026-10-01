"""
Lotus Fin - AI Core Plugin Specification (Microkernel Interface).

Defines the contract for business modules (AI-F001, AI-F004, AI-F005, etc.)
allowing independent development while exposing a unified tool-calling
and grounding interface to the AI Orchestrator.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from lotus_fin.core.ai.tools.tool_registry import ToolDefinition


class BaseLotusPlugin(ABC):
    """
    Standard Plugin Interface for Lotus Fin Business Modules.
    
    Every domain module implements this interface to:
    1. Register its domain tools for AI function-calling (Zero DB Mutation).
    2. Provide verified domain facts for LLM prompt grounding.
    3. Enforce domain invariants.
    """

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique identifier, e.g. 'f001_health', 'f004_what_if', 'f005_financing'."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the module."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string."""
        pass

    @property
    def description(self) -> str:
        """Description of what this module provides."""
        return ""

    @abstractmethod
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Returns the list of tools exposed by this module to the AI."""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes a domain tool request safely.
        Must enforce read-only execution (R4/R5 Zero DB Mutation).
        """
        pass

    @abstractmethod
    def get_grounding_context(self, company: str, **kwargs) -> Dict[str, Any]:
        """
        Extracts verified, deterministic domain context for LLM grounding.
        Must exclude raw GL entries, PII, or unverified numbers.
        """
        pass

    def validate_invariants(self, data: Dict[str, Any]) -> bool:
        """Validates module domain invariants. Default passes."""
        return True
