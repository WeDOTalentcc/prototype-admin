"""
Template variable validation utility — GAP-06-008 (2026-06-16).

Single source of truth for extracting and validating {{variable}} placeholders
in email/WhatsApp templates. The pattern {{var_name}} (double curly braces)
is the canonical WeDOTalent template variable syntax.

Usage:
    from app.shared.template_validation import (
        extract_template_variables,
        validate_template_variables,
    )

    required = extract_template_variables(subject + body_html)
    missing = validate_template_variables(subject + body_html, provided_variables)
    if missing:
        raise HTTPException(422, detail={
            "error": "missing_template_variables",
            "missing": missing,
            "required": sorted(required),
        })
"""
import re
from typing import Any

# Canonical variable pattern: {{word}} — matches alphanumeric + underscore names.
# Intentionally does NOT match {single_brace} (Jinja2 / Python format strings).
_VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def extract_template_variables(template: str) -> set[str]:
    """Return the set of unique {{variable}} names found in *template*.

    Args:
        template: Raw template string (subject, body_html, body_text, etc.).

    Returns:
        Set of variable name strings (without the surrounding braces).

    Examples:
        >>> extract_template_variables("Olá {{candidate_name}}, vaga: {{job_title}}")
        {'candidate_name', 'job_title'}
        >>> extract_template_variables("No variables here")
        set()
    """
    if not template:
        return set()
    return set(_VARIABLE_PATTERN.findall(template))


def validate_template_variables(
    template: str, provided: dict[str, Any]
) -> list[str]:
    """Return a list of variable names that are required by *template* but absent
    from *provided*.

    Args:
        template: Raw template string (may combine subject + body_html, etc.).
        provided: Dict of variable name → value supplied by the caller.

    Returns:
        List of missing variable names (empty list = all required vars present).

    Notes:
        - Extra variables in *provided* that are NOT in the template are silently
          allowed (callers may pass a superset of variables; this is intentional).
        - Variable names are case-sensitive: {{Candidate_Name}} ≠ {{candidate_name}}.

    Examples:
        >>> validate_template_variables(
        ...     "Hello {{candidate_name}}, role: {{job_title}}",
        ...     {"candidate_name": "Ana"}
        ... )
        ['job_title']
        >>> validate_template_variables(
        ...     "Hello {{candidate_name}}",
        ...     {"candidate_name": "Ana", "extra": "ignored"}
        ... )
        []
    """
    required = extract_template_variables(template)
    return sorted(var for var in required if var not in provided)
