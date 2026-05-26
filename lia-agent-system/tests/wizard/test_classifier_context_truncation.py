"""Sensor de regressão F-1.5 (2026-05-26) — Sprint 4 proactive context
NÃO deve ser cortado silenciosamente pelos classifiers downstream.

Histórico do bug:
  Sprint 4 (commit 6f2c53ba, wizard_session_service.py:1110-1112)
  APPENDA bloco markdown ao FIM de tenant_context_snippet:

      ### Contexto recente das configurações (últimos 30min)
      <instrução proativa>
      - <section> · campo <fld> = <val>  (ação: <action_id>)
      ...até 8 notas...

  Esse bloco pode chegar a ~1.5KB. Truncate [:500] em
  wizard_gate_classifier.py:342 e [:400] em
  wizard_supervisor_classifier.py:329 cortavam o append PRIMEIRO
  (porque vem appendado depois do contexto canonical do tenant) →
  Sprint 4 ficava inert silenciosamente. Telemetria de status code
  reportava 100% saúde, feature broken.

Fix PR-3: subir truncate para [:2000] (gate) e [:1500] (supervisor),
acomodando o bloco proactive completo + reforço Anti-pattern #1 inline.

Sensores estáticos (source-grep, não rodam LLM):
  1. gate_classifier line 342 usa [:2000] (não [:500] regression)
  2. supervisor_classifier line 329 usa [:1500] (não [:400] regression)
  3. Limites quantitativos: gate >= 1800, supervisor >= 1400.
  4. Simulação funcional: marker canonical aparece no contexto truncado.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


GATE_SVC = Path("app/domains/job_creation/services/wizard_gate_classifier.py")
SUPERVISOR_SVC = Path(
    "app/domains/job_creation/services/wizard_supervisor_classifier.py"
)

# Sentinela canonical — se aparecer no prompt, append preservado.
_PROACTIVE_TAIL_MARKER = "__PROACTIVE_TAIL_MARKER_F15__"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Static source-grep sensors (não rodam LLM — rápidos, robustos)
# ---------------------------------------------------------------------------


def test_gate_classifier_truncate_preserves_proactive_append():
    """PR-3 fix: wizard_gate_classifier:342 deve usar [:2000] (não [:500]).

    Truncate [:500] cortava o bloco proactive Sprint 4 (que pode chegar
    a ~1.5KB appendado ao FIM de tenant_context_snippet).
    """
    src = _read(GATE_SVC)
    lines = src.split("\n")
    line_342 = lines[341]  # 0-indexed

    # Sanity: linha 342 deve ser a do truncate canonical
    assert "tenant_context_snippet" in line_342, (
        "line 342 nao tem tenant_context_snippet -- file estrutura mudou. "
        "Got: {!r}. Reajustar o indice.".format(line_342)
    )

    # Regression guard: nao deve voltar pra [:500]
    assert "[:500]" not in line_342, (
        "PR-3 REGRESSION: line 342 has [:500] truncate (kills Sprint 4 "
        "proactive context appendado ao FIM de tenant_context_snippet "
        "por wizard_session_service:1112). Sprint 4 fica inert. "
        "Restaurar [:2000]. Got: {!r}".format(line_342)
    )
    # Fix canonical: [:2000]
    assert "[:2000]" in line_342, (
        "PR-3 REGRESSION: line 342 must use [:2000] truncate para "
        "acomodar bloco proactive Sprint 4 (~1.5KB) + tenant canonical "
        "(~500). Got: {!r}".format(line_342)
    )


def test_supervisor_classifier_truncate_preserves_proactive_append():
    """PR-3 fix: wizard_supervisor_classifier:329 deve usar [:1500] (não [:400]).

    Mesma classe de bug que gate_classifier — truncate baixo cortava
    bloco proactive Sprint 4 appendado.
    """
    src = _read(SUPERVISOR_SVC)
    lines = src.split("\n")
    line_329 = lines[328]  # 0-indexed
    assert "tenant_context_snippet" in line_329, (
        "line 329 nao tem tenant_context_snippet. Got: {!r}".format(line_329)
    )
    assert "[:400]" not in line_329, (
        "PR-3 REGRESSION: line 329 has [:400] truncate (kills Sprint 4 "
        "proactive context). Got: {!r}".format(line_329)
    )
    assert "[:1500]" in line_329, (
        "PR-3 REGRESSION: line 329 must use [:1500]. Got: {!r}".format(line_329)
    )


def test_gate_classifier_truncate_fits_proactive_block_size():
    """Garantia quantitativa: o limite atual no gate_classifier
    acomoda o bloco proactive típico do Sprint 4 (header + 8 notas)."""
    src = _read(GATE_SVC)
    lines = src.split("\n")
    line_342 = lines[341]
    m = re.search(r"\[:(\d+)\]", line_342)
    assert m, "Truncate pattern not found on gate_classifier line 342: {!r}".format(line_342)
    limit = int(m.group(1))
    # Sprint 4 block size estimate (header ~250 + 8 notes ~150 each = ~1450).
    # Plus tenant canonical context (~500). Limite minimo seguro = 1800.
    assert limit >= 1800, (
        "gate_classifier truncate limit={} eh menor que 1800. "
        "Bloco proactive Sprint 4 (header + 8 notes ~1.5KB) + tenant "
        "context canonical (~500) precisa de ao menos 1800. Subir limite "
        "em wizard_gate_classifier.py:342.".format(limit)
    )


def test_supervisor_classifier_truncate_fits_proactive_block_size():
    """Garantia quantitativa: supervisor_classifier limite acomoda
    proactive block."""
    src = _read(SUPERVISOR_SVC)
    lines = src.split("\n")
    line_329 = lines[328]
    m = re.search(r"\[:(\d+)\]", line_329)
    assert m, "Truncate pattern not found on supervisor_classifier line 329: {!r}".format(line_329)
    limit = int(m.group(1))
    # Supervisor recebe snippet potencialmente menor (sem hiring policy),
    # mas ainda assim precisa acomodar bloco proactive. Minimo = 1400.
    assert limit >= 1400, (
        "supervisor_classifier truncate limit={} eh menor que 1400. "
        "Subir limite em wizard_supervisor_classifier.py:329.".format(limit)
    )


# ---------------------------------------------------------------------------
# Functional simulation: marker no fim do snippet aparece no prompt block
# ---------------------------------------------------------------------------


def test_proactive_marker_survives_gate_context_block_construction():
    """Simula a construção do context_block do gate_classifier com
    tenant_context_snippet contendo marker no FIM (mimic Sprint 4 append).

    Sem rodar LLM — apenas exerce o template f-string + truncate.
    """
    # Snippet: tenant canonical (~400 chars) + Sprint 4 block (~1.2KB) com marker
    tenant_canonical = "A" * 400
    sprint4_block = (
        "\n\n### Contexto recente das configuracoes (ultimos 30min)\n"
        + ("- section . campo X = Y  (acao: settings_update)\n" * 8)
        + _PROACTIVE_TAIL_MARKER
    )
    snippet = tenant_canonical + sprint4_block
    # Total deve estar dentro do novo limite [:2000]
    assert len(snippet) < 2000, (
        "Snippet sintetico tem {} chars, fora do limite [:2000]. "
        "Ajustar tenant_canonical.".format(len(snippet))
    )

    # Mimic construção do context_block (gate_classifier:342)
    truncated = (snippet or "(nao disponivel)")[:2000]
    assert _PROACTIVE_TAIL_MARKER in truncated, (
        "PR-3 fix INERT: marker proactive cortado mesmo com [:2000]. "
        "Algo errado no setup do test ou regressao no limite."
    )


def test_proactive_marker_survives_supervisor_context_block_construction():
    """Mesma simulação para o supervisor (truncate [:1500])."""
    # Snippet menor: ~200 tenant + ~1.1KB Sprint 4 block + marker
    tenant_canonical = "A" * 200
    sprint4_block = (
        "\n\n### Contexto recente das configuracoes (ultimos 30min)\n"
        + ("- section . campo X = Y  (acao: settings_update)\n" * 6)
        + _PROACTIVE_TAIL_MARKER
    )
    snippet = tenant_canonical + sprint4_block
    assert len(snippet) < 1500, (
        "Snippet sintetico tem {} chars, fora do limite [:1500]. "
        "Ajustar tenant_canonical.".format(len(snippet))
    )

    # Mimic construção do tenant_block (supervisor_classifier:329)
    truncated = (snippet or "")[:1500] or "(nao disponivel)"
    assert _PROACTIVE_TAIL_MARKER in truncated, (
        "PR-3 fix INERT: marker proactive cortado mesmo com [:1500]. "
        "Algo errado no setup do test ou regressao no limite."
    )


def test_old_truncate_500_would_lose_marker():
    """Negativo: confirma que o limite ANTIGO [:500] perderia o marker.

    Sanity check do sensor — se este teste falha, o cenário do bug
    não é mais reproduzível e o sensor pode estar overcorrecting."""
    tenant_canonical = "A" * 400
    sprint4_block = (
        "\n\n### Contexto recente das configuracoes (ultimos 30min)\n"
        + ("- section . campo X = Y  (acao: settings_update)\n" * 8)
        + _PROACTIVE_TAIL_MARKER
    )
    snippet = tenant_canonical + sprint4_block
    truncated_old = (snippet or "(nao disponivel)")[:500]
    assert _PROACTIVE_TAIL_MARKER not in truncated_old, (
        "Sanity test failed: marker survived [:500] truncate -- cenario do "
        "bug nao eh reproduzivel com este snippet sintetico. Reduzir "
        "tenant_canonical ou aumentar bloco proactive ate o marker cair "
        "fora dos 500 primeiros chars."
    )
