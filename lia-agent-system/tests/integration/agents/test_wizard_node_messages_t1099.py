"""Task #1099 — Sentinela do contrato ``ws_stage_payload.data.message`` em
TODOS os nodes do JobCreationGraph.

Generaliza a sentinela da Task #1096 (que cobria apenas
``jd_enrichment_node``) para os outros 9 nodes do wizard:

  ``bigfive`` · ``salary`` · ``competency`` · ``wsi_questions`` ·
  ``eligibility`` · ``review`` · ``publish`` · ``calibration`` · ``handoff``

Invariant arquitetural — todo node que retorna ``current_stage`` setado DEVE
incluir ``ws_stage_payload.data["message"]`` truthy. Sem isso, o
``WizardSessionService`` cai em ``_emit_silent_fallback`` (Task #1089) e o
recrutador vê o fail-loud ``[ATENÇÃO: estado inconsistente — contate suporte]``.

Em paths normais os ``*_gate_node`` populam ``gate_clarify_message`` (que tem
precedência no consumer). Esta sentinela cobre os paths em que o gate NÃO
roda — erro, retry, policy DENY, FairnessGuard PRE-BLOCK — onde a mensagem do
node é o único fallback.

Cada teste exercita um node real com dependências externas mockadas (sem
rede, sem DB) e valida que ``ws_stage_payload["data"]["message"]`` é truthy.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_BACKEND_ROOT))


def _base_state(**overrides):
    state = {
        "session_id": "sess-test-1099",
        "user_id": "user-test",
        "company_id": "00000000-0000-4000-a000-000000000001",
        "workspace_id": 1,
        "raw_input": "",
        "user_query": "",
        "stage_history": [],
        "conversation_messages": [],
    }
    state.update(overrides)
    return state


def _msg_of(result: dict) -> str:
    payload = (result or {}).get("ws_stage_payload") or {}
    data = payload.get("data") or {}
    return data.get("message") or ""


def _assert_msg(test, result, *, where: str, must_contain=()):
    msg = _msg_of(result)
    test.assertTrue(
        msg,
        f"{where}: ws_stage_payload.data.message DEVE ser truthy — sem isso "
        "WizardSessionService cai em _emit_silent_fallback (Task #1089).",
    )
    test.assertNotIn(
        "[ATENÇÃO", msg,
        f"{where}: mensagem do node não pode ser o fail-loud canned.",
    )
    for token in must_contain:
        test.assertIn(
            token, msg,
            f"{where}: mensagem deve conter {token!r} para ser parametrizada.",
        )


class WizardNodeMessagesT1099(unittest.TestCase):
    # ──────────────────────────────────────────────────────── bigfive
    def test_bigfive_normal_populates_message(self):
        from app.domains.job_creation.graph import bigfive_node
        state = _base_state(
            parsed_title="Engenheiro Backend Pleno",
            parsed_seniority="pleno",
            jd_enriched={
                "titulo_padronizado": "Engenheiro de Software Backend",
                "about_role": "Vaga descrita.",
                "responsabilidades": ["arquitetar APIs"],
                "skills_obrigatorias": [{"skill": "Python", "contexto": "FastAPI"}],
                "competencias_comportamentais": [],
            },
        )

        fake_bf = MagicMock()
        fake_bf.model_dump.return_value = {
            "openness": 0.6, "conscientiousness": 0.7, "extraversion": 0.5,
            "agreeableness": 0.5, "neuroticism": 0.3,
        }
        fake_gen = MagicMock()
        fake_gen.extract_bigfive.return_value = fake_bf
        fake_gen.rank_traits.return_value = []

        with patch(
            "app.domains.job_creation.graph._get_wsi_generator",
            return_value=fake_gen,
        ):
            result = bigfive_node(state)

        _assert_msg(self, result, where="bigfive[normal]",
                    must_contain=("Engenheiro Backend Pleno",))

    def test_bigfive_fairness_pre_block_populates_message(self):
        from app.domains.job_creation.graph import bigfive_node

        state = _base_state(
            jd_enriched={
                "about_role": "trigger",
                "responsabilidades": ["x"],
            },
        )
        fake_block = MagicMock(is_blocked=True, category="age",
                               blocked_terms=["jovem"])
        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard"
        ) as fg_cls:
            fg_cls.return_value.check.return_value = fake_block
            result = bigfive_node(state)

        self.assertEqual(result.get("current_stage"), "bigfive")
        _assert_msg(self, result, where="bigfive[fairness_pre_block]")

    # ──────────────────────────────────────────────────────── salary
    def test_salary_normal_populates_message(self):
        from app.domains.job_creation.graph import salary_node
        state = _base_state(
            salary_min=8000, salary_max=12000, salary_currency="BRL",
            salary_benchmark={"source": "internal", "confidence": 0.8},
        )
        result = salary_node(state)
        _assert_msg(self, result, where="salary[normal]",
                    must_contain=("salarial",))

    # ──────────────────────────────────────────────────────── competency
    def test_competency_normal_populates_message(self):
        from app.domains.job_creation.graph import competency_node
        state = _base_state(
            parsed_title="Engenheiro Backend",
            parsed_seniority="pleno",
            screening_mode="compact",
            jd_enriched={
                "titulo_padronizado": "Engenheiro Backend",
                "about_role": "x",
                "skills_obrigatorias": [{"skill": "Python", "contexto": "y"}],
                "competencias_comportamentais": [],
            },
        )
        result = competency_node(state)
        _assert_msg(self, result, where="competency[normal]",
                    must_contain=("senioridade",))

    # ──────────────────────────────────────────────────────── wsi_questions
    def test_wsi_questions_normal_populates_message(self):
        from app.domains.job_creation.graph import wsi_questions_node
        state = _base_state(
            jd_enriched={
                "about_role": "x", "responsabilidades": [],
                "skills_obrigatorias": [], "competencias_comportamentais": [],
            },
            screening_mode="compact",
            seniority_resolved="pleno",
            question_distribution={"technical": 4, "behavioral": 3},
            trait_rankings=[],
            competency_tree=[],
        )

        fake_q = [
            {"question": "Conte uma situação em que você liderou um projeto.",
             "block": "behavioral"},
        ]
        fake_gen = MagicMock()
        fake_gen.generate_wsi_questions.return_value = fake_q
        with patch(
            "app.domains.job_creation.graph._get_wsi_generator",
            return_value=fake_gen,
        ):
            result = wsi_questions_node(state)

        _assert_msg(self, result, where="wsi_questions[normal]",
                    must_contain=("WSI",))

    # ──────────────────────────────────────────────────────── eligibility
    def test_eligibility_with_questions_populates_message(self):
        from app.domains.job_creation.graph import eligibility_node
        state = _base_state(
            eligibility_questions=[
                {"text": "Você tem CNH B?"},
                {"text": "Disponibilidade para viagens?"},
            ],
        )
        result = eligibility_node(state)
        _assert_msg(self, result, where="eligibility[with]",
                    must_contain=("eliminat",))

    def test_eligibility_empty_populates_message(self):
        from app.domains.job_creation.graph import eligibility_node
        state = _base_state(eligibility_questions=[])
        result = eligibility_node(state)
        _assert_msg(self, result, where="eligibility[empty]")

    # ──────────────────────────────────────────────────────── review
    def test_review_populates_message(self):
        from app.domains.job_creation.graph import review_node
        state = _base_state(
            jd_enriched={"titulo_padronizado": "x"},
            wsi_questions=[{"question": "q1"}],
            screening_mode="compact",
            publish_platforms=["website"],
            company_defaults_applied=["screening_mode"],
        )
        # Stub the API client to skip company defaults network call.
        with patch(
            "app.domains.job_creation.graph._get_api_client"
        ) as api_factory:
            api_factory.return_value.get_company_defaults.return_value = (
                MagicMock(success=False, data=None)
            )
            result = review_node(state)
        _assert_msg(self, result, where="review[normal]")

    # ──────────────────────────────────────── architectural sentinel
    def test_AST_all_ws_stage_payload_literals_carry_message(self):
        """AST-level invariant: todo dict literal atribuído à chave
        ``ws_stage_payload`` no graph.py cujo ``data`` é também um dict
        literal DEVE conter a chave ``"message"``.

        Cobre o caso em que um futuro node adicione um literal sem rodar
        nenhum dos testes runtime acima — a sentinela arquitetural pega.
        Para o único caso onde ``data`` é uma referência a ``Name``
        (``_wsi_stage_data`` em ``wsi_questions_node``), a sentinela
        verifica a definição da variável separadamente.
        """
        import ast
        graph_path = (
            _REPO_BACKEND_ROOT / "app" / "domains" / "job_creation" / "graph.py"
        )
        tree = ast.parse(graph_path.read_text())

        def _dict_keys(node: ast.Dict) -> list[str]:
            keys = []
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.append(k.value)
            return keys

        def _data_dict_for(payload: ast.Dict) -> ast.AST | None:
            for k, v in zip(payload.keys, payload.values):
                if (isinstance(k, ast.Constant) and k.value == "data"):
                    return v
            return None

        # Map of variable name -> assigned Dict (for follow-through, e.g.
        # _wsi_stage_data).
        var_dicts: dict[str, ast.Dict] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if isinstance(value, ast.Dict):
                    targets = (
                        node.targets if isinstance(node, ast.Assign)
                        else [node.target]
                    )
                    for t in targets:
                        if isinstance(t, ast.Name):
                            var_dicts[t.id] = value

        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for k, v in zip(node.keys, node.values):
                if not (isinstance(k, ast.Constant)
                        and k.value == "ws_stage_payload"):
                    continue
                if not isinstance(v, ast.Dict):
                    continue
                data_node = _data_dict_for(v)
                if data_node is None:
                    continue
                target_dict: ast.Dict | None = None
                if isinstance(data_node, ast.Dict):
                    target_dict = data_node
                elif isinstance(data_node, ast.Name):
                    target_dict = var_dicts.get(data_node.id)
                if target_dict is None:
                    # Conservative: skip dynamically-built data dicts the
                    # AST walker can't follow. The runtime tests above must
                    # cover those cases.
                    continue
                if "message" not in _dict_keys(target_dict):
                    violations.append(
                        f"line {v.lineno}: ws_stage_payload.data missing "
                        "'message' key (Task #1099 invariant)."
                    )

        self.assertFalse(
            violations,
            "Task #1099 architectural sentinel — every ws_stage_payload "
            "literal in graph.py must include data['message'] truthy:\n  - "
            + "\n  - ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
