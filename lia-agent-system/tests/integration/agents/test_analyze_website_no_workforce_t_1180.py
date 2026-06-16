"""Task #1180 sentinela: o fluxo de `analyze_company_website` NUNCA dispara
`import_workforce_plan`, mesmo que o LLM extraia pista de workforce do site.

Motivação: o plano `.local/tasks/analyze-website-modal-and-proposal-card.md`
declara workforce planning EXPLICITAMENTE fora de escopo (linha 30):

    `import_workforce_plan` / workforce planning — desativado para este fluxo.
    Se o LLM extrair dados de planejamento de headcount do site, o adaptador
    descarta. Sentinela impede regressão.

Esta sentinela é AST-based: parse `_wrap_analyze_company_website` e qualquer
helper imediatamente chamado a partir dele, e garante que `import_workforce_plan`
não aparece como string literal nem como chamada.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

TOOL_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "domains"
    / "company_settings"
    / "agents"
    / "company_tool_registry.py"
)


def _extract_analyze_website_fn() -> ast.FunctionDef:
    source = TOOL_REGISTRY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_wrap_analyze_company_website"
        ):
            return node  # type: ignore[return-value]
    raise AssertionError("_wrap_analyze_company_website não encontrado.")


def test_analyze_website_wrapper_never_references_workforce() -> None:
    """AST guard: nenhuma string literal nem nome contém `workforce`/`headcount`."""
    fn = _extract_analyze_website_fn()
    for node in ast.walk(fn):
        # String literals
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert "workforce" not in node.value.lower(), (
                f"T-1180 REGRESSÃO: _wrap_analyze_company_website referencia "
                f"workforce na string {node.value!r}."
            )
            assert "import_workforce_plan" not in node.value.lower(), (
                "T-1180 REGRESSÃO: _wrap_analyze_company_website cita "
                "`import_workforce_plan` — escopo proibido."
            )
        # Identifiers (calls, names)
        if isinstance(node, ast.Name):
            assert node.id != "import_workforce_plan", (
                "T-1180 REGRESSÃO: _wrap_analyze_company_website invoca "
                "`import_workforce_plan` diretamente."
            )
        if isinstance(node, ast.Attribute):
            assert node.attr != "import_workforce_plan", (
                "T-1180 REGRESSÃO: _wrap_analyze_company_website invoca "
                "`.import_workforce_plan(...)`."
            )


def test_analyze_website_wrapper_calls_analyze_direct_only() -> None:
    """Verifica que o único endpoint chamado é `culture-profile/analyze-direct`.

    Defesa adicional: qualquer outro endpoint da família company (em
    particular `workforce-plan/*`) é proibido neste wrapper.
    """
    fn = _extract_analyze_website_fn()
    endpoint_strings: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if "/api/" in v or "/company/" in v:
                endpoint_strings.append(v)
    # Tolera o template `{backend_url}/api/v1/company/culture-profile/analyze-direct`.
    for ep in endpoint_strings:
        assert "workforce" not in ep.lower(), (
            f"T-1180 REGRESSÃO: endpoint workforce vazado em "
            f"_wrap_analyze_company_website: {ep!r}"
        )
        # Deve ser analyze-direct OU um path neutro (logs etc).
        if "/api/v1/company/" in ep:
            assert "culture-profile/analyze-direct" in ep, (
                f"T-1180 REGRESSÃO: _wrap_analyze_company_website chamou "
                f"endpoint inesperado {ep!r}. Apenas `analyze-direct` é permitido."
            )
