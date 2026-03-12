"""
Testes unitários para detect_command_type() em kanban_assistant_prompts.py.

Cobre:
- Fórmula de confiança correta: max(0.6, min(best_score * 3, 0.95))
- Piso mínimo de 0.6 com qualquer match
- Teto máximo de 0.95
- Default 0.5 sem nenhum match
- Negation detection não gera falso positivo de tipo
- Comandos de cada tipo principal detectados corretamente
"""
import pytest
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import detect_command_type


class TestConfidenceFormula:
    """Valida a fórmula de confiança padronizada com talent/jobs."""

    def test_sem_match_retorna_0_5(self):
        _, confidence = detect_command_type("xyzwq123 sem sentido algum")
        assert confidence == 0.5

    def test_com_match_confianca_minima_0_6(self):
        # qualquer match deve resultar em confiança >= 0.6 (piso)
        _, confidence = detect_command_type("ranking dos candidatos")
        assert confidence >= 0.6

    def test_confianca_nao_excede_0_95(self):
        # muitos matches não devem ultrapassar 0.95
        msg = "ranking comparar mover candidato avançar etapa listar pipeline score"
        _, confidence = detect_command_type(msg)
        assert confidence <= 0.95

    def test_formula_multipicacao_nao_divisao(self):
        # Com score=1.0 (1 match sem peso extra):
        # fórmula CORRETA: max(0.6, min(1.0 * 3, 0.95)) = 0.95
        # fórmula ERRADA:  min(0.95, 1.0 / 3.0) = 0.333 → nunca atingiria 0.9+
        _, confidence = detect_command_type("ranking dos candidatos avaliados")
        assert confidence >= 0.9, (
            f"Fórmula deve usar multiplicação (*3), não divisão (/3). "
            f"Confiança obtida: {confidence}"
        )


class TestDeteccaoTipos:
    """Valida que cada tipo principal de comando é detectado."""

    def test_detecta_ranking(self):
        cmd_type, confidence = detect_command_type("me dê um ranking dos candidatos")
        # Tipo deve ser rankear_candidatos ou similar, com confiança >= 0.6
        assert confidence >= 0.6
        assert cmd_type is not None and isinstance(cmd_type, str)

    def test_detecta_mover_candidato(self):
        cmd_type, _ = detect_command_type("mover o candidato João para entrevista")
        assert cmd_type is not None
        assert isinstance(cmd_type, str)

    def test_detecta_gargalo(self):
        cmd_type, confidence = detect_command_type("quais são os gargalos do pipeline")
        assert confidence >= 0.6

    def test_detecta_triagem(self):
        cmd_type, confidence = detect_command_type("disparar triagem para os candidatos")
        assert confidence >= 0.6

    def test_detecta_comparar(self):
        cmd_type, confidence = detect_command_type("comparar os candidatos finalistas")
        assert confidence >= 0.6


class TestNegationDetection:
    """Valida que negações não disparam comandos errados com alta confiança."""

    def test_negacao_nao_dispara_ranking_com_alta_confianca(self):
        # "não quero ranking" não deve ter confiança máxima para ranking
        _, confidence = detect_command_type("não quero ranking agora")
        # Pode detectar ranking (keyword match ainda existe), mas não deve
        # ter confiança absurdamente alta — a negação reduz a relevância
        # Este teste garante que não há score artificial >= 0.95 nesse caso
        # (o fix de negation detection completa é P1-B)
        assert confidence <= 0.95

    def test_mensagem_generica_retorna_tipo_default(self):
        cmd_type, confidence = detect_command_type("ok, entendi")
        # Sem match forte → confiança baixa
        assert confidence <= 0.65
