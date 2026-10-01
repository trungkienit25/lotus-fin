"""Lotus Fin Plugin Subsystem."""

from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin
from lotus_fin.core.plugin.registry import LotusPluginRegistry, plugin_registry

__all__ = ["BaseLotusPlugin", "LotusPluginRegistry", "plugin_registry"]
