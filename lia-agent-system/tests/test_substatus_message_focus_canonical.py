"""
Sensor — SUBSTATUS_MESSAGE_FOCUS e SubStatusPredictor falam o vocabulário canônico
Camada 2 (Unitário BE — pytest, sem DB)

Contexto (auditoria 2026-06-10): o modal "Mover para: Reprovado" envia o
`sub_status` (motivo) usando o vocabulário canônico CANONICAL_SUB_STATUSES["rejected"]
(que espelha o front em plataforma-lia). Mas o MessageGenerator.SUBSTATUS_MESSAGE_FOCUS
e o SubStatusPredictor usavam um vocabulário próprio divergente
(ex: 'overqualified' vs canônico 'over_qualified', 'cultural_fit' vs 'cultural_mismatch',
'insufficient_technical_skills' vs 'lacking_technical_skills').

Efeito do drift:
- O foco curado do feedback (SUBSTATUS_MESSAGE_FOCUS.get(...)) caía no default genérico
  para quase todos os motivos -> personalização degradada silenciosamente.
- O substatus INFERIDO pelo predictor era persistido em vacancy_candidate.status com
  código não-canônico -> FE exibia sem tradução/cor.

Este sensor pina:
1. Toda chave de SUBSTATUS_MESSAGE_FOCUS é um código canônico de 'rejected'.
2. Todo código canônico de 'rejected' tem foco curado (cobertura completa).
3. Toda saída possível de SubStatusPredictor._predict_rejection é canônica.
4. normalize_rejection_substatus mapeia aliases legados -> canônico.
"""

from app.models.recruitment_stages import CANONICAL_SUB_STATUSES
from app.domains.automation.services.stage_transition_automation import (
    MessageGenerator,
    SubStatusPredictor,
    normalize_rejection_substatus,
)

CANONICAL_REJECTED = {item["name"] for item in CANONICAL_SUB_STATUSES["rejected"]}


class TestSubStatusMessageFocusCanonical:

    def test_all_focus_keys_are_canonical(self):
        """Toda chave em SUBSTATUS_MESSAGE_FOCUS deve existir em CANONICAL_SUB_STATUSES['rejected'].

        Fix: renomeie a chave para o código canônico (ex: 'overqualified' -> 'over_qualified',
        'cultural_fit' -> 'cultural_mismatch') em
        app/domains/automation/services/stage_transition_automation.py.
        """
        orphans = set(MessageGenerator.SUBSTATUS_MESSAGE_FOCUS) - CANONICAL_REJECTED
        assert not orphans, (
            f"Chaves não-canônicas em SUBSTATUS_MESSAGE_FOCUS: {sorted(orphans)}. "
            f"Use os códigos de CANONICAL_SUB_STATUSES['rejected']."
        )

    def test_every_canonical_rejected_code_has_focus(self):
        """Todo motivo canônico de reprovação deve ter foco curado de mensagem.

        Fix: adicione uma entrada para o código faltante em SUBSTATUS_MESSAGE_FOCUS
        descrevendo o foco do feedback (fairness-aware: business-decision != culpa do candidato).
        """
        missing = CANONICAL_REJECTED - set(MessageGenerator.SUBSTATUS_MESSAGE_FOCUS)
        assert not missing, (
            f"Motivos canônicos sem foco curado: {sorted(missing)}. "
            f"Adicione cada um em SUBSTATUS_MESSAGE_FOCUS."
        )


class TestSubStatusPredictorCanonical:

    def _contexts(self):
        # (context, from_stage) cobrindo todas as ramificações de _predict_rejection
        return [
            ({"job": {"has_hired_candidate": True}}, ""),
            ({"wsi_score": {"technical": 25}, "job": {}}, ""),
            ({"wsi_score": {"technical": 60, "cultural": 40}, "job": {}}, ""),
            ({"wsi_score": {"technical": 60, "cultural": 60, "overall": 30}, "job": {}}, ""),
            ({"wsi_score": {}, "job": {}}, "interview_manager"),
            (
                {
                    "wsi_score": {"technical": 60, "cultural": 60, "overall": 60},
                    "job": {},
                    "interview_notes": [
                        {"stage": "interview_technical", "gaps": ["a", "b", "c"]}
                    ],
                },
                "interview_technical",
            ),
            ({"wsi_score": {"technical": 60, "cultural": 60, "overall": 75}, "job": {}}, ""),
            ({"wsi_score": {}, "job": {}}, "screening"),
        ]

    def test_all_rejection_predictions_are_canonical(self):
        """Toda predição de substatus de reprovação deve ser um código canônico.

        Fix: em SubStatusPredictor._predict_rejection, retorne códigos de
        CANONICAL_SUB_STATUSES['rejected'] (ex: 'lacking_technical_skills', não
        'insufficient_technical_skills').
        """
        for ctx, from_stage in self._contexts():
            result = SubStatusPredictor.predict(ctx, from_stage=from_stage, to_stage="rejected")
            code = result["predicted_substatus"]
            assert code in CANONICAL_REJECTED, (
                f"Predição não-canônica '{code}' para from_stage='{from_stage}'. "
                f"Use um código de CANONICAL_SUB_STATUSES['rejected']."
            )


class TestNormalizeRejectionSubstatus:

    def test_legacy_aliases_map_to_canonical(self):
        legacy = {
            "overqualified": "over_qualified",
            "underqualified": "under_qualified",
            "insufficient_technical_skills": "lacking_technical_skills",
            "cultural_fit": "cultural_mismatch",
            "salary_expectation": "salary_above_budget",
            "candidate_withdrew": "withdrew",
        }
        for alias, expected in legacy.items():
            normalized = normalize_rejection_substatus(alias)
            assert normalized == expected, f"{alias} deveria normalizar para {expected}, veio {normalized}"
            assert normalized in CANONICAL_REJECTED

    def test_canonical_code_passes_through(self):
        assert normalize_rejection_substatus("over_qualified") == "over_qualified"

    def test_empty_is_safe(self):
        assert normalize_rejection_substatus("") == ""
        assert normalize_rejection_substatus(None) is None


class TestPredictNonRejectionCanonical:
    """Predições de sub-status para transições NÃO-rejeição também devem ser canônicas."""

    NON_REJECTION_STAGES = [
        "screening", "long_list", "short_list", "interview_hr", "interview_technical",
        "interview_manager", "interview_manager2", "interview_final", "references",
        "offer", "hired", "offer_declined", "standby",
    ]

    def test_non_rejection_predictions_are_canonical(self):
        """Fix: em SubStatusPredictor._predict_non_rejection, o default de cada etapa
        deve ser um código de CANONICAL_SUB_STATUSES[<etapa>]
        (ex: standby -> 'future_talent', não 'temporary_hold').
        """
        for stage in self.NON_REJECTION_STAGES:
            res = SubStatusPredictor.predict({}, from_stage="", to_stage=stage)
            code = res["predicted_substatus"]
            canonical = {i["name"] for i in CANONICAL_SUB_STATUSES.get(stage, [])}
            assert code in canonical, (
                f"Predição não-canônica '{code}' para to_stage='{stage}'. "
                f"Use um código de CANONICAL_SUB_STATUSES['{stage}']."
            )
