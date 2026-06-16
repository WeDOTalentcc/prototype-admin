"""Sprint 2.1 sensor (2026-05-26) — wizard_gate_classifier NÃO força LLM
ecoar user_message no extracted_data. Schema + prompt YAML refatorados
pra eliminar echo (root cause de confidence=0.0 quando LLM truncava ao
tentar repetir JD substancial).

Histórico do bug:
  Fix CR-2 (commit 00a93670) desbloqueou supervisor SKIP, revelando bug
  downstream no jd_gate: LLM Haiku-4.5 com max_tokens=400 (hardcoded em
  _invoke_llm:463) + schema instruindo ecoar `extracted_data.new_content`
  (até 4000 chars) → output truncava antes de emitir confidence/
  conversational_reply → Pydantic defaults 0.0/"" → caller cai em "clarify"
  → self-loop "preciso de mais contexto". Diagnóstico empírico em
  /tmp/diag_jd_gate_confidence.py confirmou LLM retornando apenas
  {'intent': 'provide_new_content'} (campos omitidos por truncation).

Sensor estático (source-grep) — não roda LLM. Pin que:
  1. _invoke_llm assina max_tokens param (não hardcoded)
  2. classify() lê max_tokens do prompt_cfg YAML
  3. Schema description NÃO instrui ecoar new_content/feedback
  4. YAML max_tokens >= 800
  5. YAML rule 6 NÃO instrui ecoar (regra "NUNCA ecoe user_message")
"""
import re
from pathlib import Path

import pytest


SVC = Path("app/domains/job_creation/services/wizard_gate_classifier.py")
YAML = Path("app/prompts/job_creation/gate_classifier.yaml")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_invoke_llm_accepts_max_tokens_param():
    """Sprint 2.1: _invoke_llm signature deve incluir max_tokens param
    (não hardcoded 400 dentro de _call_sync)."""
    src = _read(SVC)
    # match the function signature
    match = re.search(r"async def _invoke_llm\([^)]*\)", src, re.DOTALL)
    assert match, "Could not find _invoke_llm signature"
    sig = match.group(0)
    assert "max_tokens" in sig, (
        f"_invoke_llm signature missing max_tokens param. Signature found:\n{sig}\n"
        f"Sprint 2.1 fix: caller (classify) must pass max_tokens read from YAML cfg."
    )


def test_invoke_llm_does_not_hardcode_max_tokens_400():
    """Sprint 2.1: hardcoded `max_tokens=400` em _call_sync foi root cause
    do truncation (era ignorado o YAML). Deve usar var dinâmica."""
    src = _read(SVC)
    # Capture the _call_sync inner function body
    match = re.search(
        r"def _call_sync\(\):.*?return client\.messages\.create\((.*?)\)",
        src, re.DOTALL,
    )
    assert match, "Could not find _call_sync"
    call_body = match.group(1)
    assert "max_tokens=400" not in call_body, (
        "Sprint 2.1 REGRESSION: _call_sync still has hardcoded max_tokens=400. "
        "Root cause of confidence=0.0 jd_gate bug. Must use param max_tokens."
    )
    # Must reference the param
    assert "max_tokens=max_tokens" in call_body, (
        f"_call_sync must pass max_tokens=max_tokens (from outer scope param). "
        f"Got: {call_body[:300]}"
    )


def test_classify_reads_max_tokens_from_yaml_cfg():
    """Sprint 2.1: classify() deve ler max_tokens do prompt_cfg (carregado
    do YAML via _load_prompt). Elimina config drift YAML↔código."""
    src = _read(SVC)
    # Should reference prompt_cfg.get("max_tokens")
    assert 'prompt_cfg.get("max_tokens")' in src, (
        "classify() must read max_tokens from prompt_cfg (loaded from YAML). "
        "Sprint 2.1 fix eliminates the drift where YAML declared one value "
        "but code hardcoded another."
    )


def test_schema_extracted_data_does_not_instruct_echo():
    """Sprint 2.1: schema description do extracted_data NÃO pode mais
    instruir LLM a ecoar new_content/feedback. Era o anti-pattern que
    causava truncation."""
    src = _read(SVC)
    # Locate the extracted_data block via its anchor + extract surrounding ~600 chars.
    # Regex com parênteses aninhados é fragil — usamos substring search.
    anchor = '"extracted_data":'
    idx = src.find(anchor)
    assert idx >= 0, "Could not find extracted_data key in schema"
    desc = src[idx:idx + 1000]  # 1000-char window covers the dict + description
    forbidden_patterns = [
        ("'provide_new_content': {'new_content': str}", "echo new_content"),
        ("'reject_with_feedback': {'feedback': str}", "echo feedback"),
    ]
    for pattern, label in forbidden_patterns:
        assert pattern not in desc, (
            f"Schema extracted_data ainda instrui {label!r} echo. "
            f"Sprint 2.1 removeu pra eliminar truncation. "
            f"Encontrado: {pattern!r} em:\n{desc[:300]}"
        )
    # Must contain "NUNCA ecoe" reinforcing the canonical
    assert "NUNCA ecoe" in desc, (
        "Schema description deve incluir instrução explícita "
        "'NUNCA ecoe o user_message no extracted_data' para reforçar canonical."
    )


def test_yaml_max_tokens_is_at_least_800():
    """Sprint 2.1: YAML max_tokens >= 800. Era 400, insuficiente."""
    ysrc = _read(YAML)
    match = re.search(r"^max_tokens:\s*(\d+)\s*$", ysrc, re.MULTILINE)
    assert match, "Could not find max_tokens in YAML"
    value = int(match.group(1))
    assert value >= 800, (
        f"YAML max_tokens={value} é insuficiente. Sprint 2.1 raise to >= 800 "
        f"pra LLM completar JSON do tool_use sem truncation."
    )


def test_yaml_prompt_rule_6_forbids_echo():
    """Sprint 2.1: rule 6 do prompt YAML deve instruir 'NUNCA ecoe
    user_message no extracted_data' E NÃO mais conter as instruções
    antigas de echo (new_content/feedback chars)."""
    ysrc = _read(YAML)
    # Should contain the explicit prohibition
    assert "NUNCA ecoe" in ysrc, (
        "YAML prompt rule 6 deve incluir 'NUNCA ecoe' como instrução canonical."
    )
    # Must NOT contain old echo instructions (specifically the 4000 chars limit
    # that was the bug)
    forbidden = [
        "'new_content': '<texto colado",
        "max 4000 chars",
        "máximo 4000 chars",
    ]
    for f in forbidden:
        assert f not in ysrc, (
            f"YAML still contains old echo instruction: {f!r}. "
            f"Sprint 2.1 removeu pra eliminar truncation."
        )
