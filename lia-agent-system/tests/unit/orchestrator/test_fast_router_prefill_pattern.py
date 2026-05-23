"""PR5 / A2 (Task #1005) — FastRouter pattern coverage para a tag
`[ACTION:prefill_section][target_section:<key>]` enviada pelo chat
lateral de Configurações (use-settings-conversational.ts).

Contrato: a tag DEVE casar com o domínio `company_settings` em alta
confidence (>=0.85), garantindo roteamento determinístico ANTES da
cascata LLM.
"""
from __future__ import annotations

import pytest

from app.orchestrator.routing import fast_router as fr_mod
from app.orchestrator.routing.fast_router import FastRouter, _COMPILED_PATTERNS


@pytest.fixture(scope="module", autouse=True)
def _ensure_compiled():
    # Garante que _COMPILED_PATTERNS esteja populado antes dos asserts.
    FastRouter()
    yield


@pytest.mark.parametrize(
    "section",
    ["basic", "culture", "tech_stack", "benefits", "workforce", "policy", "compensation"],
)
def test_prefill_tag_matches_company_settings_for_each_section(section: str):
    msg = f"[ACTION:prefill_section][target_section:{section}] preencher dados"
    msg_lower = msg.lower()
    matched_domains: list[str] = []
    for domain_id, patterns in _COMPILED_PATTERNS.items():
        if any(p.search(msg_lower) for p in patterns):
            matched_domains.append(domain_id)
    assert "company_settings" in matched_domains, (
        f"Tag prefill_section[{section}] não casou com company_settings. "
        f"Domínios casados: {matched_domains}."
    )


def test_prefill_tag_case_insensitive():
    """A tag chega com `[ACTION:...]` (maiúsculas) mas o FastRouter
    normaliza via `.lower()` antes do match. Garantimos que ambos os
    casings batem."""
    for variant in (
        "[ACTION:prefill_section][target_section:culture]",
        "[action:prefill_section][target_section:culture]",
        "[Action:Prefill_Section][Target_Section:Culture]",
    ):
        lowered = variant.lower()
        matches = [
            domain_id
            for domain_id, patterns in _COMPILED_PATTERNS.items()
            if any(p.search(lowered) for p in patterns)
        ]
        assert "company_settings" in matches, (
            f"variant {variant!r} (lowered={lowered!r}) não casou. "
            f"Matches: {matches}."
        )


def test_prefill_tag_does_not_match_unrelated_domains():
    """A tag é tão específica (~50 chars) que NÃO deve casar com
    domínios não-relacionados (wsi, talent_pool, agent_studio, etc).
    """
    msg = "[ACTION:prefill_section][target_section:basic]".lower()
    unrelated = (
        "wsi_assessment", "wsi_screening", "talent_pool", "agent_studio",
        "digital_twin", "recruitment_campaign", "interview_scheduling",
        "task_planning",
    )
    for domain_id in unrelated:
        patterns = _COMPILED_PATTERNS.get(domain_id, [])
        for pat in patterns:
            assert not pat.search(msg), (
                f"Domínio `{domain_id}` casou com a tag prefill via "
                f"pattern {pat.pattern!r} — over-matching."
            )


@pytest.mark.parametrize(
    "ambiguous_msg",
    [
        # Tag estruturada + termos que casariam wizard / job_management
        "[ACTION:prefill_section][target_section:basic] quero criar vaga",
        "[ACTION:prefill_section][target_section:culture] nova campanha de recrutamento",
        "[ACTION:prefill_section][target_section:tech_stack] criar agente especialista",
        "[ACTION:prefill_section][target_section:policy] talent pool de devs",
        "[ACTION:prefill_section][target_section:benefits] agendar reunião amanhã",
    ],
)
def test_prefill_tag_wins_routing_under_ambiguity(ambiguous_msg: str):
    """PR5 / A2 (Task #1005) — gap apontado pela code review: o
    `FastRouter.match()` final (não só o `pattern.search` cru) DEVE
    devolver `company_settings` mesmo quando a mensagem cita termos de
    outros domínios. Sem o short-circuit de structured-tag, a penalidade
    de ambiguidade e/ou um match concorrente roubavam o roteamento.
    """
    fr = FastRouter()
    result = fr.match(ambiguous_msg)
    assert result is not None, (
        f"FastRouter retornou None para mensagem com tag estruturada: {ambiguous_msg!r}"
    )
    assert result.domain_id == "company_settings", (
        f"PR5 / A2 regressão: tag estruturada perdeu para outro domínio. "
        f"msg={ambiguous_msg!r} → {result.domain_id} (conf={result.confidence:.2f}, "
        f"matched={result.matched_text!r})"
    )
    # Hard-priority preserva confidence alto (sem penalidade de ambiguidade).
    assert result.confidence >= 0.9, (
        f"Tag estruturada deveria manter confidence >= 0.9 (sem penalidade). "
        f"Atual: {result.confidence:.2f} para {ambiguous_msg!r}"
    )


def test_prefill_pattern_present_in_hardcoded_fallback():
    """Defense in depth: o pattern deve estar TAMBÉM em
    `_HARDCODED_DOMAIN_PATTERNS` para sobreviver a
    `LIA_DISABLE_YAML_ROUTING=1` ou YAML ausente."""
    hardcoded = fr_mod._HARDCODED_DOMAIN_PATTERNS.get("company_settings", [])
    assert any("prefill_section" in p for p in hardcoded), (
        "Pattern `prefill_section` ausente do fallback hardcoded — "
        "FastRouter perde roteamento determinístico se YAML cair."
    )
