"""TDD (Task #1211) — canonical PT-BR confirmation classifier.

Run: pytest tests/unit/orchestrator/routing/test_confirmation_classifier.py -v
"""
import pytest


class TestPositives:
    @pytest.mark.parametrize(
        "msg",
        [
            "sim", "sim, pode publicar", "claro", "pode", "pode ir",
            "vamos", "bora", "manda ver", "fechou", "perfeito",
            "ok", "beleza", "quero sim", "com certeza", "pode sincronizar",
            "isso, faz aí", "aprovo", "confirmo", "segue", "avançar",
        ],
    )
    def test_yes(self, msg):
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        assert classify_confirmation(msg) == "yes"


class TestNegatives:
    @pytest.mark.parametrize(
        "msg",
        [
            "não", "nao", "agora não", "depois", "mais tarde",
            "deixa pra lá", "cancela", "melhor não", "prefiro não",
            "sem publicar", "não precisa", "pode esperar",  # negative wins over "pode"
            "pode deixar pra depois", "por enquanto não", "esquece",
        ],
    )
    def test_no(self, msg):
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        assert classify_confirmation(msg) == "no"


class TestAmbiguous:
    @pytest.mark.parametrize(
        "msg",
        ["", "talvez", "o que você acha?", "qual a diferença?", "hmm", "e o salário?"],
    )
    def test_ambiguous(self, msg):
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        assert classify_confirmation(msg) == "ambiguous"

    def test_negative_precedence_over_positive_token(self):
        from app.orchestrator.routing.confirmation_classifier import (
            classify_confirmation,
        )
        # "pode esperar" contains "pode" (positive) but must resolve to no.
        assert classify_confirmation("pode esperar") == "no"
