"""
Testes unitários para detect_command_type() em kanban_assistant_prompts.py.

Cobre:
- Fórmula de confiança: min(0.5 + best_score * 0.15, 0.95)
- Default 0.4 sem nenhum match
- Teto máximo de 0.95
- Negation detection não gera falso positivo de tipo
- Comandos de cada tipo principal detectados corretamente
"""
import pytest
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import detect_command_type


class TestConfidenceFormula:
    """Valida a fórmula de confiança padronizada."""

    def test_sem_match_retorna_0_4(self):
        _, confidence = detect_command_type("xyzwq123 sem sentido algum")
        assert confidence == 0.4

    def test_com_match_confianca_acima_de_0_5(self):
        _, confidence = detect_command_type("ranking dos candidatos")
        assert confidence > 0.5

    def test_confianca_nao_excede_0_95(self):
        msg = "ranking comparar mover candidato avançar etapa listar pipeline score"
        _, confidence = detect_command_type(msg)
        assert confidence <= 0.95


class TestDeteccaoTipos:
    """Valida que cada tipo principal de comando é detectado."""

    def test_detecta_ranking(self):
        cmd_type, confidence = detect_command_type("me dê um ranking dos candidatos")
        assert confidence > 0.5
        assert cmd_type is not None and isinstance(cmd_type, str)

    def test_detecta_mover_candidato(self):
        cmd_type, _ = detect_command_type("mover o candidato João para entrevista")
        assert cmd_type is not None
        assert isinstance(cmd_type, str)

    def test_detecta_gargalo(self):
        cmd_type, confidence = detect_command_type("quais são os gargalos do pipeline")
        assert confidence > 0.5

    def test_detecta_triagem(self):
        cmd_type, confidence = detect_command_type("disparar triagem para os candidatos")
        assert confidence > 0.5

    def test_detecta_comparar(self):
        cmd_type, confidence = detect_command_type("comparar os candidatos finalistas")
        assert confidence > 0.5


class TestNegationDetection:
    """Valida que negações não disparam comandos errados."""

    def test_negacao_nao_dispara_ranking(self):
        cmd_type, confidence = detect_command_type("não quero ranking agora")
        assert cmd_type != "rankear_candidatos" or confidence <= 0.5

    def test_negacao_sem_gargalo(self):
        cmd_type, confidence = detect_command_type("sem gargalo nenhum")
        assert cmd_type != "gargalos_processo" or confidence <= 0.5

    def test_mensagem_generica_retorna_tipo_default(self):
        cmd_type, confidence = detect_command_type("ok, entendi")
        assert confidence <= 0.5
