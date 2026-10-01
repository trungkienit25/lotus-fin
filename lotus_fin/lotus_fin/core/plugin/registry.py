"""
Lotus Fin - AI Core Plugin Registry (Kernel / Host).

Acts as the Strategy intermediary between the AI Engine and independent domain modules.
Enforces modular isolation while providing centralized discovery and routing.
"""

import logging
from typing import Any, Dict, List, Optional
from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin

_logger = logging.getLogger("lotus_fin.core.plugin.registry")


class LotusPluginRegistry:
    """
    Singleton registry managing domain module plugins.
    Allows independent modules to register tools and context providers.
    """

    def __init__(self):
        self._plugins: Dict[str, BaseLotusPlugin] = {}
        self._tool_to_plugin: Dict[str, str] = {}

    def register(self, plugin: BaseLotusPlugin) -> None:
        """Registers a domain plugin and maps its tools."""
        self._plugins[plugin.plugin_id] = plugin
        for tool in plugin.get_tool_definitions():
            self._tool_to_plugin[tool.name] = plugin.plugin_id
        _logger.info(f"Registered Lotus Fin plugin: {plugin.plugin_id} (v{plugin.version})")

    def unregister(self, plugin_id: str) -> None:
        """Removes a plugin and its tool mappings."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            self._tool_to_plugin = {
                t: p for t, p in self._tool_to_plugin.items() if p != plugin_id
            }

    def get_plugin(self, plugin_id: str) -> Optional[BaseLotusPlugin]:
        """Returns a registered plugin by ID."""
        self.ensure_builtins_registered()
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Lists metadata of all registered plugins."""
        self.ensure_builtins_registered()
        return [
            {
                "plugin_id": p.plugin_id,
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "tool_count": len(p.get_tool_definitions())
            }
            for p in self._plugins.values()
        ]

    def export_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns OpenAI/Gemini compatible function calling schemas for all tools."""
        self.ensure_builtins_registered()
        schemas = []
        for plugin in self._plugins.values():
            for tool in plugin.get_tool_definitions():
                schemas.append(tool.to_schema())
        return schemas

    def dispatch_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Routes tool execution to the appropriate module plugin.
        Raises KeyError if tool is unregistered.
        """
        self.ensure_builtins_registered()
        plugin_id = self._tool_to_plugin.get(tool_name)
        if not plugin_id or plugin_id not in self._plugins:
            raise KeyError(f"Tool '{tool_name}' is not registered by any active plugin.")
        return self._plugins[plugin_id].execute_tool(tool_name, arguments)

    def gather_grounding_context(
        self,
        company: str,
        plugin_ids: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Aggregates deterministic grounding facts from registered plugins.
        Excludes ungrounded or non-verified data.
        """
        self.ensure_builtins_registered()
        contexts: Dict[str, Any] = {}

        targets = plugin_ids or list(self._plugins.keys())
        for pid in targets:
            plugin = self._plugins.get(pid)
            if plugin:
                try:
                    contexts[pid] = plugin.get_grounding_context(company, **kwargs)
                except Exception as e:
                    _logger.warning(f"Failed to gather grounding context from {pid}: {e}")
                    contexts[pid] = {"status": "UNAVAILABLE", "error": str(e)}
        return contexts

    def ensure_builtins_registered(self) -> None:
        if not self._plugins:
            self.register_builtins()


    def register_builtins(self) -> None:
        """Auto-discovers and registers standard domain modules."""
        try:
            from lotus_fin.modules.f001_health.plugin import HealthPlugin
            self.register(HealthPlugin())
        except Exception as e:
            _logger.warning(f"Could not auto-register HealthPlugin: {e}")

        try:
            from lotus_fin.modules.f004_what_if.plugin import WhatIfPlugin
            self.register(WhatIfPlugin())
        except Exception as e:
            _logger.warning(f"Could not auto-register WhatIfPlugin: {e}")

        try:
            from lotus_fin.modules.f005_financing.plugin import FinancingPlugin
            self.register(FinancingPlugin())
        except Exception as e:
            _logger.warning(f"Could not auto-register FinancingPlugin: {e}")


# Singleton registry instance
plugin_registry = LotusPluginRegistry()

