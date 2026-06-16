"""
Re-export of PromptInjectionGuard from the canonical prompt_injection module.

compliance_base.py imports PromptInjectionGuard from this path.
The actual implementation lives in app.shared.prompt_injection (which itself
delegates to app.shared.robustness.security_patterns).

This file exists solely to keep the import path
``from app.shared.compliance.prompt_injection_guard import PromptInjectionGuard``
working without duplicating any logic.
"""

from app.shared.prompt_injection import PromptInjectionGuard, InjectionCheckResult  # noqa: F401

__all__ = ["PromptInjectionGuard", "InjectionCheckResult"]
