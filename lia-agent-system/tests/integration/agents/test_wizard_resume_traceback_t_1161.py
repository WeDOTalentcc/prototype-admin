"""Task #1161 — Bug B sentinel.

Garante que o catch ao redor de ``aresume_with_message`` em
``WizardSessionService._aresume`` preserva o traceback original via
``logger.exception(...)`` e ``sentry_sdk.capture_exception(...)`` ANTES de
``_emit_silent_fallback``. Sem isso, exceções como ``NotImplementedError``
de stubs legados eram silenciadas, deixando o wizard travado e o operador
sem stack trace para diagnóstico.

Sentinela puramente AST — não roda o wizard, não toca DB nem Redis.
"""
from __future__ import annotations

import ast
import inspect
import textwrap


def _find_target_try_block() -> ast.Try:
    """Localiza o ``try/except`` que envolve ``aresume_with_message`` em
    ``_aresume`` de ``WizardSessionService``."""
    from app.domains.job_creation.services import wizard_session_service as wss

    src = textwrap.dedent(inspect.getsource(wss))
    tree = ast.parse(src)

    cls = next(
        n for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "WizardSessionService"
    )

    # O catch alvo está no método público que envolve aresume_with_message —
    # historicamente process_message; aceitamos qualquer método público do
    # service desde que envolva a chamada certa.
    for node in ast.walk(cls):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Try):
                for stmt in sub.body:
                    src_stmt = ast.unparse(stmt)
                    if "aresume_with_message" in src_stmt:
                        return sub
    raise AssertionError(
        "try/except envolvendo aresume_with_message não encontrado em WizardSessionService"
    )


def test_resume_catch_calls_logger_exception():
    """Bug B regression: o handler DEVE chamar logger.exception (não logger.error)
    para preservar o traceback completo do NotImplementedError."""
    try_block = _find_target_try_block()
    assert try_block.handlers, "try precisa ter pelo menos um except"

    handler_src = ast.unparse(try_block.handlers[0])
    assert "logger.exception(" in handler_src, (
        "Bug B regression: o except de aresume_with_message DEVE chamar "
        "logger.exception(...) para capturar o traceback. "
        "logger.error(f'... {type(e).__name__}') esconde o stack."
    )


def test_resume_catch_calls_sentry_capture():
    """Captura no Sentry para observabilidade em prod (defesa em profundidade)."""
    try_block = _find_target_try_block()
    handler_src = ast.unparse(try_block.handlers[0])
    assert "sentry_sdk.capture_exception(" in handler_src, (
        "Bug B regression: o except DEVE chamar sentry_sdk.capture_exception "
        "para reportar exceções de resume em produção."
    )


def test_logger_exception_runs_before_silent_fallback():
    """Ordem importa: log/sentry ANTES de _emit_silent_fallback,
    senão o fallback pode mascarar a exceção real."""
    try_block = _find_target_try_block()
    handler = try_block.handlers[0]

    log_idx = None
    fallback_idx = None
    for i, stmt in enumerate(handler.body):
        stmt_src = ast.unparse(stmt)
        if log_idx is None and "logger.exception(" in stmt_src:
            log_idx = i
        if fallback_idx is None and "_emit_silent_fallback(" in stmt_src:
            fallback_idx = i

    assert log_idx is not None, "logger.exception ausente no except"
    assert fallback_idx is not None, "_emit_silent_fallback ausente no except"
    assert log_idx < fallback_idx, (
        "Bug B regression: logger.exception(...) DEVE rodar ANTES de "
        "_emit_silent_fallback(...) — senão o fallback pode ofuscar a causa raiz."
    )
