"""Shim de compatibilidade — re-exporta de lia_config.sentry. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.sentry em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.sentry import init_sentry  # noqa: F401

__all__ = ["init_sentry"]
