"""Task #1161 — Bug C sentinel.

Garante que nenhum handler em ``app/api/v1/company_culture.py`` ou
``app/api/v1/company_culture_config.py`` vaza ``str(e)`` (mensagem interna
de exceção, stack hints, paths, queries SQL) no campo ``detail`` de uma
``HTTPException``. Esse tipo de leak viola o threat model (Information
Disclosure) e foi raiz dos 500 vazados em pw-cenario-D.

Também garante que todo ``except Exception`` que culmina em 500 use
``logger.exception(...)`` para preservar o traceback do lado do servidor
(necessário para diagnosticar a raiz do ResponseValidationError 500 que
gerou a Task #1161).
"""
from __future__ import annotations

import ast
import inspect

import pytest

ROUTE_MODULES = (
    "app.api.v1.company_culture",
    "app.api.v1.company_culture_config",
)


def _module_tree(modpath: str) -> ast.Module:
    mod = __import__(modpath, fromlist=["*"])
    return ast.parse(inspect.getsource(mod))


@pytest.mark.parametrize("modpath", ROUTE_MODULES)
def test_no_str_e_in_http_exception_detail(modpath: str):
    """Bug C regression: ``HTTPException(detail=str(e))`` (e variantes
    ``f"... {e}"`` / ``f"{e}"``) é proibido. Detail deve ser literal."""
    tree = _module_tree(modpath)
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = (
            node.func.attr if isinstance(node.func, ast.Attribute)
            else getattr(node.func, "id", None)
        )
        if func_name != "HTTPException":
            continue
        for kw in node.keywords:
            if kw.arg != "detail":
                continue
            val = kw.value
            # detail=str(e)
            if isinstance(val, ast.Call):
                fn = val.func
                if isinstance(fn, ast.Name) and fn.id == "str":
                    offenders.append(f"line {node.lineno}: detail=str(...)")
            # detail=f"... {e}" / f"... {exc}"
            if isinstance(val, ast.JoinedStr):
                for piece in val.values:
                    if isinstance(piece, ast.FormattedValue):
                        var = piece.value
                        if isinstance(var, ast.Name) and var.id in {"e", "exc", "err", "error"}:
                            offenders.append(
                                f"line {node.lineno}: detail=f'...{{{var.id}}}'"
                            )

    assert not offenders, (
        f"Bug C regression em {modpath}: HTTPException.detail NÃO pode embutir "
        f"a exceção crua (vaza interno). Use 'internal error' + raise ... from e. "
        f"Ofensores: {offenders}"
    )


@pytest.mark.parametrize("modpath", ROUTE_MODULES)
def test_catch_all_uses_logger_exception(modpath: str):
    """Bug C regression: todo ``except Exception`` que termina em 500 DEVE
    chamar ``logger.exception`` (não ``logger.error(f'... {e}')``) para
    preservar o traceback. Catches em handler de HTTP rota."""
    tree = _module_tree(modpath)
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        # Apenas catches de `Exception` (não os mais específicos)
        et = node.type
        if not (isinstance(et, ast.Name) and et.id == "Exception"):
            continue
        body_src = "\n".join(ast.unparse(s) for s in node.body)
        # Só checa catches que terminam em 500 (raise HTTPException(status_code=500, ...))
        raises_500 = "status_code=500" in body_src or "HTTPException(500" in body_src
        if not raises_500:
            continue
        if "logger.exception(" not in body_src:
            offenders.append(
                f"line {node.lineno}: except Exception que raise 500 sem logger.exception"
            )

    assert not offenders, (
        f"Bug C regression em {modpath}: catches de Exception que retornam 500 "
        f"DEVEM usar logger.exception(...) para preservar traceback. "
        f"Ofensores: {offenders}"
    )


def test_culture_profile_schema_normalizes_dict_items():
    """Bug C raiz (ResponseValidationError 500): o schema deve coercer
    list[dict] → list[str] para tolerar drift de dados (default_languages
    salvo como [{code,label,...}] por UIs antigas)."""
    from app.schemas.company_culture import CompanyCultureProfileBase

    payload = {
        "website_url": "https://x.test",
        "default_languages": [
            {"code": "pt-BR", "label": "Português (Brasil)", "level": "native"},
            "en-US",
            {"name": "Espanhol"},
            None,
            "",
        ],
        "tech_stack": [{"value": "Python"}, "Go"],
    }
    parsed = CompanyCultureProfileBase.model_validate(payload)
    assert parsed.default_languages == ["pt-BR", "en-US", "Espanhol"]
    assert parsed.tech_stack == ["Python", "Go"]
