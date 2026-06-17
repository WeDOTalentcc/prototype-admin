"""Shim de compatibilidade — re-exporta de lia_config.langsmith. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.langsmith em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.langsmith import configure_langsmith, get_langsmith_project, is_langsmith_enabled  # noqa: F401

__all__ = ["configure_langsmith", "get_langsmith_project", "is_langsmith_enabled"]
