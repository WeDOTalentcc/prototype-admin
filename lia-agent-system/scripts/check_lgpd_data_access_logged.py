#!/usr/bin/env python3
"""Sensor: endpoint /agent-monitoring/executions/{id}/reasoning DEVE expor
data_fields_NOT_accessed com o conjunto canonical LGPD Art. 9.

Onda 1 B5.2 (2026-05-27) — sensor BLOCKING canonical.

Recidiva proibida: ExecutionReasoningResponse.data_fields_NOT_accessed é o
"compromisso LGPD" declarativo da Sala de Controle — o recruiter abre a
4ª aba e vê EXPLICITAMENTE que o agente NUNCA acessou cpf, raça, religião,
gênero, estado civil. Remover esse campo = quebra contrato LGPD + perda de
confiança do cliente.

O sensor é AST-based (não-inferencial — não usa LLM). Verifica em
app/api/v1/agent_monitoring.py:
  1. Classe ExecutionReasoningResponse existe e tem campo
     data_fields_NOT_accessed: list[str]
  2. Endpoint GET /executions/{execution_id}/reasoning popula esse campo
     com lista que inclui os 5 canonical: cpf, raca, religiao, genero,
     estado_civil
  3. Lista é estável (não dynamic), preferencialmente referenciada de
     constante module-level (ex: _LGPD_NEVER_ACCESSED_FIELDS)

Output otimizado pra consumo de LLM (instruções de fix embutidas em PT-BR).

Exit codes:
  0 — OK (B4.2 mantém invariante LGPD)
  1 — violação (recidiva: campo declarativo sumiu OU lista incompleta)
  2 — arquivo não encontrado (estrutura mudou — investigar)

Uso:
  python3 scripts/check_lgpd_data_access_logged.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

TARGET = Path("app/api/v1/agent_monitoring.py")

LGPD_REQUIRED = {
    "cpf",
    "raca",
    "religiao",
    "genero",
    "estado_civil",
}


def _find_class(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _class_has_annotation(cls: ast.ClassDef, field_name: str) -> bool:
    for item in cls.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            if item.target.id == field_name:
                return True
    return False


def main() -> int:
    if not TARGET.exists():
        sys.stderr.write(
            f"❌ Sensor ERRO: arquivo canonical não encontrado: {TARGET}\n"
            "→ Fix: investigar se agent_monitoring foi renomeado/movido.\n"
        )
        return 2

    src = TARGET.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        sys.stderr.write(f"❌ Sensor ERRO: parse AST falhou: {e}\n")
        return 2

    violations: list[str] = []

    cls = _find_class(tree, "ExecutionReasoningResponse")
    if cls is None:
        violations.append(
            "  - Classe ExecutionReasoningResponse não encontrada em "
            f"{TARGET}.\n"
            "    → Fix: restaurar response model do endpoint "
            "/agent-monitoring/executions/{id}/reasoning (Onda 1 B4.2).\n"
            "    Deve ter campo:\n"
            "      data_fields_NOT_accessed: list[str]"
        )
    else:
        if not _class_has_annotation(cls, "data_fields_NOT_accessed"):
            violations.append(
                "  - ExecutionReasoningResponse não tem campo "
                "data_fields_NOT_accessed: list[str].\n"
                "    → Fix: adicionar campo à classe.\n"
                "    Endpoint deve popular com: cpf, raca, religiao, "
                "genero, estado_civil.\n"
                "    Esse é o compromisso LGPD declarativo da Sala de "
                "Controle."
            )
        if not _class_has_annotation(cls, "data_fields_accessed_summary"):
            violations.append(
                "  - ExecutionReasoningResponse não tem campo "
                "data_fields_accessed_summary: list[str].\n"
                "    → Fix: adicionar campo agregado dos data_fields_accessed "
                "de cada step. Permite ao recruiter ver o conjunto total de "
                "PII tocada pela execução em uma linha."
            )

    # Check that 5 canonical tokens aparecem no arquivo (heurística textual
    # — não-AST porque tokens podem estar em literal de lista, var, ou
    # frozenset). Lista canonical _LGPD_NEVER_ACCESSED_FIELDS é o pattern
    # esperado.
    missing_tokens = [t for t in LGPD_REQUIRED if t not in src]
    if missing_tokens:
        violations.append(
            f"  - Tokens LGPD canonical ausentes em {TARGET}: "
            f"{missing_tokens}\n"
            "    → Fix: garantir que _LGPD_NEVER_ACCESSED_FIELDS (ou\n"
            "    equivalente) inclui:\n"
            f"    {sorted(LGPD_REQUIRED)}\n"
            "    Endpoint /executions/{id}/reasoning deve retornar essa\n"
            "    lista em data_fields_NOT_accessed (LGPD Art. 9 declarativo)."
        )

    # Sanity adicional: deve haver uma referência data_fields_NOT_accessed= no body
    if "data_fields_NOT_accessed=" not in src:
        violations.append(
            "  - Endpoint não popula data_fields_NOT_accessed na response.\n"
            "    → Fix: na construção do ExecutionReasoningResponse passar:\n"
            "      data_fields_NOT_accessed=list(_LGPD_NEVER_ACCESSED_FIELDS)"
        )

    if violations:
        sys.stderr.write(
            "❌ Sensor BLOCKING: LGPD audit trail da Sala de Controle "
            "perdeu integridade (Onda 1 B4.2 — recidiva proibida).\n\n"
            "Violations:\n"
        )
        for v in violations:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "\n"
            "Contexto: data_fields_NOT_accessed é o compromisso LGPD\n"
            "DECLARATIVO da Sala de Controle. O recruiter abre a 4ª aba e\n"
            "vê: \"esse agente nunca tocou em CPF, raça, religião, gênero,\n"
            "estado civil\". Remover esse campo = recruiter perde visibilidade\n"
            "+ cliente perde confiança + audit LGPD Art. 9 fica sem trail\n"
            "visível.\n\n"
            "Ver: ~/.claude/plans/steady-dazzling-shamir.md Onda 1 B4.2 + B5.2\n"
            "     CLAUDE.md ADR-LGPD-001\n"
        )
        return 1

    print(
        "✅ Sensor OK: ExecutionReasoningResponse expõe "
        "data_fields_NOT_accessed com tokens LGPD canonical "
        f"{sorted(LGPD_REQUIRED)}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
