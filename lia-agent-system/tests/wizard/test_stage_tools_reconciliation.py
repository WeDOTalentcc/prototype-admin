"""Sensor PR-16: STAGE_TOOLS keys são snake_case canonical (creation + lifecycle).

Background: PR-1 (commit 4e904792) descobriu drift kebab vs snake. PR-8
(d16f6316) documentou design layered como ADR. PR-16 (2026-05-26)
reconciliou kebab -> snake nos 7 creation stages para alinhar com
WizardStage Literal canonical em app/domains/job_creation/state.py.

Mapping aplicado:
    input-evaluation  -> intake
    jd-enrichment     -> jd_enrichment
    pipeline-template -> pipeline_template
    salary            -> salary (no change)
    competencies      -> competency (singular)
    wsi-questions     -> wsi_questions
    review-publish    -> review + publish (split em 2 entries)

Lifecycle Phase E mantido snake (DB column values, NÃO toca):
    enriquecida, wsi_config, aguardando_aprovacao, publicada, ao_vivo

PR-1 confirmou zero callers de get_stage_tools em produção, então
a reconciliação é canonical-safe (STAGE_TOOLS hoje é docs + sensor,
não gating real). Frontend continua dispatching kebab via
/api/v1/wizard/smart-orchestrate -- tradução kebab->snake fica em
FRONTEND_TO_BACKEND_STAGE (app/api/v1/wizard_smart_orchestrator.py).
"""

from typing import get_args

import pytest

from app.domains.job_creation.state import WizardStage
from app.domains.job_management.agents.wizard_tool_registry import STAGE_TOOLS


PHASE_E_LIFECYCLE_KEYS = {
    "enriquecida",
    "wsi_config",
    "aguardando_aprovacao",
    "publicada",
    "ao_vivo",
}


def test_no_kebab_keys_in_stage_tools():
    """STAGE_TOOLS não deve ter nenhuma key com hyphen (PR-16 regression)."""
    kebab_keys = [k for k in STAGE_TOOLS.keys() if "-" in k]
    assert not kebab_keys, (
        f"PR-16 regression: keys kebab encontradas: {kebab_keys}. "
        "Convenção canonical pós-PR-16 é snake_case."
    )


def test_creation_stages_match_wizardstage_literal():
    """Creation stages em STAGE_TOOLS devem estar em WizardStage Literal."""
    literal_stages = set(get_args(WizardStage))
    creation_keys_in_stage_tools = {
        k for k in STAGE_TOOLS.keys() if k not in PHASE_E_LIFECYCLE_KEYS
    }

    diff = creation_keys_in_stage_tools - literal_stages
    assert not diff, (
        f"STAGE_TOOLS creation keys não em WizardStage Literal: {sorted(diff)}.\n"
        f"  WizardStage Literal: {sorted(literal_stages)}\n"
        f"  STAGE_TOOLS creation: {sorted(creation_keys_in_stage_tools)}\n"
        "  Fix: ou (a) renomear key em STAGE_TOOLS para match Literal, ou "
        "(b) adicionar valor ao Literal em app/domains/job_creation/state.py."
    )


def test_pr16_mapping_keys_present():
    """Sanity: as 8 creation keys canonical pós-PR-16 estão presentes."""
    expected_creation = {
        "intake",
        "jd_enrichment",
        "pipeline_template",
        "salary",
        "competency",
        "wsi_questions",
        "review",
        "publish",
    }
    missing = expected_creation - set(STAGE_TOOLS.keys())
    assert not missing, (
        f"PR-16 canonical creation keys ausentes: {sorted(missing)}"
    )


def test_pr16_lifecycle_keys_unchanged():
    """Phase E lifecycle keys (DB column values) permanecem snake."""
    missing = PHASE_E_LIFECYCLE_KEYS - set(STAGE_TOOLS.keys())
    assert not missing, (
        f"Phase E lifecycle keys ausentes (não deveriam mudar em PR-16): "
        f"{sorted(missing)}"
    )


def test_review_and_publish_have_same_tools():
    """PR-16: review e publish (split de review-publish) têm o mesmo tool set."""
    review = set(STAGE_TOOLS.get("review", []))
    publish = set(STAGE_TOOLS.get("publish", []))
    assert review == publish, (
        f"review e publish stages devem ter o mesmo tool set (split de "
        f"'review-publish' pré-PR-16).\n"
        f"  Em review apenas: {sorted(review - publish)}\n"
        f"  Em publish apenas: {sorted(publish - review)}"
    )
