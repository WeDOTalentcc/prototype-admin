"""
PR-B — test_offer_layer3_fairness.py

Valida que o domínio 'offer' ativa os safeguards obrigatórios para ações de
alto impacto (LIA-C07: stage=OFFER é high_impact).

Camadas validadas:
  - OfferDomain._compliance_config["high_impact"] = True
  - FairnessGuard.check() bloqueia termos discriminatórios em qualquer campo de
    texto-livre da proposta (notes, carta, motivo de recusa)
  - Termos de gênero, idade e raça retornam is_blocked=True com educational_message
  - Texto limpo passa sem bloqueio (não-falso-positivo)

Esses testes são o sensor computacional (harness-engineering Célula I) que
garante que propostas com viés serão detectadas antes de chegar ao candidato.
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def guard():
    from app.shared.compliance.fairness_guard import FairnessGuard
    return FairnessGuard()


@pytest.fixture(scope="module")
def offer_domain():
    from app.domains.offer.domain import OfferDomain
    return OfferDomain()


# ── Compliance config ─────────────────────────────────────────────────────────

class TestOfferDomainHighImpact:

    def test_high_impact_is_true(self, offer_domain):
        """Inegociável: OFFER stage = high-impact (LIA-C07)."""
        assert offer_domain._compliance_config.get("high_impact") is True

    def test_fairness_action_type_is_offer(self, offer_domain):
        """fairness_action_type identifica o tipo de ação para audit trail."""
        assert offer_domain._compliance_config.get("fairness_action_type") == "offer"

    def test_extends_compliance_domain_prompt(self, offer_domain):
        from app.domains.compliance_base import ComplianceDomainPrompt
        assert isinstance(offer_domain, ComplianceDomainPrompt)


# ── FairnessGuard blocks discriminatory offer text ────────────────────────────

class TestFairnessGuardBlocksOfferText:
    """
    Simula textos que poderiam aparecer em campos livres da carta-oferta
    (recruiter_notes, cover_letter_text) e valida que FairnessGuard bloqueia.
    """

    # Gender
    def test_blocks_gender_filter_men_only(self, guard):
        result = guard.check("Enviar proposta apenas para homens com perfil sênior")
        assert result.is_blocked is True, "Filtro de gênero deve ser bloqueado"
        assert result.educational_message, "Deve fornecer mensagem educativa"

    def test_blocks_gender_filter_women_only(self, guard):
        result = guard.check("Prefiro mulheres para essa posição")
        assert result.is_blocked is True

    # Age
    def test_blocks_age_filter_max_age(self, guard):
        result = guard.check("Candidatos com até 35 anos para essa proposta")
        assert result.is_blocked is True, "Limite etário máximo deve ser bloqueado"

    def test_blocks_age_filter_young_only(self, guard):
        result = guard.check("Apenas jovens dinâmicos para esse pacote de oferta")
        assert result.is_blocked is True

    def test_blocks_age_faixa_etaria(self, guard):
        result = guard.check("Perfil com faixa etária de 25 a 35 anos")
        assert result.is_blocked is True

    # Race / ethnicity
    def test_blocks_race_filter(self, guard):
        # "apenas brancos" / "somente candidatos brancos" — triggers raca_etnia category.
        # Note: "candidatos brancos" (bare adjective) is NOT yet a hard-block pattern —
        # that gap is tracked separately in fairness_guard.py (implicit-bias layer).
        result = guard.check("apenas brancos nessa proposta salarial")
        assert result.is_blocked is True

    # Category label in result
    def test_blocked_result_includes_category(self, guard):
        result = guard.check("somente homens nessa faixa salarial")
        assert result.is_blocked is True
        assert result.category is not None
        assert result.category in (
            "genero", "idade", "raca_etnia", "religiao",
            "orientacao_sexual", "estado_civil", "deficiencia", "aparencia",
        )

    def test_blocked_result_includes_educational_message(self, guard):
        result = guard.check("somente mulheres para a proposta de R$ 20.000")
        assert result.is_blocked is True
        assert isinstance(result.educational_message, str)
        assert len(result.educational_message) > 20


# ── FairnessGuard does NOT block clean offer text ─────────────────────────────

class TestFairnessGuardAllowsCleanOfferText:
    """
    Textos legítimos de proposta não devem ser bloqueados
    (prevenção de falso-positivo).
    """

    def test_clean_salary_text(self, guard):
        result = guard.check("Proposta salarial de R$ 15.000 mensais + benefícios")
        assert result.is_blocked is False

    def test_clean_benefits_text(self, guard):
        result = guard.check(
            "Inclui VR R$ 50/dia, VT, plano de saúde Amil, seguro de vida e PLR"
        )
        assert result.is_blocked is False

    def test_clean_start_date_text(self, guard):
        result = guard.check("Início previsto para 01/06/2026, com período de experiência de 90 dias")
        assert result.is_blocked is False

    def test_clean_remote_work_text(self, guard):
        result = guard.check("Modelo híbrido: 3 dias remotos, 2 dias presenciais em São Paulo")
        assert result.is_blocked is False

    def test_clean_experience_years(self, guard):
        # "5 anos de experiência" não deve disparar filtro de idade
        result = guard.check("Requer 5 anos de experiência em Python e arquitetura de sistemas")
        assert result.is_blocked is False, (
            "Requisito de experiência (anos) não é discriminação etária"
        )

    def test_empty_text_not_blocked(self, guard):
        result = guard.check("")
        assert result.is_blocked is False

    def test_none_like_empty_not_blocked(self, guard):
        result = guard.check("   ")
        assert result.is_blocked is False
