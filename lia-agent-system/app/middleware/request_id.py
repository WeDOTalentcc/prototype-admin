"""Shim de compatibilidade — re-exporta de lia_config.request_id. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.request_id em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.request_id import RequestIdMiddleware, get_correlation_id, _current_correlation_id  # noqa: F401

__all__ = ["RequestIdMiddleware", "get_correlation_id", "_current_correlation_id"]
