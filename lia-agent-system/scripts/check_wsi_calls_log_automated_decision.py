#!/usr/bin/env python3
"""
WT-2022 P0.C wave 2 — WSI audit-trail coverage sensor.

Verifica que toda funcao que chama wsi_service.generate_* (ou via instancia
wsi_svc.generate_*) em paths WSI canonical TAMBEM chama log_automated_decision
no mesmo escopo lexico — fechando o gap LGPD Art. 20 + EU AI Act Art. 13.

Escopo coberto:
    - app/api/v1/wsi/**.py
    - app/api/v1/wsi_*.py
    - app/api/v1/screening.py
    - app/api/wsi_endpoints.py
    - app/api/v1/wsi_screening_pipeline_endpoint.py
    - app/domains/cv_screening/services/wsi_voice_orchestrator.py
    - app/domains/cv_screening/services/wsi_screening_pipeline.py
    - app/domains/recruitment/services/triagem_session_service/wsi_blocks.py
    - app/domains/voice/services/voice_screening_orchestrator.py
    - app/domains/recruiter_assistant/services/wizard_action_executor.py

Escape hatch:
    Adicione `# WSI-AUDIT-EXEMPT: <reason>` em comment dentro da funcao
    (no escopo do erro reportado). O sensor pula a deteccao quando encontra
    o marker.

Exit codes:
    0 — zero violations OU --warn-only
    1 — violations detectadas (BLOCKING modo default)
"""
from __future__ import annotations

import argparse
import ast
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths canonical WSI a vigiar (relativos ao root do lia-agent-system).
# Padrao pathlib glob: usar "**/" como componente OU "*" simples.
WATCHED_GLOBS = [
    "app/api/v1/wsi/*.py",
    "app/api/v1/wsi_*.py",
    "app/api/v1/screening.py",
    "app/api/wsi_endpoints.py",
    "app/api/v1/wsi_screening_pipeline_endpoint.py",
    "app/domains/cv_screening/services/wsi_voice_orchestrator.py",
    "app/domains/cv_screening/services/wsi_screening_pipeline.py",
    "app/domains/recruitment/services/triagem_session_service/wsi_blocks.py",
    "app/domains/voice/services/voice_screening_orchestrator.py",
    "app/domains/recruiter_assistant/services/wizard_action_executor.py",
]

# Metodos do wsi_service que sao gates de decisao automatizada
WSI_GENERATION_METHODS = {
    "generate_from_simple_inputs",
    "generate_screening_questions",
}

# Funcao canonical de audit que precisa estar no escopo
AUDIT_FUNCTION = "log_automated_decision"

# Marker pra opt-out (deve aparecer em comment dentro da funcao)
EXEMPT_MARKER = "WSI-AUDIT-EXEMPT"


def _function_calls_wsi_generate(func_node: ast.AST) -> list[ast.Call]:
    """Retorna lista de Calls dentro da funcao que invocam metodos WSI generation."""
    calls: list[ast.Call] = []
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        # Match: <something>.generate_from_simple_inputs(...) ou
        # <something>.generate_screening_questions(...)
        if isinstance(node.func, ast.Attribute) and node.func.attr in WSI_GENERATION_METHODS:
            calls.append(node)
    return calls


def _function_calls_audit_logger(func_node: ast.AST) -> bool:
    """True se a funcao chama log_automated_decision em qualquer ponto."""
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        # Match: log_automated_decision(...) direto
        if isinstance(node.func, ast.Name) and node.func.id == AUDIT_FUNCTION:
            return True
        # Match: alguma_var.log_automated_decision(...) (improvavel mas seguro)
        if isinstance(node.func, ast.Attribute) and node.func.attr == AUDIT_FUNCTION:
            return True
    return False


def _function_has_exempt_marker(source: str, func_node: ast.AST) -> bool:
    """True se o codigo da funcao contem o marker `# WSI-AUDIT-EXEMPT: ...`."""
    # AST nao preserva comments — precisamos extrair texto via line range
    start = func_node.lineno
    end = getattr(func_node, "end_lineno", start + 100)
    lines = source.splitlines()
    fn_text = "\n".join(lines[start - 1 : end])
    return EXEMPT_MARKER in fn_text


def _check_file(path: Path) -> list[str]:
    """Retorna lista de violations em path:linha:funcao."""
    violations: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("Falha ao ler %s: %s", path, exc)
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        logger.warning("Erro de sintaxe em %s: %s", path, exc)
        return []

    # Walk top-level + classes pra functions
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        wsi_calls = _function_calls_wsi_generate(node)
        if not wsi_calls:
            continue

        if _function_calls_audit_logger(node):
            continue

        if _function_has_exempt_marker(source, node):
            continue

        # Violation: chama wsi_service.generate_* sem log_automated_decision.
        first_call_line = wsi_calls[0].lineno
        violations.append(
            f"{path}:{first_call_line}:{node.name} — chama "
            f"wsi_service.{wsi_calls[0].func.attr}() mas nao chama "
            f"{AUDIT_FUNCTION}() no escopo. Wire audit log (LGPD Art. 20) ou "
            f"adicione comment '# {EXEMPT_MARKER}: <reason>' no corpo."
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta violations mas sai com 0 (opt-out do BLOCKING modo).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Root do lia-agent-system (default: parent do scripts/)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    if not args.root.is_dir():
        logger.error("Root nao existe: %s", args.root)
        return 2

    all_violations: list[str] = []
    files_checked = 0
    for pattern in WATCHED_GLOBS:
        for path in args.root.glob(pattern):
            if not path.is_file():
                continue
            files_checked += 1
            all_violations.extend(_check_file(path))

    if all_violations:
        print(
            f"\nWSI audit-trail sensor: {len(all_violations)} violation(s) em {files_checked} arquivo(s) verificado(s).\n",
            file=sys.stderr,
        )
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            f"\nFix: wire log_automated_decision no escopo da funcao (LGPD Art. 20 + EU AI Act Art. 13).\n"
            f"Ou opt-out: comment '# {EXEMPT_MARKER}: <reason>' dentro da funcao.\n"
            f"Referencia canonical: app/api/v1/wsi/questions.py:generate_questions (commit 27134ec5b).\n",
            file=sys.stderr,
        )
        return 0 if args.warn_only else 1

    print(
        f"WSI audit-trail sensor: 0 violations em {files_checked} arquivo(s) verificado(s). OK.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
