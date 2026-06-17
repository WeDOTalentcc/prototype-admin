"""Shim de compatibilidade — re-exporta de lia_config.rate_limiter. Não adicionar lógica aqui."""
# SHIM: módulo movido para lia_config.rate_limiter em 2026-06-13 (Fase 2 MONOLITH-IMPORT)
from lia_config.rate_limiter import RateLimitMiddleware, RateLimiter, rate_limiter, rate_limit_middleware  # noqa: F401

__all__ = ["RateLimitMiddleware", "RateLimiter", "rate_limiter", "rate_limit_middleware"]
