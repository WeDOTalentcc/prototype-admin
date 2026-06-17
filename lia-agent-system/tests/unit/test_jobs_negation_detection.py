"""
P1-B — Testes de negation detection no JOBS_MANAGEMENT_SYSTEM_PROMPT.

Cobre:
1. Prompt tem bloco "Entenda negacoes"
2. Palavras-chave de negação presentes ("nao", "espera", "cancelar", etc.)
3. Prompt tem bloco "Entenda confirmacoes" (existia antes — não regrediu)
4. Paridade com talent e kanban: todos os três têm negation detection
5. Bloco negação está na seção correta (TRANSICOES)
"""
import pytest


class TestNegationDetectionJobsManagement:

    def test_prompt_tem_entenda_negacoes(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert "Entenda negacoes" in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_negacoes_contem_nao(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert '"nao"' in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_negacoes_contem_cancelar(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert '"cancelar"' in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_negacoes_contem_espera(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert '"espera"' in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_confirmacoes_nao_regrediu(self):
        """Bloco de confirmações existia antes — não deve ter sido removido."""
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert "Entenda confirmacoes" in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_negacoes_na_secao_transicoes(self):
        """Negation detection deve estar dentro da seção TRANSICOES."""
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        idx_transicoes = JOBS_MANAGEMENT_SYSTEM_PROMPT.find("=== TRANSICOES ===")
        idx_negacoes = JOBS_MANAGEMENT_SYSTEM_PROMPT.find("Entenda negacoes")
        idx_next_section = JOBS_MANAGEMENT_SYSTEM_PROMPT.find("===", idx_transicoes + len("=== TRANSICOES ==="))
        assert idx_transicoes < idx_negacoes < idx_next_section


class TestParidadeNegationDetection:
    """Todos os prompts com keyword detection devem ter negation block."""

    def test_talent_tem_negation(self):
        from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import TALENT_SYSTEM_PROMPT
        assert "Entenda negacoes" in TALENT_SYSTEM_PROMPT

    def test_kanban_tem_negation(self):
        from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import LIA_SYSTEM_PROMPT
        assert "Entenda negacoes" in LIA_SYSTEM_PROMPT

    def test_jobs_tem_negation(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert "Entenda negacoes" in JOBS_MANAGEMENT_SYSTEM_PROMPT
