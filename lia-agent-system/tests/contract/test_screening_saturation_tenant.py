"""
Contract tests: screening auto-trigger LGPD + saturation tenant isolation
P0-W1-01 + P0-W1-11

P0-W1-01: POST /screening/auto-trigger não tinha current_user dependency →
          qualquer caller sem JWT poderia criar tarefa de triagem.
          Fix: adicionar Depends(get_current_active_user) ao endpoint.

P0-W1-11: GET/PUT /settings/saturation usavam Query(...) obrigatório para
          company_id → frontend não envia → HTTP 422 + anti-pattern LGPD.
          Fix: substituir Query(...) por Depends(require_company_id) como
          nos outros endpoints do mesmo arquivo.

Sensor estático (AST-inspection via source text) — não requer DB,
roda em < 1s, falha com mensagem auto-explicativa.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENING_PATH = REPO_ROOT / "app" / "api" / "v1" / "screening.py"
SATURATION_PATH = REPO_ROOT / "app" / "api" / "v1" / "saturation.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# P0-W1-01: auto-trigger must have current_user Depends
# ──────────────────────────────────────────────────────────────────────────────


def test_auto_trigger_has_current_active_user_dependency() -> None:
    """P0-W1-01: auto_trigger_screening handler DEVE ter Depends(get_current_active_user).

    Sem essa dependency, requests sem JWT válido podem criar screening tasks
    cross-tenant — violação LGPD e multi-tenancy canonical.
    Fix: adicionar `current_user: User = Depends(get_current_active_user)`.
    """
    source = _read(SCREENING_PATH)

    # Parse AST to find the auto_trigger_screening function
    tree = ast.parse(source)
    auto_trigger_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "auto_trigger_screening":
            auto_trigger_func = node
            break

    assert auto_trigger_func is not None, (
        "Função auto_trigger_screening não encontrada em screening.py — "
        "endpoint foi renomeado ou removido?"
    )

    # Extract all Depends(...) calls in the function signature
    deps_calls = []
    for arg in auto_trigger_func.args.defaults + [
        d.value for d in auto_trigger_func.args.kw_defaults if d is not None
    ]:
        deps_calls.append(ast.unparse(arg))

    # Also check annotations for kwonlyargs
    for kwarg in auto_trigger_func.args.kwonlyargs:
        if kwarg.annotation:
            deps_calls.append(ast.unparse(kwarg.annotation))

    # Check all default values (where Depends(...) typically lives)
    all_defaults = []
    for default in auto_trigger_func.args.defaults:
        all_defaults.append(ast.unparse(default))
    # kw_defaults aligns with kwonlyargs
    for default in auto_trigger_func.args.kw_defaults:
        if default is not None:
            all_defaults.append(ast.unparse(default))

    has_current_user_dep = any(
        "get_current_active_user" in d for d in all_defaults
    )

    assert has_current_user_dep, (
        "P0-W1-01 REGRESSION: auto_trigger_screening não tem "
        "Depends(get_current_active_user) na assinatura.\n"
        "Fix: adicionar `current_user: User = Depends(get_current_active_user)` "
        "como parâmetro do handler.\n"
        "Sem isso, o endpoint aceita requests sem JWT válido, permitindo "
        "criação de screening tasks sem tenant verification."
    )


def test_auto_screening_request_has_no_company_id_field() -> None:
    """P0-W1-01: AutoScreeningRequest NÃO deve ter campo company_id no body.

    company_id deve vir exclusivamente do JWT via require_company_id —
    nunca do payload (REGRA 2 canonical + LGPD multi-tenancy).
    """
    source = _read(SCREENING_PATH)
    tree = ast.parse(source)

    auto_request_cls = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "AutoScreeningRequest":
            auto_request_cls = node
            break

    assert auto_request_cls is not None, (
        "Classe AutoScreeningRequest não encontrada em screening.py"
    )

    # Check for company_id field assignment in class body
    field_names = []
    for stmt in auto_request_cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            field_names.append(stmt.target.id)

    assert "company_id" not in field_names, (
        "P0-W1-01: AutoScreeningRequest tem campo 'company_id' no body — "
        "viola REGRA 2 (company_id PROIBIDO no request payload).\n"
        "Fix: remover o campo company_id do schema. O handler deve obter "
        "company_id via Depends(require_company_id) ou get_user_company_id(current_user)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# P0-W1-11: saturation settings endpoints must NOT use Query(...) for company_id
# ──────────────────────────────────────────────────────────────────────────────


def _get_function_source(source: str, func_name: str) -> str:
    """Extract source lines of a named async function."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == func_name:
            lines = source.splitlines()
            return "\n".join(lines[node.lineno - 1: node.end_lineno])
    return ""


def test_get_saturation_settings_no_mandatory_query_company_id() -> None:
    """P0-W1-11: GET /settings/saturation NÃO deve ter company_id: str = Query(...).

    company_id: str = Query(...) é obrigatório → frontend não envia → HTTP 422.
    Anti-pattern adicional: Query com company_id é anti-tenant (REGRA 6 variant).
    Fix: substituir por company_id: str = Depends(require_company_id).
    """
    source = _read(SATURATION_PATH)
    func_src = _get_function_source(source, "get_saturation_settings")

    assert func_src, "Função get_saturation_settings não encontrada em saturation.py"

    # Detect the anti-pattern: company_id with Query(...) — either Query(...) or Query(...)
    has_mandatory_query = bool(
        re.search(r'company_id\s*:\s*str\s*=\s*Query\s*\(\s*\.\.\.', func_src)
    )

    assert not has_mandatory_query, (
        "P0-W1-11 REGRESSION: get_saturation_settings usa "
        "company_id: str = Query(...) obrigatório.\n"
        "Isso causa HTTP 422 quando o frontend não envia company_id no query string.\n"
        "Fix: substituir `company_id: str = Query(...)` por "
        "`company_id: str = Depends(require_company_id)` — obtém do JWT, "
        "consistente com os demais endpoints do mesmo arquivo."
    )


def test_update_saturation_settings_no_mandatory_query_company_id() -> None:
    """P0-W1-11: PUT /settings/saturation NÃO deve ter company_id: str = Query(...).

    Mesmo problema do GET — company_id obrigatório no query string causa 422.
    Fix: usar Depends(require_company_id) igual aos outros endpoints.
    """
    source = _read(SATURATION_PATH)
    func_src = _get_function_source(source, "update_saturation_settings")

    assert func_src, "Função update_saturation_settings não encontrada em saturation.py"

    has_mandatory_query = bool(
        re.search(r'company_id\s*:\s*str\s*=\s*Query\s*\(\s*\.\.\.', func_src)
    )

    assert not has_mandatory_query, (
        "P0-W1-11 REGRESSION: update_saturation_settings usa "
        "company_id: str = Query(...) obrigatório.\n"
        "Isso causa HTTP 422 quando o frontend não envia company_id no query string.\n"
        "Fix: substituir por `company_id: str = Depends(require_company_id)`."
    )


def test_saturation_settings_get_uses_require_company_id_depends() -> None:
    """P0-W1-11: GET /settings/saturation DEVE usar Depends(require_company_id).

    Verifica que o fix canônico foi aplicado (não apenas que o Query foi removido).
    """
    source = _read(SATURATION_PATH)
    func_src = _get_function_source(source, "get_saturation_settings")

    assert func_src, "Função get_saturation_settings não encontrada em saturation.py"

    has_requires_dep = bool(
        re.search(r'Depends\s*\(\s*require_company_id\s*\)', func_src)
    )

    assert has_requires_dep, (
        "P0-W1-11: get_saturation_settings não tem Depends(require_company_id).\n"
        "Fix canônico: `company_id: str = Depends(require_company_id)` na assinatura.\n"
        "Isso garante que company_id vem do JWT (multi-tenancy canonical)."
    )


def test_saturation_settings_put_uses_require_company_id_depends() -> None:
    """P0-W1-11: PUT /settings/saturation DEVE usar Depends(require_company_id).

    Verifica que o fix canônico foi aplicado no endpoint de atualização também.
    """
    source = _read(SATURATION_PATH)
    func_src = _get_function_source(source, "update_saturation_settings")

    assert func_src, "Função update_saturation_settings não encontrada em saturation.py"

    has_requires_dep = bool(
        re.search(r'Depends\s*\(\s*require_company_id\s*\)', func_src)
    )

    assert has_requires_dep, (
        "P0-W1-11: update_saturation_settings não tem Depends(require_company_id).\n"
        "Fix canônico: `company_id: str = Depends(require_company_id)` na assinatura.\n"
        "Isso garante que company_id vem do JWT (multi-tenancy canonical)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Bonus: verify strict_match dependency is removed (was masking 422 root cause)
# ──────────────────────────────────────────────────────────────────────────────


def test_saturation_settings_no_redundant_strict_match() -> None:
    """P0-W1-11: Endpoints de saturation settings não devem ter require_company_id_strict_match
    para query.company_id — esse padrão pressupõe que o Query param existe,
    mantendo o 422 mesmo que a dependência original seja removida.

    Fix: remover _company_gate: str = Depends(require_company_id_strict_match(...))
    junto com o Query param, pois sem o Query param o strict_match não serve.
    """
    source = _read(SATURATION_PATH)
    get_src = _get_function_source(source, "get_saturation_settings")
    put_src = _get_function_source(source, "update_saturation_settings")

    # After fix, the strict_match for query.company_id should not be needed
    # (it was only there to validate the Query param against JWT)
    # We verify: if Query(...) is gone, strict_match("query.company_id") is also gone
    for func_name, func_src in [
        ("get_saturation_settings", get_src),
        ("update_saturation_settings", put_src),
    ]:
        has_query_company_id = bool(
            re.search(r'company_id\s*:\s*str\s*=\s*Query\s*\(', func_src)
        )
        has_strict_match_query = bool(
            re.search(r'require_company_id_strict_match\s*\(\s*["\']query\.company_id["\']', func_src)
        )

        # Consistent state: either both exist or neither
        assert has_query_company_id == has_strict_match_query, (
            f"P0-W1-11: {func_name} tem estado inconsistente — "
            f"Query company_id={'presente' if has_query_company_id else 'ausente'} mas "
            f"strict_match={'presente' if has_strict_match_query else 'ausente'}.\n"
            "Fix: remover ambos (Query + strict_match) e usar apenas Depends(require_company_id)."
        )
