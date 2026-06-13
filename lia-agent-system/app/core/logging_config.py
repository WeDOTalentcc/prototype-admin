"""Shim de compatibilidade — re-exporta de lia_config.logging_config. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.logging_config em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.logging_config import JSONFormatter, configure_logging  # noqa: F401

__all__ = ["JSONFormatter", "configure_logging"]
