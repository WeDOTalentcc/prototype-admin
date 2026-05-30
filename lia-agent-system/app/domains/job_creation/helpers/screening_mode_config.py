"""SCREENING_MODE_CONFIG — single source of truth for screening mode constants.

Consumed by intake_gate_node (time estimates), competency_gate_node (confirmation),
CompetencyBenchmarkService (dimensiona nº de competências sugeridas), and any
future consumer (wsi_questions, competency_node).

Invariante canônica: technical_competencies + behavioral_competencies == total_questions
(WSI gera ~1 pergunta por competência confirmada). O sensor
tests/unit/test_competency_benchmark_service_fase2.py pina esse invariante.

Nota: a distribuição POR SENIORIDADE (compact senior=4tec/3comp etc.) vive em
app/prompts/job_creation/wsi_question_distribution.yaml e é aplicada no estágio
de competency/wsi_questions (Fase 6). O split aqui é o DEFAULT por modo, usado
para dimensionar a SUGESTÃO inicial de competências no intake (Fase 2/3).
"""
from __future__ import annotations
from typing import TypedDict


class ScreeningModeInfo(TypedDict):
    total_questions: int
    estimated_minutes: int
    technical_competencies: int
    behavioral_competencies: int


SCREENING_MODE_CONFIG: dict[str, ScreeningModeInfo] = {
    "compact": {
        "total_questions": 7,
        "estimated_minutes": 15,
        "technical_competencies": 5,
        "behavioral_competencies": 2,
    },
    "full": {
        "total_questions": 12,
        "estimated_minutes": 25,
        "technical_competencies": 8,
        "behavioral_competencies": 4,
    },
}
