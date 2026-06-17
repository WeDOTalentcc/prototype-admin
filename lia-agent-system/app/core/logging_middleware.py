"""Shim de compatibilidade — re-exporta de lia_config.logging_middleware. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.logging_middleware em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.logging_middleware import StructuredLoggingMiddleware  # noqa: F401

__all__ = ["StructuredLoggingMiddleware"]
