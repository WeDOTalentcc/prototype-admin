"""
Onda 2D — prazos da vaga derivados do SLA do pipeline.

derive_deadlines_from_stages normaliza interview_stages (sla_hours|sla_days) e devolve
os 4 prazos (deadline_screening/shortlist/closing/deadline) = soma cumulativa dos SLAs.
Usado no PUT da vaga: ao salvar as etapas, os prazos recalculam (fonte = SLA, não manual).
"""
from datetime import datetime

from app.domains.cv_screening.services.deadline_calculator_service import (
    derive_deadlines_from_stages,
)


class TestDeriveDeadlinesFromStages:
    def test_returns_only_four_deadline_fields(self):
        d = derive_deadlines_from_stages([{"name": "x", "sla_days": 1}])
        assert set(d.keys()) == {"deadline_screening", "deadline_shortlist", "deadline_closing", "deadline"}
        assert d["deadline"] == d["deadline_closing"]

    def test_empty_stages_returns_defaults(self):
        d = derive_deadlines_from_stages([])
        assert d["deadline_closing"] is not None

    def test_sla_days_cumulative(self):
        stages = [
            {"name": "Triagem", "order": 0, "sla_days": 3},
            {"name": "Entrevista", "order": 1, "sla_days": 5},
        ]
        d = derive_deadlines_from_stages(stages)
        delta = (d["deadline_closing"] - datetime.utcnow()).days
        assert 7 <= delta <= 8  # 3+5 dias

    def test_sla_hours_converted_to_days(self):
        stages = [{"name": "Triagem", "order": 0, "sla_hours": 48}]  # 2 dias
        d = derive_deadlines_from_stages(stages)
        delta = (d["deadline_closing"] - datetime.utcnow()).days
        assert 1 <= delta <= 2

    def test_screening_deadline_from_triagem_stage(self):
        stages = [
            {"name": "Triagem CV", "order": 0, "sla_days": 2},
            {"name": "Final", "order": 1, "sla_days": 4},
        ]
        d = derive_deadlines_from_stages(stages)
        sdelta = (d["deadline_screening"] - datetime.utcnow()).days
        assert 1 <= sdelta <= 2

    def test_ignores_non_dict_entries(self):
        d = derive_deadlines_from_stages([{"name": "ok", "sla_days": 2}, "garbage", None])
        assert d["deadline_closing"] is not None
