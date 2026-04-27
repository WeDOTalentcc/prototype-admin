"""PR-I — keyword routing conflict regression tests.

harness-engineering: guide computacional — capabilities.yaml preciso elimina
P(conflito) no routing sem precisar de LLM inference.

TDD red-green: testes falham antes das correções, passam depois.
"""
import os
import yaml
import pytest

DOMAINS_DIR = os.path.join(os.path.dirname(__file__), "../../app/domains")


def load_keywords(domain: str) -> dict[str, str]:
    path = os.path.join(DOMAINS_DIR, domain, "config", "capabilities.yaml")
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("intent_keywords", {})


class TestTriagemOwnership:
    """cv_screening é o dono canônico de 'triagem' e 'screening'."""

    def test_triagem_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "triagem" not in kws, (
            "hiring_policy NÃO deve ter keyword 'triagem' — "
            "conflito direto com cv_screening.auto_screen (mesmo comprimento → TIE)"
        )

    def test_screening_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "screening" not in kws, (
            "hiring_policy NÃO deve ter keyword 'screening' — conflito com cv_screening"
        )

    def test_hiring_policy_configure_screening_uses_compound_keywords(self):
        """hiring_policy mantém configure_screening via keywords compostos (>= 2 palavras)."""
        kws = load_keywords("hiring_policy")
        screening_kws = {k for k, v in kws.items() if v == "configure_screening"}
        assert len(screening_kws) >= 1, "hiring_policy deve ter ao menos 1 keyword para configure_screening"
        for kw in screening_kws:
            assert len(kw.split()) >= 2, (
                f"'{kw}' para configure_screening deve ser composto — keyword simples conflita com cv_screening"
            )


class TestAutomacaoOwnership:
    """automation domain é o dono canônico de 'automação'."""

    def test_automacao_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "automação" not in kws, (
            "hiring_policy NÃO deve ter 'automação' simples — automation domain é o dono"
        )

    def test_automacao_sem_acento_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "automacao" not in kws, (
            "hiring_policy NÃO deve ter 'automacao' — automation domain é o dono"
        )

    def test_automation_english_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "automation" not in kws, (
            "hiring_policy NÃO deve ter 'automation' (EN) — automation domain é o dono"
        )

    def test_hiring_policy_configure_automation_uses_compound_keywords(self):
        """Apenas os conflitantes (automação/automacao/automation) foram removidos.
        Keywords não-conflitantes como 'autonomia' podem permanecer simples.
        """
        kws = load_keywords("hiring_policy")
        auto_kws = {k for k, v in kws.items() if v == "configure_automation"}
        assert len(auto_kws) >= 1, "hiring_policy deve ter ao menos 1 keyword para configure_automation"
        # Os 3 conflitantes específicos devem estar ausentes
        for conflicting in ("automação", "automacao", "automation"):
            assert conflicting not in auto_kws, (
                f"'{conflicting}' conflita com automation domain — deve ter sido removido"
            )


class TestEmailOwnership:
    """communication domain é o dono de 'email' e 'whatsapp' simples."""

    def test_email_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "email" not in kws, (
            "hiring_policy NÃO deve ter 'email' simples — communication domain é o dono"
        )

    def test_whatsapp_not_in_hiring_policy(self):
        kws = load_keywords("hiring_policy")
        assert "whatsapp" not in kws, (
            "hiring_policy NÃO deve ter 'whatsapp' simples — communication domain é o dono"
        )

    def test_hiring_policy_configure_communication_uses_compound_keywords(self):
        """Apenas os conflitantes (email, whatsapp) foram removidos.
        Keywords não-conflitantes como 'comunicação', 'comunicacao' podem permanecer.
        """
        kws = load_keywords("hiring_policy")
        comm_kws = {k for k, v in kws.items() if v == "configure_communication"}
        assert len(comm_kws) >= 1, "hiring_policy deve ter ao menos 1 keyword para configure_communication"
        # Os 2 conflitantes específicos devem estar ausentes
        for conflicting in ("email", "whatsapp"):
            assert conflicting not in comm_kws, (
                f"'{conflicting}' conflita com communication domain — deve ter sido removido"
            )


class TestSuggestActionOwnership:
    """recruiter_assistant é o dono canônico de 'sugerir ação' / 'próxima ação'."""

    def test_sugerir_acao_not_in_pipeline(self):
        kws = load_keywords("pipeline")
        assert "sugerir ação" not in kws, (
            "pipeline NÃO deve ter 'sugerir ação' — conflito exato com recruiter_assistant.suggest_action"
        )

    def test_proxima_acao_not_in_pipeline(self):
        kws = load_keywords("pipeline")
        assert "próxima ação" not in kws, (
            "pipeline NÃO deve ter 'próxima ação' — conflito exato com recruiter_assistant.suggest_action"
        )

    def test_pipeline_suggest_uses_pipeline_specific_keywords(self):
        """pipeline mantém suggest_next_action via keywords específicos de pipeline."""
        kws = load_keywords("pipeline")
        suggest_kws = {k for k, v in kws.items() if v == "suggest_next_action"}
        assert len(suggest_kws) >= 1, (
            "pipeline deve ter ao menos 1 keyword pipeline-específico para suggest_next_action"
        )


class TestIniciarTriagemOwnership:
    """'iniciar triagem' genérico não deve estar em interview_scheduling."""

    def test_iniciar_triagem_not_in_interview_scheduling(self):
        kws = load_keywords("interview_scheduling")
        assert "iniciar triagem" not in kws, (
            "interview_scheduling NÃO deve ter 'iniciar triagem' genérico — "
            "cv_screening é o dono; use 'iniciar triagem wsi' para ser específico"
        )
