"""Sensor (harness-engineering) — garante que domain_routing.yaml CARREGA de fato.

Contexto (audit unificacao wizard 2026-05-29): o path em _load_domain_patterns()
apontava para routing/config/domain_routing.yaml (INEXISTENTE) em vez de
config/domain_routing.yaml, fazendo TODO o YAML cair no fallback _HARDCODED
silenciosamente (so um logger.warning "YAML not found"). Resultado: os dominios
company_settings (+18 patterns), job_management (+10 de listagem) e wizard (+1)
rodavam com config degradada sem ninguem notar.

Este sensor falha ALTO se o YAML voltar a nao carregar (computacional, feedforward).
"""
from __future__ import annotations

from pathlib import Path

from app.orchestrator.routing import fast_router as fr


def test_domain_routing_yaml_file_exists_at_expected_path():
    yaml_path = Path(fr.__file__).parent.parent / "config" / "domain_routing.yaml"
    assert yaml_path.exists(), (
        f"domain_routing.yaml nao encontrado em {yaml_path}. "
        "Se moveu o arquivo, atualize _load_domain_patterns()."
    )


def test_load_domain_patterns_uses_yaml_not_hardcoded_fallback():
    """Discriminante: o YAML tem patterns de LISTAGEM em job_management
    (list/ver/minhas/quantas vagas) que o _HARDCODED nao tem. Se ausentes,
    o YAML nao carregou (caiu no fallback)."""
    loaded = fr._load_domain_patterns()
    jm = loaded.get("job_management", [])
    listing = [p for p in jm if "list" in p or "minhas" in p or "quantas" in p]
    assert listing, (
        "job_management sem patterns de listagem — YAML NAO carregou, caiu no "
        "_HARDCODED_DOMAIN_PATTERNS. Verifique o path em _load_domain_patterns() "
        "(deve ser .parent.parent / 'config')."
    )


def test_yaml_wizard_has_creation_patterns():
    loaded = fr._load_domain_patterns()
    joined = " ".join(loaded.get("wizard", []))
    for needle in ("criar", "abrir", "nova", "contratar"):
        assert needle in joined, f"wizard YAML sem gatilho de criacao {needle!r}"


def test_yaml_and_hardcoded_wizard_in_sync_for_creation():
    """Defense-in-depth: patterns de criacao DEVEM estar tambem no hardcoded
    (mesma disciplina do test_prefill_pattern_present_in_hardcoded_fallback)."""
    joined = " ".join(fr._HARDCODED_DOMAIN_PATTERNS.get("wizard", []))
    for needle in ("criar", "abrir", "nova", "contratar"):
        assert needle in joined, (
            f"wizard HARDCODED sem gatilho de criacao {needle!r} — defense-in-depth quebrada"
        )
