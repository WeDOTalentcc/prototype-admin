"""
P1-C — Testes de deduplicação de seções nos prompts.

Cobre:
1. wizard: seção CONFIRMACOES removida (não deve mais existir)
2. wizard: TRANSICOES tem as confirmações canônicas (inclui palavras mescladas)
3. wizard: TRANSICOES tem as negações canônicas (inclui "cancelar" mesclado)
4. wizard: nenhum conteúdo único perdido ("confirmo", "certo", "cancelar" preservados)
5. wizard: apenas uma seção com listas de confirmação/negação
6. policy: seções distintas permanecem intactas (não regrediu)
7. policy: RACIOCINIO CONSULTIVO presente
8. policy: VERIFICACAO DE PREMISSAS presente
9. policy: CONTRA-ARGUMENTACAO presente
"""
import pytest


class TestWizardDeduplicacao:

    def test_secao_confirmacoes_removida(self):
        """Seção duplicada CONFIRMACOES não deve mais existir."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        # A seção standalone foi removida — TRANSICOES é a fonte canônica
        # Conta ocorrências do cabeçalho de seção
        count = WIZARD_SYSTEM_PROMPT.count("=== CONFIRMACOES ===")
        assert count == 0, f"Seção CONFIRMACOES duplicada ainda presente ({count} vez/vezes)"

    def test_transicoes_tem_confirmacoes_canonicas(self):
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert "Entenda confirmacoes" in WIZARD_SYSTEM_PROMPT
        assert '"sim"' in WIZARD_SYSTEM_PROMPT
        assert '"ok"' in WIZARD_SYSTEM_PROMPT

    def test_transicoes_tem_negacoes_canonicas(self):
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert "Entenda negacoes" in WIZARD_SYSTEM_PROMPT
        assert '"nao"' in WIZARD_SYSTEM_PROMPT
        assert '"espera"' in WIZARD_SYSTEM_PROMPT

    def test_palavra_confirmo_preservada(self):
        """'confirmo' estava apenas em CONFIRMACOES — deve ter sido mesclada em TRANSICOES."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert '"confirmo"' in WIZARD_SYSTEM_PROMPT

    def test_palavra_certo_preservada(self):
        """'certo' estava apenas em CONFIRMACOES — deve ter sido mesclada em TRANSICOES."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert '"certo"' in WIZARD_SYSTEM_PROMPT

    def test_palavra_cancelar_preservada(self):
        """'cancelar' estava apenas em CONFIRMACOES — deve ter sido mesclada em TRANSICOES."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert '"cancelar"' in WIZARD_SYSTEM_PROMPT

    def test_uma_unica_lista_de_confirmacoes(self):
        """Deve haver apenas uma ocorrência de 'Entenda confirmacoes'."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        count = WIZARD_SYSTEM_PROMPT.count("Entenda confirmacoes")
        assert count == 1, f"Esperado 1 ocorrência, encontrado {count}"

    def test_uma_unica_lista_de_negacoes(self):
        """Deve haver apenas uma ocorrência de 'Entenda negacoes'."""
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        count = WIZARD_SYSTEM_PROMPT.count("Entenda negacoes")
        assert count == 1, f"Esperado 1 ocorrência, encontrado {count}"


class TestPolicyNaoRegrediu:
    """Policy não deve ter sido alterada — todas as seções distintas permanecem."""

    def test_raciocinio_consultivo_presente(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "RACIOCINIO CONSULTIVO" in POLICY_SYSTEM_PROMPT

    def test_contra_argumentacao_presente(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "CONTRA-ARGUMENTACAO" in POLICY_SYSTEM_PROMPT

    def test_prevencao_sycophancy_presente(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in POLICY_SYSTEM_PROMPT

    def test_verificacao_premissas_presente(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "VERIFICACAO DE PREMISSAS" in POLICY_SYSTEM_PROMPT

    def test_confirmacoes_presente(self):
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "CONFIRMACOES" in POLICY_SYSTEM_PROMPT
