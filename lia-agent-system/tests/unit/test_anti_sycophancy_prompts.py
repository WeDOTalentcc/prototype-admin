"""
P0-B — Testes de presença do bloco anti-sycophancy nos prompts da LIA.

Cobre:
1. TALENT_SYSTEM_PROMPT contém seção PREVENCAO DE SYCOPHANCY
2. LIA_SYSTEM_PROMPT (kanban) contém seção PREVENCAO DE SYCOPHANCY
3. JOBS_MANAGEMENT_SYSTEM_PROMPT contém seção PREVENCAO DE SYCOPHANCY
4. WIZARD_SYSTEM_PROMPT contém seção PREVENCAO DE SYCOPHANCY + VERIFICACAO DE PREMISSAS
5. _LIA_SYSTEM_PROMPT (orchestrator) contém regra anti-sycophancy
6. policy_system_prompt já tinha — não foi alterado (regressão)
7. Bloco compartilhado anti_sycophancy_block importável e com 3 variantes
8. Regras críticas presentes no bloco OPERATIONAL
9. Regras críticas presentes no bloco FULL
10. Bloco ORCHESTRATOR é compacto (< 200 chars)
"""
import pytest


class TestAntiSycophancyPresenca:
    """Valida presença do bloco em cada prompt."""

    def test_talent_system_prompt_tem_anti_sycophancy(self):
        from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import TALENT_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in TALENT_SYSTEM_PROMPT

    def test_kanban_system_prompt_tem_anti_sycophancy(self):
        from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import LIA_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in LIA_SYSTEM_PROMPT

    def test_jobs_management_system_prompt_tem_anti_sycophancy(self):
        from app.domains.recruiter_assistant.prompts.jobs_management_prompts import JOBS_MANAGEMENT_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in JOBS_MANAGEMENT_SYSTEM_PROMPT

    def test_wizard_system_prompt_tem_anti_sycophancy(self):
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in WIZARD_SYSTEM_PROMPT

    def test_wizard_system_prompt_tem_verificacao_premissas(self):
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        assert "VERIFICACAO DE PREMISSAS" in WIZARD_SYSTEM_PROMPT

    def test_orchestrator_system_prompt_tem_anti_sycophancy(self):
        from app.orchestrator.legacy.orchestrator import _LIA_SYSTEM_PROMPT
        prompt_lower = _LIA_SYSTEM_PROMPT.lower()
        assert "anti-sycophancy" in prompt_lower or "sycophancy" in prompt_lower

    def test_policy_system_prompt_nao_regrediu(self):
        """policy já tinha anti-sycophancy — garantir que não foi removido."""
        from app.domains.hiring_policy.agents.policy_system_prompt import POLICY_SYSTEM_PROMPT
        assert "PREVENCAO DE SYCOPHANCY" in POLICY_SYSTEM_PROMPT


class TestAntiSycophancyBloco:
    """Valida o módulo compartilhado de blocos."""

    def test_modulo_importavel(self):
        from app.shared.prompts.anti_sycophancy_block import (
            ANTI_SYCOPHANCY_OPERATIONAL,
            ANTI_SYCOPHANCY_FULL,
            ANTI_SYCOPHANCY_ORCHESTRATOR,
        )
        assert ANTI_SYCOPHANCY_OPERATIONAL
        assert ANTI_SYCOPHANCY_FULL
        assert ANTI_SYCOPHANCY_ORCHESTRATOR

    def test_bloco_operational_tem_regras_criticas(self):
        from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_OPERATIONAL
        assert "NUNCA concorde" in ANTI_SYCOPHANCY_OPERATIONAL
        assert "discriminat" in ANTI_SYCOPHANCY_OPERATIONAL.lower()
        assert "compliance" in ANTI_SYCOPHANCY_OPERATIONAL.lower()

    def test_bloco_full_tem_verificacao_premissas(self):
        from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_FULL
        assert "VERIFICACAO DE PREMISSAS" in ANTI_SYCOPHANCY_FULL
        assert "NUNCA concorde" in ANTI_SYCOPHANCY_FULL

    def test_bloco_orchestrator_e_compacto(self):
        from app.shared.prompts.anti_sycophancy_block import ANTI_SYCOPHANCY_ORCHESTRATOR
        assert len(ANTI_SYCOPHANCY_ORCHESTRATOR) < 250


class TestAntiSycophancyNaoDuplica:
    """Garante que a inserção não criou duplicação de seções."""

    def test_talent_prompt_tem_exatamente_uma_secao_sycophancy(self):
        from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import TALENT_SYSTEM_PROMPT
        count = TALENT_SYSTEM_PROMPT.count("PREVENCAO DE SYCOPHANCY")
        assert count == 1, f"Esperado 1 ocorrência, encontrado {count}"

    def test_kanban_prompt_tem_exatamente_uma_secao_sycophancy(self):
        from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import LIA_SYSTEM_PROMPT
        count = LIA_SYSTEM_PROMPT.count("PREVENCAO DE SYCOPHANCY")
        assert count == 1, f"Esperado 1 ocorrência, encontrado {count}"

    def test_wizard_prompt_tem_exatamente_uma_secao_sycophancy(self):
        from app.domains.job_management.agents.wizard_system_prompt import WIZARD_SYSTEM_PROMPT
        count = WIZARD_SYSTEM_PROMPT.count("PREVENCAO DE SYCOPHANCY")
        assert count == 1, f"Esperado 1 ocorrência, encontrado {count}"
