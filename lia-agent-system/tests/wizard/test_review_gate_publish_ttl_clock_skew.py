"""Sensor F-2.4 (P0-#4): dual confirmation TTL resists clock-skew.

Background pre-fix: graph.py review_gate_node usava `(time.time() - ts) <= TTL`
sem clip. Cenarios problematicos:

1. ts > now (clock voltou no tempo via NTP correction) -> age negativo ->
   _within_ttl=True sempre, aceita publish_now FORA da janela canonical
   (vulneravel a clock manipulation tanto NTP-bug quanto deliberado).

2. age >> TTL (worker restart, deploy delay, pgbouncer reconnect, ts persistido
   com tz diferente) -> usuario sempre exige nova confirmacao mesmo apos
   reconnect rapido. UX ruim mas seguro.

Pos-fix:
- Age clipped em [0, 2*TTL]: comportamento deterministico em edge cases.
- Logger.warning quando age > TTL: observability pra detectar clock-skew em prod.
- `_within_ttl` permanece a flag canonical de decisao.

Estilo de teste: source-string analysis (regex). Aligned com pattern canonical
de tests/wizard/test_review_gate_dual_confirmation.py — review_gate_node tem
side-effects complexos (audit emit, fairness, langgraph interrupt) cuja
inicializacao runtime polui o test. Regex pinning protege o fix do ARQUIVO,
sem precisar de mocks fragile.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_GRAPH_FILE = (
    Path(__file__).resolve().parents[2]
    / "app/domains/job_creation/graph.py"
)
# PR-10 step 17: review_gate_node moved to nodes/review_gate.py.
# Source-string sentinels concatenate both to remain robust regardless
# of where the code physically lives.
_REVIEW_GATE_NODE_FILE = (
    Path(__file__).resolve().parents[2]
    / "app/domains/job_creation/nodes/review_gate.py"
)


def _read_source() -> str:
    assert _GRAPH_FILE.exists(), f"missing canonical file: {_GRAPH_FILE}"
    parts = [_GRAPH_FILE.read_text(encoding="utf-8")]
    if _REVIEW_GATE_NODE_FILE.exists():
        parts.append(_REVIEW_GATE_NODE_FILE.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_ttl_check_uses_clip_not_raw_difference() -> None:
    """Regra: codigo MUST NOT usar `(_now - float(_ts)) <= TTL` sem clip.

    Pre-fix pattern (vulneravel): _within_ttl = _pending and (_now - float(_ts)) <= _PUBLISH_DUAL_CONFIRMATION_TTL_S
    Pos-fix pattern: clip via max/min antes da comparacao.

    Quando este teste falhar, alguem regrediu o clock-skew guard.
    """
    src = _read_source()
    # Anti-pattern direto (raw subtraction sem clip)
    anti_pattern = re.compile(
        r"_within_ttl\s*=\s*_pending\s+and\s+\(_now\s*-\s*float\(_ts\)\)\s*<=\s*_PUBLISH_DUAL_CONFIRMATION_TTL_S"
    )
    matches = anti_pattern.findall(src)
    assert not matches, (
        "REGRESSION F-2.4 (P0-#4): raw `(_now - ts) <= TTL` pattern found. "
        "Use _ts_age = max(0.0, min(_now - float(_ts), 2.0 * TTL)) instead. "
        "See graph.py review_gate_node and the F-2.4 fix block."
    )


def test_ttl_check_uses_canonical_clip_pattern() -> None:
    """Pos-fix pattern explicito: max(0, min(now-ts, 2*TTL))."""
    src = _read_source()
    clip_pattern = re.compile(
        r"_ts_age\s*=\s*max\(\s*0\.0,\s*min\(\s*_now\s*-\s*float\(_ts\),\s*2\.0\s*\*\s*_PUBLISH_DUAL_CONFIRMATION_TTL_S\s*\)\s*\)"
    )
    assert clip_pattern.search(src), (
        "Canonical clock-skew clip absent. Expected: "
        "`_ts_age = max(0.0, min(_now - float(_ts), 2.0 * _PUBLISH_DUAL_CONFIRMATION_TTL_S))`"
    )


def test_ttl_check_warns_when_age_exceeds_ttl() -> None:
    """Quando age > TTL, deve loggar warning pra observability.

    Sem warning, drift de clock fica invisivel em prod.
    """
    src = _read_source()
    # Pattern: dentro do bloco do review_gate (post-clip), if _pending and _ts_age > TTL: logger.warning
    warn_block = re.compile(
        r"if\s+_pending\s+and\s+_ts_age\s*>\s*_PUBLISH_DUAL_CONFIRMATION_TTL_S\s*:\s*\n"
        r"\s*logger\.warning\(",
        re.MULTILINE,
    )
    assert warn_block.search(src), (
        "F-2.4 observability gap: warning absent when age > TTL. "
        "Sem isso, clock-skew em prod fica invisivel. Verifica graph.py "
        "review_gate_node post-clip block."
    )


def test_ttl_check_uses_age_variable_not_raw_diff() -> None:
    """Comparacao final usa _ts_age (clipped), nao raw subtraction."""
    src = _read_source()
    # Locate the within-TTL check
    canonical = re.compile(
        r"_within_ttl\s*=\s*_pending\s+and\s+_ts_age\s*<=\s*_PUBLISH_DUAL_CONFIRMATION_TTL_S"
    )
    assert canonical.search(src), (
        "F-2.4: _within_ttl must compare against clipped _ts_age, not raw subtraction. "
        "Expected: `_within_ttl = _pending and _ts_age <= _PUBLISH_DUAL_CONFIRMATION_TTL_S`"
    )


def test_clock_skew_clip_preserves_canonical_constant() -> None:
    """F-2.4 fix NAO deve renomear ou duplicar a constante TTL canonical."""
    src = _read_source()
    # A constante canonical existe e e a unica usada no bloco TTL
    assert "_PUBLISH_DUAL_CONFIRMATION_TTL_S: float = 300.0" in src, (
        "Canonical TTL constant missing or modified."
    )
    # Garantir que NAO existe um _REVIEW_PUBLISH_CONFIRM_TTL_S (constante errada do audit original)
    assert "_REVIEW_PUBLISH_CONFIRM_TTL_S" not in src, (
        "Stale audit constant _REVIEW_PUBLISH_CONFIRM_TTL_S resurfaced — "
        "canonical is _PUBLISH_DUAL_CONFIRMATION_TTL_S."
    )
