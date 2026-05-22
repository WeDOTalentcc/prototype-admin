"""
WT-2022 P0.C wave 2 — Contract test: WSI generation paths grava AutomatedDecisionExplanation.

Sensores complementares ao AST checker `scripts/check_wsi_calls_log_automated_decision.py`:
o AST sensor garante que o call EXISTE no codigo; este teste valida que ele
EXECUTA com sucesso e grava row real na tabela `automated_decision_explanations`
(LGPD Art. 20 + EU AI Act Art. 13).

Roda contra DB de teste isolado (fixture). Cada paths e parametrizado por:
    (endpoint_path, decision_type_esperado, payload_minimo)

Skip se ambiente nao tem DB de teste configurado (CI roda; local dev opcional).
"""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.asyncio


# Gate: this contract test requires an isolated TEST_DATABASE_URL plus
# `authenticated_client` and `db_session` fixtures (not yet wired in conftest).
#
# Bypassing on DATABASE_URL alone is unsafe: dev DATABASE_URL points to a
# shared DB; running this would pollute it. Until the integration fixture
# scaffold lands (tracked TODO below), skip explicitly so the gap is visible
# rather than disguised as a passing test.
#
# Companion sensor remains live: `scripts/check_wsi_calls_log_automated_decision.py`
# (AST check that the call SITE exists in code — file:line guard).
_TEST_DB_AVAILABLE = bool(os.getenv("TEST_DATABASE_URL"))

skip_if_no_db = pytest.mark.skipif(
    not _TEST_DB_AVAILABLE,
    reason=(
        "TEST_DATABASE_URL not set OR `authenticated_client`/`db_session` "
        "fixtures not yet wired (tracked: WT-2022 P0.C wave 2 follow-up). "
        "AST sensor `scripts/check_wsi_calls_log_automated_decision.py` still "
        "guards the call-site existence."
    ),
)


# Matrix de paths a validar. Cada entry: (endpoint, decision_type, payload-builder)
WSI_AUDIT_PATHS = [
    pytest.param(
        "/api/v1/screening/questions",
        "wsi_simple_inputs",
        lambda: {
            "title": "Engenheiro Backend",
            "department": "Tecnologia",
            "seniority": "pleno",
            "skills": ["Python", "FastAPI"],
            "behavioral_competencies": ["Comunicacao"],
            "job_description": "Vaga backend para audit test.",
            "question_count": 8,
        },
        id="screening_questions",
    ),
    pytest.param(
        "/api/v1/wsi/generate-questions",
        "wsi_legacy_questions",
        lambda: {
            "job_title": "Engenheiro Backend",
            "seniority": "pleno",
            "technical_skills": ["Python", "FastAPI"],
            "behavioral_competencies": ["Comunicacao"],
            "responsibilities": ["Desenvolver APIs"],
            "max_questions": 8,
        },
        id="wsi_legacy_questions",
    ),
    pytest.param(
        "/api/v1/wsi/screening-pipeline",
        "wsi_screening_pipeline_iteration",
        lambda: {
            "job_title": "Engenheiro Backend",
            "department": "Tecnologia",
            "seniority": "pleno",
            "technical_skills": ["Python", "FastAPI"],
            "behavioral_competencies": ["Comunicacao"],
            "responsibilities": ["Desenvolver APIs"],
            "job_description": "Vaga backend para audit test.",
            "question_count": 8,
            "format": "compact",
            "include_company_questions": False,
            "is_affirmative": False,
        },
        id="wsi_screening_pipeline",
    ),
]


@skip_if_no_db
@pytest.mark.parametrize("endpoint,decision_type,payload_builder", WSI_AUDIT_PATHS)
async def test_wsi_endpoint_creates_audit_log(
    endpoint: str,
    decision_type: str,
    payload_builder,
    authenticated_client,
    db_session,
):
    """Verifica que chamada ao endpoint WSI grava AutomatedDecisionExplanation row.

    Fixtures necessarias (a serem providas pelo conftest do projeto):
        - authenticated_client: AsyncClient com JWT valido (company_id no token)
        - db_session: AsyncSession apontando pro DB de teste
    """
    from sqlalchemy import select

    # Import lazy pra evitar coupling no test discovery
    try:
        from app.models.automated_decision_explanation import AutomatedDecisionExplanation
    except ImportError:
        pytest.skip("AutomatedDecisionExplanation model nao disponivel")

    # Snapshot do count ANTES (para evitar interferencia de outras chamadas)
    pre_count_stmt = select(AutomatedDecisionExplanation).where(
        AutomatedDecisionExplanation.decision_type == decision_type
    )
    pre_rows = (await db_session.execute(pre_count_stmt)).scalars().all()
    pre_count = len(pre_rows)

    payload = payload_builder()
    response = await authenticated_client.post(endpoint, json=payload)

    # Aceitar 200 OK ou 422 se schema mudou — focar no audit log, nao no contract da API
    assert response.status_code in (200, 201), (
        f"Endpoint {endpoint} retornou {response.status_code}: {response.text[:500]}"
    )

    # Refresh + count POS
    await db_session.commit()
    post_rows = (await db_session.execute(pre_count_stmt)).scalars().all()
    post_count = len(post_rows)

    assert post_count > pre_count, (
        f"Endpoint {endpoint} nao gravou AutomatedDecisionExplanation com "
        f"decision_type={decision_type!r}. Pre={pre_count}, Pos={post_count}. "
        f"Wire log_automated_decision (LGPD Art. 20 + EU AI Act Art. 13)."
    )

    # Validar shape do row mais recente
    latest = max(post_rows, key=lambda r: r.created_at)
    assert latest.decision_type == decision_type
    assert latest.ai_model_used, "ai_model_used vazio — quebra contract LGPD"
    assert latest.explanation_text, "explanation_text vazio — quebra Art. 20"
    assert latest.input_criteria, "input_criteria (criteria_used) vazio"
    # PROTECTED_CRITERIA_PT em decision_criteria.criteria_ignored
    decision_criteria = latest.decision_criteria or {}
    criteria_ignored = decision_criteria.get("criteria_ignored", [])
    assert criteria_ignored, "criteria_ignored vazio — ADR-LGPD-001 violation"


@skip_if_no_db
async def test_protected_criteria_violation_raises_value_error(db_session):
    """Sensor fail-loud: passar atributo protegido em criteria_used deve raise ValueError.

    Garante ADR-LGPD-001 enforcement permanece — CLAUDE.md REGRA #2 (LGPD).
    """
    from app.shared.services.automated_decision_logger import log_automated_decision

    test_company = str(uuid.uuid4())

    with pytest.raises(ValueError):
        await log_automated_decision(
            db=db_session,
            company_id=test_company,
            decision_type="wsi_test_protected_violation",
            ai_model_used="claude-test",
            explanation_text="Test que protected criteria viola guardrails.",
            criteria_used=["raca:branco"],  # PROTECTED — deve fail-loud
            criteria_ignored=[],
            confidence_score=0.5,
            review_eligible=True,
        )
